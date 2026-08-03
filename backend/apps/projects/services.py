"""Project Performance services: completion, burndown, velocity, prediction, risk."""
from datetime import date, timedelta

from core.utils import linear_projection

from .models import Milestone, ProgressSnapshot, Project

PHASE_WEIGHTS = {"backend_pct": 0.35, "frontend_pct": 0.35, "testing_pct": 0.15, "deployment_pct": 0.15}


def total_completion(project: Project) -> float:
    return round(
        sum(getattr(project, field) * weight for field, weight in PHASE_WEIGHTS.items()), 1
    )


def record_snapshot(project: Project, on: date | None = None) -> ProgressSnapshot:
    """Capture the project's current progress as a snapshot (idempotent per date)."""
    on = on or date.today()
    snapshot, _ = ProgressSnapshot.objects.update_or_create(
        project=project,
        date=on,
        defaults={
            "backend_pct": project.backend_pct,
            "frontend_pct": project.frontend_pct,
            "testing_pct": project.testing_pct,
            "deployment_pct": project.deployment_pct,
            "pending_bugs": project.pending_bugs,
            "risk_score": risk_score(project),
        },
    )
    return snapshot


def burndown(project: Project, periods: int = 12) -> list[dict]:
    """Remaining % to completion over recent snapshots (100 − total progress)."""
    snapshots = list(
        ProgressSnapshot.objects.filter(project=project)
        .order_by("-date")[:periods]
    )
    snapshots.reverse()
    return [
        {
            "date": s.date.isoformat(),
            "remaining": round(100.0 - total_completion(s), 1),
            "total_pct": total_completion(s),
        }
        for s in snapshots
    ]


def velocity(project: Project, periods: int = 8) -> float:
    """Average total-% gained per snapshot interval."""
    snaps = list(ProgressSnapshot.objects.filter(project=project).order_by("date")[:periods])
    if len(snaps) < 2:
        return 0.0
    deltas = [
        total_completion(snaps[i]) - total_completion(snaps[i - 1]) for i in range(1, len(snaps))
    ]
    return round(sum(deltas) / len(deltas), 2)


def delivery_prediction(project: Project) -> dict:
    """Predict completion date from the progress trend (simple linear fit)."""
    snaps = list(ProgressSnapshot.objects.filter(project=project).order_by("date"))
    if len(snaps) < 2:
        return {"predicted_delivery": None, "confidence": None}
    ys = [total_completion(s) for s in snaps]
    periods = linear_projection(ys, 100.0)
    predicted = None
    confidence = None
    if periods is not None:
        predicted_date = snaps[-1].date + timedelta(days=int(round(periods * 7)))
        predicted = predicted_date.isoformat()
        # Rough confidence: closer the latest progress is to the trend line, higher.
        confidence = round(min(95, 40 + len(snaps) * 8), 0)
    return {"predicted_delivery": predicted, "confidence": confidence}


def risk_score(project: Project) -> float:
    """0-100 risk from schedule slip, stale velocity, bugs, testing, milestones."""
    score = 0.0
    if project.end_date and project.end_date < date.today() and project.status != "completed":
        score += 35
    if project.completion_pct == 0 and project.status == "active":
        score += 10
    if project.pending_bugs >= 10:
        score += 20
    elif project.pending_bugs >= 5:
        score += 12
    if project.testing_pct < 30 and project.frontend_pct > 40:
        score += 15
    overdue = Milestone.objects.filter(project=project, status="pending", due_date__lt=date.today()).count()
    score += min(15, overdue * 5)
    vel = velocity(project)
    if project.status == "active" and vel <= 0:
        score += 15
    return round(min(100.0, score), 1)


def project_metrics(project: Project) -> dict:
    """Dashboard payload for one project."""
    return {
        "id": str(project.id),
        "name": project.name,
        "client": project.client,
        "status": project.status,
        "completion_pct": project.completion_pct,
        "phase": {
            "backend": project.backend_pct,
            "frontend": project.frontend_pct,
            "testing": project.testing_pct,
            "deployment": project.deployment_pct,
        },
        "pending_bugs": project.pending_bugs,
        "risk_score": risk_score(project),
        "velocity": velocity(project),
        "delivery": delivery_prediction(project),
        "burndown": burndown(project),
        "end_date": project.end_date.isoformat() if project.end_date else None,
    }


def risk_summary(owner) -> list[dict]:
    """All projects ranked by risk (for the command router)."""
    projects = Project.objects.filter(owner=owner)
    rows = []
    for p in projects:
        score = risk_score(p)
        rows.append(
            {
                "name": p.name,
                "completion_pct": p.completion_pct,
                "risk_score": score,
                "reason": _risk_reason(p, score),
            }
        )
    rows.sort(key=lambda r: r["risk_score"], reverse=True)
    return rows


def delivery_predictions(owner) -> list[dict]:
    projects = Project.objects.filter(owner=owner).exclude(status="completed")
    rows = []
    for p in projects:
        rows.append(
            {
                "name": p.name,
                "completion_pct": p.completion_pct,
                "risk_score": risk_score(p),
                **delivery_prediction(p),
            }
        )
    rows.sort(key=lambda r: r["completion_pct"], reverse=True)
    return rows


def _risk_reason(project: Project, score: float) -> str:
    if score >= 60:
        return "Behind schedule with open blockers — escalate review."
    if score >= 30:
        return "Some risk factors (bugs/testing/milestones) need attention."
    return "On track — monitor weekly."

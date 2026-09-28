import { lazy, Suspense, useEffect } from "react";
import { Navigate, Route, Routes, useNavigate, useLocation } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import { AppShell } from "@/components/layout/AppShell";
import { ErrorBoundary } from "@/components/ErrorBoundary";
import { Spinner } from "@/components/ui/spinner";
import Login from "@/pages/Login";
import { useProfile } from "@/hooks/useIntelligence";

// Lazy load pages
const Dashboard = lazy(() => import("@/pages/Dashboard"));
const Onboarding = lazy(() => import("@/pages/Onboarding"));
const GitHubIntegration = lazy(() => import("@/pages/GitHubIntegration"));
const Insights = lazy(() => import("@/pages/Insights"));
const Alerts = lazy(() => import("@/pages/Alerts"));
const DailyPlan = lazy(() => import("@/pages/DailyPlan"));
const Profile = lazy(() => import("@/pages/Profile"));

// Legacy pages kept intact
const Github = lazy(() => import("@/pages/Github"));
const Projects = lazy(() => import("@/pages/Projects"));
const TasksCalendar = lazy(() => import("@/pages/TasksCalendar"));
const Reports = lazy(() => import("@/pages/Reports"));
const Resume = lazy(() => import("@/pages/Resume"));
const Portfolio = lazy(() => import("@/pages/Portfolio"));
const Learning = lazy(() => import("@/pages/Learning"));
const Linkedin = lazy(() => import("@/pages/Linkedin"));
const Notifications = lazy(() => import("@/pages/Notifications"));
const Assistant = lazy(() => import("@/pages/Assistant"));
const DeveloperOptions = lazy(() => import("@/pages/DeveloperOptions"));

const PageFallback = (
  <div className="flex h-64 items-center justify-center">
    <Spinner className="h-6 w-6 text-primary" />
  </div>
);

/** Redirects to /onboarding when the user has not completed onboarding yet. */
function OnboardingGuard({ children }: { children: React.ReactNode }) {
  const { data: profile, isLoading } = useProfile();
  const location = useLocation();
  const navigate = useNavigate();

  useEffect(() => {
    if (
      !isLoading &&
      profile &&
      !profile.onboarding_completed &&
      location.pathname !== "/onboarding"
    ) {
      // Only redirect on first-ever visit to "/" — do not force redirect from every page
      if (location.pathname === "/") {
        navigate("/onboarding", { replace: true });
      }
    }
  }, [isLoading, profile, location.pathname, navigate]);

  return <>{children}</>;
}

export default function App() {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <Spinner className="h-6 w-6 text-primary" />
      </div>
    );
  }

  if (!user) {
    return <Login />;
  }

  return (
    <AppShell>
      <ErrorBoundary>
        <OnboardingGuard>
          <Suspense fallback={PageFallback}>
            <Routes>
              {/* Intelligence routes */}
              <Route path="/" element={<Dashboard />} />
              <Route path="/dashboard" element={<Navigate to="/" replace />} />
              <Route path="/onboarding" element={<Onboarding />} />
              <Route path="/integrations/github" element={<GitHubIntegration />} />
              <Route path="/insights" element={<Insights />} />
              <Route path="/alerts" element={<Alerts />} />
              <Route path="/daily-plan" element={<DailyPlan />} />
              <Route path="/profile" element={<Profile />} />

              {/* Settings — redirects to profile for now */}
              <Route path="/settings" element={<Profile />} />

              {/* Legacy routes */}
              <Route path="/github" element={<Github />} />
              <Route path="/projects" element={<Projects />} />
              <Route path="/tasks" element={<TasksCalendar />} />
              <Route path="/reports" element={<Reports />} />
              <Route path="/resume" element={<Resume />} />
              <Route path="/portfolio" element={<Portfolio />} />
              <Route path="/learning" element={<Learning />} />
              <Route path="/linkedin" element={<Linkedin />} />
              <Route path="/notifications" element={<Notifications />} />
              <Route path="/assistant" element={<Assistant />} />
              <Route path="/developer" element={<DeveloperOptions />} />

              {/* Fallback */}
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </Suspense>
        </OnboardingGuard>
      </ErrorBoundary>
    </AppShell>
  );
}

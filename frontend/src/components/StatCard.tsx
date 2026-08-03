import type { LucideIcon } from "lucide-react";
import type { ReactNode } from "react";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

interface StatCardProps {
  icon: LucideIcon;
  label: string;
  value: string | number | null | undefined;
  sub?: ReactNode;
  loading?: boolean;
  tone?: "primary" | "success" | "warning" | "critical";
}

const toneClasses = {
  primary: "bg-[#6366f1]/12 text-[#6366f1] dark:text-[#818cf8]",
  success: "bg-[#0ca30c]/12 text-[#0d9e0d] dark:text-[#4ade80]",
  warning: "bg-[#fab219]/16 text-[#b77f00] dark:text-[#fbbf24]",
  critical: "bg-[#d03b3b]/12 text-[#c03434] dark:text-[#f87171]",
};

export function StatCard({ icon: Icon, label, value, sub, loading, tone = "primary" }: StatCardProps) {
  return (
    <Card className="p-4">
      <div className="flex items-center justify-between">
        <p className="text-xs font-medium text-muted">{label}</p>
        <span className={`flex h-8 w-8 items-center justify-center rounded-lg ${toneClasses[tone]}`}>
          <Icon className="h-4 w-4" />
        </span>
      </div>
      {loading ? (
        <Skeleton className="mt-2 h-8 w-20" />
      ) : (
        <p className="mt-1 text-2xl font-semibold tabular-nums">{value ?? "—"}</p>
      )}
      {sub && <div className="mt-1 text-xs text-muted">{sub}</div>}
    </Card>
  );
}

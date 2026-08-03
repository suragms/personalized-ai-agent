import { type HTMLAttributes } from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-[11px] font-medium tracking-wide",
  {
    variants: {
      variant: {
        default: "border-border bg-muted/10 text-foreground",
        primary: "border-transparent bg-primary/15 text-primary",
        success: "border-transparent bg-[#0ca30c]/12 text-[#0d9e0d] dark:text-[#4ade80]",
        warning: "border-transparent bg-[#fab219]/18 text-[#b77f00] dark:text-[#fbbf24]",
        critical: "border-transparent bg-[#d03b3b]/12 text-[#c03434] dark:text-[#f87171]",
        info: "border-transparent bg-[#22d3ee]/12 text-[#0891b2] dark:text-[#67e8f9]",
        violet: "border-transparent bg-[#9085e9]/15 text-[#6d5bd0] dark:text-[#b1a7f0]",
      },
    },
    defaultVariants: { variant: "default" },
  }
);

export interface BadgeProps extends HTMLAttributes<HTMLDivElement>, VariantProps<typeof badgeVariants> {}

export function Badge({ className, variant, ...props }: BadgeProps) {
  return <span className={cn(badgeVariants({ variant }), className)} {...props} />;
}

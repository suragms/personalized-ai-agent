import { cn } from "@/lib/utils";

interface AvatarProps {
  name?: string;
  url?: string;
  className?: string;
}

/** Initials avatar with optional image URL (falls back to initials). */
export function Avatar({ name, url, className }: AvatarProps) {
  const initials = (name ?? "?").split(/\s+/).map((p) => p[0]).slice(0, 2).join("").toUpperCase();
  return (
    <div
      className={cn(
        "flex h-8 w-8 shrink-0 items-center justify-center overflow-hidden rounded-full bg-gradient-to-br from-[#6366f1] to-[#22d3ee] text-xs font-semibold text-white",
        className
      )}
    >
      {url ? <img src={url} alt={name ?? ""} className="h-full w-full object-cover" /> : initials}
    </div>
  );
}

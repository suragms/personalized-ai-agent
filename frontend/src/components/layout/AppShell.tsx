import type { ReactNode } from "react";
import { NavLink, useNavigate } from "react-router-dom";
import {
  Bell,
  BrainCircuit,
  CalendarDays,
  Code2,
  FileText,
  FolderKanban,
  Github,
  GraduationCap,
  LayoutDashboard,
  Linkedin,
  LogOut,
  Moon,
  Search,
  Settings,
  Sparkles,
  Sun,
} from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { cn } from "@/lib/utils";
import { useTheme } from "@/contexts/ThemeContext";
import { useAuth } from "@/contexts/AuthContext";
import { notifications } from "@/services";
import { Avatar } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu";

const NAV = [
  { to: "/", label: "Overview", icon: LayoutDashboard },
  { to: "/github", label: "GitHub", icon: Github },
  { to: "/projects", label: "Projects", icon: FolderKanban },
  { to: "/tasks", label: "Tasks & Calendar", icon: CalendarDays },
  { to: "/reports", label: "Reports", icon: FileText },
  { to: "/resume", label: "Resume", icon: FileText },
  { to: "/portfolio", label: "Portfolio", icon: Sparkles },
  { to: "/learning", label: "Learning", icon: GraduationCap },
  { to: "/linkedin", label: "LinkedIn", icon: Linkedin },
  { to: "/assistant", label: "AI Assistant", icon: BrainCircuit, highlight: true },
];

function Sidebar() {
  return (
    <aside className="fixed inset-y-0 left-0 z-30 hidden w-60 flex-col border-r border-border bg-card-solid/60 backdrop-blur-xl lg:flex">
      <div className="flex h-16 items-center gap-2 px-5">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-[#6366f1] to-[#22d3ee]">
          <BrainCircuit className="h-4 w-4 text-white" />
        </div>
        <div className="leading-tight">
          <p className="text-sm font-semibold tracking-tight">AI Chief of Staff</p>
          <p className="text-[10px] text-muted">Personal Agent Platform</p>
        </div>
      </div>

      <nav className="flex-1 space-y-0.5 overflow-y-auto px-3 py-2">
        {NAV.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === "/"}
            className={({ isActive }) =>
              cn(
                "group flex items-center gap-2.5 rounded-md px-3 py-2 text-sm text-muted transition-colors hover:bg-muted/10 hover:text-foreground",
                isActive && "bg-primary/10 font-medium text-primary"
              )
            }
          >
            <item.icon className="h-4 w-4" />
            <span className="flex-1">{item.label}</span>
            {item.highlight && <Badge variant="info">AI</Badge>}
          </NavLink>
        ))}
      </nav>

      <div className="border-t border-border p-3">
        <NavLink
          to="/developer"
          className={({ isActive }) =>
            cn("flex items-center gap-2.5 rounded-md px-3 py-2 text-sm text-muted hover:bg-muted/10 hover:text-foreground", isActive && "bg-primary/10 text-primary")
          }
        >
          <Code2 className="h-4 w-4" /> Developer Options
        </NavLink>
        <NavLink
          to="/settings"
          className={({ isActive }) =>
            cn("flex items-center gap-2.5 rounded-md px-3 py-2 text-sm text-muted hover:bg-muted/10 hover:text-foreground", isActive && "bg-primary/10 text-primary")
          }
        >
          <Settings className="h-4 w-4" /> Settings
        </NavLink>
      </div>
    </aside>
  );
}

function Topbar() {
  const { theme, toggle } = useTheme();
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const unread = useQuery({ queryKey: ["unread"], queryFn: notifications.unread, refetchInterval: 30_000 });

  return (
    <header className="sticky top-0 z-20 flex h-16 items-center gap-3 border-b border-border bg-background/80 px-4 backdrop-blur-xl lg:px-6">
      <div className="flex items-center gap-2 lg:hidden">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-[#6366f1] to-[#22d3ee]">
          <BrainCircuit className="h-4 w-4 text-white" />
        </div>
      </div>

      <div className="relative hidden max-w-sm flex-1 md:block">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted" />
        <input
          placeholder="Ask or search… (try the AI Assistant)"
          className="h-9 w-full rounded-md border border-border bg-card-solid/50 pl-9 pr-3 text-sm outline-none focus:ring-2 focus:ring-primary/40"
          onKeyDown={(e) => {
            if (e.key === "Enter") navigate("/assistant");
          }}
        />
      </div>
      <div className="flex-1 md:hidden" />

      <Button variant="ghost" size="icon" onClick={toggle} aria-label="Toggle theme">
        {theme === "dark" ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
      </Button>

      <Button variant="ghost" size="icon" onClick={() => navigate("/notifications")} aria-label="Notifications" className="relative">
        <Bell className="h-4 w-4" />
        {unread.data && unread.data.unread > 0 ? (
          <span className="absolute -right-0.5 -top-0.5 flex h-4 min-w-4 items-center justify-center rounded-full bg-[#d03b3b] px-1 text-[10px] font-semibold text-white">
            {unread.data.unread}
          </span>
        ) : null}
      </Button>

      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <button className="flex items-center gap-2 rounded-full outline-none">
            <Avatar name={user?.username} url={user?.avatar_url} />
          </button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end">
          <div className="border-b border-border px-2 py-2">
            <p className="text-sm font-medium">{user?.username}</p>
            <p className="text-xs text-muted">{user?.email}</p>
          </div>
          <DropdownMenuItem onSelect={() => navigate("/settings")}>
            <Settings className="h-4 w-4" /> Settings
          </DropdownMenuItem>
          <DropdownMenuItem destructive onSelect={logout}>
            <LogOut className="h-4 w-4" /> Sign out
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    </header>
  );
}

export function AppShell({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen">
      <Sidebar />
      <div className="lg:pl-60">
        <Topbar />
        <main className="mx-auto max-w-[1400px] px-4 py-6 lg:px-8">{children}</main>
      </div>
    </div>
  );
}

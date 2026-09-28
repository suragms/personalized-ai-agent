import { lazy, Suspense } from "react";
import { Route, Routes } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import { AppShell } from "@/components/layout/AppShell";
import { ErrorBoundary } from "@/components/ErrorBoundary";
import { Spinner } from "@/components/ui/spinner";
import Login from "@/pages/Login";

// Lazy load pages for code splitting
const Overview = lazy(() => import("@/pages/Overview"));
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
const Settings = lazy(() => import("@/pages/Settings"));
const DeveloperOptions = lazy(() => import("@/pages/DeveloperOptions"));

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
        <Suspense fallback={
          <div className="flex h-screen items-center justify-center">
            <Spinner className="h-6 w-6 text-primary" />
          </div>
        }>
          <Routes>
            <Route path="/" element={<Overview />} />
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
            <Route path="/settings" element={<Settings />} />
            <Route path="/developer" element={<DeveloperOptions />} />
            <Route path="*" element={<Overview />} />
          </Routes>
        </Suspense>
      </ErrorBoundary>
    </AppShell>
  );
}

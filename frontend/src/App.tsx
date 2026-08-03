import { Route, Routes } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import { AppShell } from "@/components/layout/AppShell";
import { ErrorBoundary } from "@/components/ErrorBoundary";
import { Spinner } from "@/components/ui/spinner";
import Login from "@/pages/Login";
import Overview from "@/pages/Overview";
import Github from "@/pages/Github";
import Projects from "@/pages/Projects";
import TasksCalendar from "@/pages/TasksCalendar";
import Reports from "@/pages/Reports";
import Resume from "@/pages/Resume";
import Portfolio from "@/pages/Portfolio";
import Learning from "@/pages/Learning";
import Linkedin from "@/pages/Linkedin";
import Notifications from "@/pages/Notifications";
import Assistant from "@/pages/Assistant";
import Settings from "@/pages/Settings";

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
          <Route path="*" element={<Overview />} />
        </Routes>
      </ErrorBoundary>
    </AppShell>
  );
}

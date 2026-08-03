import { Component, type ErrorInfo, type ReactNode } from "react";
import { AlertTriangle } from "lucide-react";

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}
interface State {
  error: Error | null;
}

/** Catches render errors per-route so a broken section never blanks the app. */
export class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error("ErrorBoundary caught:", error, info.componentStack);
  }

  render() {
    if (this.state.error) {
      if (this.props.fallback) return this.props.fallback;
      return (
        <div className="flex flex-col items-center gap-2 rounded-lg border border-[#d03b3b]/30 bg-[#d03b3b]/5 p-8 text-center">
          <AlertTriangle className="h-8 w-8 text-[#d03b3b]" />
          <p className="text-sm font-medium">Something went wrong rendering this section.</p>
          <p className="max-w-md text-xs text-muted">{this.state.error.message}</p>
        </div>
      );
    }
    return this.props.children;
  }
}

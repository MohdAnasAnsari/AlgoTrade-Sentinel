"use client";

import { Component, type ReactNode } from "react";
import { AlertTriangle, RefreshCw } from "lucide-react";

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) return this.props.fallback;
      return (
        <div className="flex flex-col items-center justify-center min-h-[400px] gap-4">
          <div className="w-12 h-12 rounded-full bg-rose-500/10 flex items-center justify-center">
            <AlertTriangle className="w-6 h-6 text-rose-400" />
          </div>
          <div className="text-center">
            <p className="text-sm font-medium text-slate-100">
              Something went wrong
            </p>
            <p className="text-xs text-slate-400 mt-1">
              {this.state.error?.message ?? "An unexpected error occurred"}
            </p>
          </div>
          <button
            onClick={() => this.setState({ hasError: false })}
            className="flex items-center gap-2 text-xs text-cyan-400 hover:text-cyan-300 transition-colors"
          >
            <RefreshCw className="w-3 h-3" />
            Try again
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}

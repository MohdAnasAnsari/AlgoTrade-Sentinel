import { Loader2 } from "lucide-react";

interface LoadingStateProps {
  message?: string;
  className?: string;
}

export function LoadingState({
  message = "Loading...",
  className,
}: LoadingStateProps) {
  return (
    <div
      className={`flex flex-col items-center justify-center min-h-[400px] gap-3 ${className ?? ""}`}
    >
      <Loader2 className="w-8 h-8 text-cyan-400 animate-spin" />
      <p className="text-sm text-slate-400">{message}</p>
    </div>
  );
}

interface ErrorStateProps {
  message: string;
  className?: string;
  onRetry?: () => void | Promise<void>;
}

export function ErrorState({ message, className, onRetry }: ErrorStateProps) {
  return (
    <div
      className={`rounded-2xl border border-rose-500/20 bg-rose-500/10 px-4 py-3 text-sm text-rose-200 ${
        className ?? ""
      }`}
    >
      <div className="flex items-center justify-between gap-3">
        <span>{message}</span>
        {onRetry ? (
          <button
            type="button"
            onClick={() => void onRetry()}
            className="rounded-lg border border-rose-400/20 bg-rose-400/10 px-3 py-1.5 text-xs font-medium text-rose-100 transition hover:bg-rose-400/20"
          >
            Retry
          </button>
        ) : null}
      </div>
    </div>
  );
}

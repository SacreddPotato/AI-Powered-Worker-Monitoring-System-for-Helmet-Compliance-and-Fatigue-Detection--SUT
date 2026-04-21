import { useEffect, useState } from "react";

const SEVERITY_STYLES = {
  high: "border-l-red-500",
  medium: "border-l-amber-500",
  low: "border-l-blue-500",
};

export default function Toast({ alerts, onDismiss, maxVisible = 3 }) {
  const visibleAlerts = (alerts || []).slice(-maxVisible);

  return (
    <div className="fixed bottom-5 right-5 z-50 flex flex-col gap-2 pointer-events-none">
      {visibleAlerts.map((alert, i) => (
        <ToastItem key={alert.__toastId || alert.id || i} alert={alert} onDismiss={onDismiss} />
      ))}
    </div>
  );
}

function ToastItem({ alert, onDismiss }) {
  const dismissKey = alert.__toastId || alert.id;

  useEffect(() => {
    if (!dismissKey) return;
    const t = setTimeout(() => onDismiss(dismissKey), 8000);
    return () => clearTimeout(t);
  }, [dismissKey, onDismiss]);

  return (
    <div
      className={`pointer-events-auto bg-zinc-900 border border-zinc-800 rounded-lg p-3 min-w-[300px] animate-slide-in border-l-[3px] ${
        SEVERITY_STYLES[alert.severity] || "border-l-zinc-600"
      }`}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="text-xs font-semibold text-zinc-50">{alert.message}</div>
        <button
          onClick={(e) => {
            e.stopPropagation();
            if (dismissKey) onDismiss(dismissKey);
          }}
          className="text-zinc-500 hover:text-zinc-300 transition-colors"
          aria-label="Dismiss alert"
          title="Dismiss"
        >
          <svg viewBox="0 0 16 16" className="w-3 h-3" fill="none" stroke="currentColor" strokeWidth="1.8">
            <line x1="4" y1="4" x2="12" y2="12" />
            <line x1="12" y1="4" x2="4" y2="12" />
          </svg>
        </button>
      </div>
      <div className="text-[10px] text-zinc-500 mt-1">
        {alert.camera_name} &middot; Just now
      </div>
    </div>
  );
}

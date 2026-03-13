import { useEffect, useState } from "react";

const SEVERITY_STYLES = {
  high: "border-l-red-500",
  medium: "border-l-amber-500",
  low: "border-l-blue-500",
};

export default function Toast({ alerts, onDismiss }) {
  return (
    <div className="fixed bottom-5 right-5 z-50 flex flex-col gap-2 pointer-events-none">
      {alerts.map((alert) => (
        <ToastItem key={alert.id} alert={alert} onDismiss={() => onDismiss(alert.id)} />
      ))}
    </div>
  );
}

function ToastItem({ alert, onDismiss }) {
  useEffect(() => {
    const t = setTimeout(onDismiss, 8000);
    return () => clearTimeout(t);
  }, [onDismiss]);

  return (
    <div
      className={`pointer-events-auto bg-zinc-900 border border-zinc-800 rounded-lg p-3 min-w-[300px] animate-slide-in border-l-[3px] ${
        SEVERITY_STYLES[alert.severity] || "border-l-zinc-600"
      }`}
    >
      <div className="text-xs font-semibold text-zinc-50">{alert.message}</div>
      <div className="text-[10px] text-zinc-500 mt-1">
        {alert.camera_name} &middot; Just now
      </div>
    </div>
  );
}

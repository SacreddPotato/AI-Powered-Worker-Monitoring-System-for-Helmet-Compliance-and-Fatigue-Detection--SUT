import { useEffect, useState } from "react";

const SEVERITY_STYLES = {
  high: "border-l-red-500",
  medium: "border-l-amber-500",
  low: "border-l-blue-500",
};

export default function Toast({ alerts, onDismiss }) {
  if (alerts.length === 0) return null;
  
  return (
    <div className="fixed bottom-6 right-6 z-[60] flex flex-col gap-2 pointer-events-none w-80">
      <div className="flex justify-between items-center mb-1 pointer-events-auto">
        <span className="text-[9px] font-black text-zinc-500 uppercase tracking-widest pl-1">Notifications</span>
        {alerts.length > 1 && (
          <button 
            onClick={() => alerts.forEach(a => onDismiss(a.id))}
            className="text-[9px] font-bold text-zinc-600 hover:text-zinc-300 transition-colors"
          >
            Clear All
          </button>
        )}
      </div>
      {alerts.map((alert) => (
        <ToastItem key={alert.id} alert={alert} onDismiss={() => onDismiss(alert.id)} />
      ))}
    </div>
  );
}

function ToastItem({ alert, onDismiss }) {
  useEffect(() => {
    const t = setTimeout(onDismiss, 6000);
    return () => clearTimeout(t);
  }, [onDismiss]);

  const severityColor = alert.severity === "high" ? "bg-red-500" : alert.severity === "medium" ? "bg-amber-500" : "bg-blue-500";

  return (
    <div
      className="pointer-events-auto bg-[#0a0a0d]/90 backdrop-blur-md border border-zinc-800/80 rounded-lg p-2.5 shadow-2xl animate-slide-in relative group overflow-hidden"
    >
      <div className={`absolute top-0 bottom-0 left-0 w-1 ${severityColor}`} />
      <div className="flex justify-between items-start pl-2 gap-3">
        <div className="flex-1 min-w-0">
          <div className="text-[10px] font-bold text-zinc-100 leading-tight truncate">{alert.message}</div>
          <div className="text-[8px] text-zinc-500 mt-1 uppercase tracking-tight font-medium opacity-80">
            {alert.camera_name} &middot; Just now
          </div>
        </div>
        <button
          onClick={onDismiss}
          className="text-zinc-600 hover:text-zinc-200 transition-colors p-0.5 opacity-0 group-hover:opacity-100"
        >
          <svg viewBox="0 0 16 16" className="w-3 h-3" fill="none" stroke="currentColor" strokeWidth="2.5">
            <path d="M4 4L12 12M12 4L4 12" />
          </svg>
        </button>
      </div>
    </div>
  );
}

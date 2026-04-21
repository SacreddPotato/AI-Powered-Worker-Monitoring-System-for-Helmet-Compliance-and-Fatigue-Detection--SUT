const SEV_STYLES = {
  high: { bg: "bg-red-500/5", border: "border-l-red-500", label: "text-red-400" },
  medium: { bg: "bg-amber-500/5", border: "border-l-amber-500", label: "text-amber-400" },
  low: { bg: "bg-blue-500/5", border: "border-l-blue-500", label: "text-blue-400" },
};

export default function AlertCard({ alert, compact = false, onClick, onAcknowledge }) {
  const s = SEV_STYLES[alert.severity] || SEV_STYLES.low;

  return (
    <div
      onClick={onClick}
      className={`group relative ${s.bg} border-l-[2px] ${s.border} rounded-md p-2 cursor-pointer transition-all hover:bg-white/[0.04] active:scale-[0.98] ${
        compact ? "mb-1.5" : "mb-2.5"
      }`}
    >
      <div className="flex justify-between items-start gap-3">
        <div className="flex-1 min-w-0">
          <div className="text-[10px] font-bold text-zinc-100 leading-tight truncate">{alert.message}</div>
          {!compact && alert.payload?.description && (
            <div className="text-[9px] text-zinc-500 mt-0.5 leading-tight line-clamp-1">{alert.payload.description}</div>
          )}
          <div className="flex items-center gap-1.5 mt-1.5 opacity-60">
             <div className="text-[7px] font-black text-zinc-400 uppercase tracking-widest truncate">{alert.camera_name}</div>
             <div className="w-0.5 h-0.5 rounded-full bg-zinc-700" />
             <div className="text-[7px] font-medium text-zinc-500 whitespace-nowrap">{formatTime(alert.created_at)}</div>
          </div>
        </div>
        
        {onAcknowledge && (
          <button
            onClick={(e) => {
              e.stopPropagation();
              onAcknowledge(alert.id);
            }}
            className="w-5 h-5 flex items-center justify-center rounded-md bg-zinc-950/40 border border-white/5 text-zinc-500 hover:text-green-400 hover:border-green-500/30 hover:bg-green-500/10 transition-all opacity-0 group-hover:opacity-100"
            title="Mark as resolved"
          >
            <svg viewBox="0 0 16 16" className="w-3 h-3" fill="none" stroke="currentColor" strokeWidth="2.5">
              <path d="M3 8.5L6.5 12L13 4" />
            </svg>
          </button>
        )}
      </div>
    </div>
  );
}

function formatTime(iso) {
  if (!iso) return "";
  const diff = (Date.now() - new Date(iso)) / 1000;
  if (diff < 60) return `${Math.round(diff)}s ago`;
  if (diff < 3600) return `${Math.round(diff / 60)}m ago`;
  return `${Math.round(diff / 3600)}h ago`;
}

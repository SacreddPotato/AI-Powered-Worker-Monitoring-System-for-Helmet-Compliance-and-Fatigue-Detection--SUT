const SEV_STYLES = {
  high: { bg: "bg-red-500/5", border: "border-l-red-500", label: "text-red-400" },
  medium: { bg: "bg-amber-500/5", border: "border-l-amber-500", label: "text-amber-400" },
  low: { bg: "bg-blue-500/5", border: "border-l-blue-500", label: "text-blue-400" },
};

export default function AlertCard({ alert, compact = false, onClick }) {
  const s = SEV_STYLES[alert.severity] || SEV_STYLES.low;

  return (
    <div
      onClick={onClick}
      className={`${s.bg} border-l-[3px] ${s.border} rounded-lg p-2.5 cursor-pointer transition-colors hover:bg-white/[0.02] ${
        compact ? "mb-1.5" : "mb-2"
      }`}
    >
      <div className="text-[10px] font-semibold text-zinc-100">{alert.message}</div>
      {!compact && alert.payload?.description && (
        <div className="text-[9px] text-zinc-500 mt-1">{alert.payload.description}</div>
      )}
      <div className="text-[8px] text-zinc-600 mt-1">
        {alert.camera_name} &middot; {formatTime(alert.created_at)}
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

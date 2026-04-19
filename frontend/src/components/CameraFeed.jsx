import Badge from "./Badge";
import useCameraStream from "../hooks/useCameraStream";

export default function CameraFeed({ camera, isHero = false, onClick, onDelete, badges = [], overlays = [], isDeleting = false, streamDisabled = false }) {
  const { src, status } = useCameraStream(streamDisabled ? null : camera.id, overlays);

  return (
    <div
      onClick={onClick}
      className={`bg-surface-alt border border-zinc-800 rounded-lg relative overflow-hidden cursor-pointer transition-colors hover:border-zinc-700 ${
        isHero ? "col-span-2" : ""
      }`}
    >
      {/* WebSocket JPEG stream */}
      {src ? (
        <img
          src={src}
          alt={camera.name}
          className="absolute inset-0 w-full h-full object-cover"
        />
      ) : (
        <div className="absolute inset-0 flex flex-col items-center justify-center bg-zinc-950">
          <svg viewBox="0 0 24 24" className="w-8 h-8 text-zinc-700 mb-2" fill="none" stroke="currentColor" strokeWidth="1.5">
            <path d="M23 19a2 2 0 01-2 2H3a2 2 0 01-2-2V8a2 2 0 012-2h4l2-3h6l2 3h4a2 2 0 012 2z" />
            <circle cx="12" cy="13" r="4" />
          </svg>
          <span className="text-[10px] text-zinc-600">
            {streamDisabled ? "Unavailable on Hugging Face demo" : status === "connecting" ? "Connecting..." : "No signal"}
          </span>
        </div>
      )}

      {/* Gradient overlay */}
      <div className="absolute inset-0 bg-gradient-to-b from-transparent via-transparent to-black/80 pointer-events-none" />

      {/* Scan line on hero */}
      {isHero && (
        <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-blue-500/30 to-transparent animate-scan pointer-events-none" />
      )}

      {/* Top bar */}
      <div className="absolute top-2.5 left-3 right-3 flex justify-between items-center z-10">
        <span className="text-[10px] font-semibold text-zinc-400">{camera.name}{camera.location ? ` — ${camera.location}` : ""}</span>
        <div className="flex items-center gap-2">
          {onDelete && (
            <button
              onClick={(e) => { e.stopPropagation(); if (!isDeleting) onDelete(); }}
              className="text-zinc-600 hover:text-red-400 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
              disabled={isDeleting}
              title="Remove camera"
            >
              {isDeleting ? (
                <svg viewBox="0 0 24 24" className="w-3 h-3 animate-spin" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M21 12a9 9 0 1 1-2.64-6.36" />
                </svg>
              ) : (
                <svg viewBox="0 0 16 16" className="w-3 h-3" fill="none" stroke="currentColor" strokeWidth="1.8"><line x1="4" y1="4" x2="12" y2="12" /><line x1="12" y1="4" x2="4" y2="12" /></svg>
              )}
            </button>
          )}
          <div className="flex items-center gap-1">
            <span className={`w-1.5 h-1.5 rounded-full ${streamDisabled ? "bg-amber-500" : status === "live" ? "bg-red-500 animate-pulse-dot" : status === "connecting" ? "bg-amber-500 animate-pulse" : "bg-zinc-600"}`} />
            <span className={`text-[8px] font-semibold ${streamDisabled ? "text-amber-400" : status === "live" ? "text-red-500" : status === "connecting" ? "text-amber-500" : "text-zinc-600"}`}>
              {streamDisabled ? "DEMO" : status === "live" ? "LIVE" : status === "connecting" ? "..." : "OFFLINE"}
            </span>
          </div>
        </div>
      </div>

      {/* Bottom badges */}
      <div className="absolute bottom-2.5 left-3 right-3 flex justify-between items-end z-10">
        <div className="flex gap-1 flex-wrap">
          {badges.map((b, i) => (
            <Badge key={i} variant={b.variant}>{b.label}</Badge>
          ))}
          {badges.length === 0 && status === "live" && <Badge variant="success">All clear</Badge>}
        </div>
      </div>
    </div>
  );
}

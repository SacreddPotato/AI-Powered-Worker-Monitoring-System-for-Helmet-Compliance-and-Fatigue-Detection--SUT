import { useState } from "react";
import Badge from "./Badge";
import { api } from "../api";

export default function CameraFeed({ camera, isHero = false, onClick, onDelete, badges = [], overlays = [] }) {
  const [error, setError] = useState(false);

  const streamUrl = api.cameraStreamUrl(camera.id, overlays);

  return (
    <div
      onClick={onClick}
      className={`bg-surface-alt border border-zinc-800 rounded-lg relative overflow-hidden cursor-pointer transition-colors hover:border-zinc-700 ${
        isHero ? "col-span-2" : ""
      }`}
    >
      {/* MJPEG stream — no lazy loading; must connect immediately */}
      {!error ? (
        <img
          src={streamUrl}
          alt={camera.name}
          className="absolute inset-0 w-full h-full object-cover"
          onError={() => setError(true)}
        />
      ) : (
        <div className="absolute inset-0 flex flex-col items-center justify-center bg-zinc-950">
          <svg viewBox="0 0 24 24" className="w-8 h-8 text-zinc-700 mb-2" fill="none" stroke="currentColor" strokeWidth="1.5">
            <path d="M23 19a2 2 0 01-2 2H3a2 2 0 01-2-2V8a2 2 0 012-2h4l2-3h6l2 3h4a2 2 0 012 2z" />
            <line x1="4" y1="4" x2="20" y2="20" />
          </svg>
          <span className="text-[10px] text-zinc-600">No signal</span>
          <button
            onClick={(e) => { e.stopPropagation(); setError(false); }}
            className="mt-2 text-[9px] text-blue-400 hover:text-blue-300"
          >
            Retry
          </button>
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
              onClick={(e) => { e.stopPropagation(); onDelete(); }}
              className="text-zinc-600 hover:text-red-400 transition-colors"
              title="Remove camera"
            >
              <svg viewBox="0 0 16 16" className="w-3 h-3" fill="none" stroke="currentColor" strokeWidth="1.8"><line x1="4" y1="4" x2="12" y2="12" /><line x1="12" y1="4" x2="4" y2="12" /></svg>
            </button>
          )}
          <div className="flex items-center gap-1">
            <span className={`w-1.5 h-1.5 rounded-full ${error ? "bg-zinc-600" : "bg-red-500 animate-pulse-dot"}`} />
            <span className={`text-[8px] font-semibold ${error ? "text-zinc-600" : "text-red-500"}`}>
              {error ? "OFFLINE" : "LIVE"}
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
          {badges.length === 0 && !error && <Badge variant="success">All clear</Badge>}
        </div>
      </div>
    </div>
  );
}

import { useState, useRef, useEffect, useCallback } from "react";
import Badge from "./Badge";
import { api } from "../api";
import useCameraStream from "../hooks/useCameraStream";

const clamp01 = (v) => Math.max(0, Math.min(1, v));

// Map a viewport point to normalized [0,1] frame coordinates, accounting for the
// `object-cover` cropping of the streamed <img> so a drawn zone lands where the
// user dragged once the server burns it back onto the feed.
function pointToFrameNorm(clientX, clientY, imgEl) {
  const rect = imgEl.getBoundingClientRect();
  const natW = imgEl.naturalWidth || rect.width;
  const natH = imgEl.naturalHeight || rect.height;
  const scale = Math.max(rect.width / natW, rect.height / natH);
  const dispW = natW * scale;
  const dispH = natH * scale;
  const offX = (rect.width - dispW) / 2;
  const offY = (rect.height - dispH) / 2;
  return {
    x: clamp01((clientX - rect.left - offX) / dispW),
    y: clamp01((clientY - rect.top - offY) / dispH),
  };
}

export default function CameraFeed({ camera, isHero = false, onClick, onDelete, badges = [], overlays = null, isDeleting = false, streamDisabled = false, inference = null }) {
  const { src, status } = useCameraStream(streamDisabled ? null : camera.id, overlays);

  const imgRef = useRef(null);
  const [zoneMode, setZoneMode] = useState(false);
  const [zones, setZones] = useState([]);
  const [drag, setDrag] = useState(null); // { startX, startY, curX, curY } in client coords

  const loadZones = useCallback(() => {
    if (streamDisabled) return Promise.resolve();
    return api
      .listZones(camera.id)
      .then((data) => setZones(data?.results || data || []))
      .catch(() => {});
  }, [camera.id, streamDisabled]);

  // Refresh zones (and their live counts) while the zone panel is open.
  useEffect(() => {
    if (!zoneMode) return undefined;
    loadZones();
    const interval = setInterval(loadZones, 2000);
    return () => clearInterval(interval);
  }, [zoneMode, loadZones]);

  function handleMouseDown(e) {
    if (!zoneMode || !imgRef.current) return;
    e.stopPropagation();
    setDrag({ startX: e.clientX, startY: e.clientY, curX: e.clientX, curY: e.clientY });
  }

  function handleMouseMove(e) {
    if (!drag) return;
    e.stopPropagation();
    setDrag((d) => (d ? { ...d, curX: e.clientX, curY: e.clientY } : d));
  }

  async function handleMouseUp(e) {
    if (!drag || !imgRef.current) {
      setDrag(null);
      return;
    }
    e.stopPropagation();
    const a = pointToFrameNorm(drag.startX, drag.startY, imgRef.current);
    const b = pointToFrameNorm(e.clientX, e.clientY, imgRef.current);
    setDrag(null);

    const x1 = Math.min(a.x, b.x);
    const y1 = Math.min(a.y, b.y);
    const x2 = Math.max(a.x, b.x);
    const y2 = Math.max(a.y, b.y);
    // Ignore accidental clicks / slivers.
    if (x2 - x1 < 0.03 || y2 - y1 < 0.03) return;

    const raw = window.prompt("Name this counting zone", `Zone ${zones.length + 1}`);
    if (raw === null) return; // user cancelled
    const name = raw.trim() || `Zone ${zones.length + 1}`;
    try {
      await api.createZone(camera.id, { name, x1, y1, x2, y2 });
      await loadZones();
    } catch {
      window.alert("Could not create zone. Please try again.");
    }
  }

  async function handleReset(zoneId) {
    try {
      await api.resetZone(camera.id, zoneId);
      await loadZones();
    } catch {
      /* ignore */
    }
  }

  async function handleDeleteZone(zoneId) {
    try {
      await api.deleteZone(camera.id, zoneId);
      await loadZones();
    } catch {
      /* ignore */
    }
  }

  // Live feedback rectangle while dragging, positioned relative to the feed.
  let dragRect = null;
  if (drag && imgRef.current) {
    const rect = imgRef.current.getBoundingClientRect();
    dragRect = {
      left: Math.min(drag.startX, drag.curX) - rect.left,
      top: Math.min(drag.startY, drag.curY) - rect.top,
      width: Math.abs(drag.curX - drag.startX),
      height: Math.abs(drag.curY - drag.startY),
    };
  }

  const inferenceStatus = inference?.status || "unknown";
  const aiLabel = streamDisabled
    ? "AI DEMO"
    : inferenceStatus === "running"
      ? "AI RUNNING"
      : inferenceStatus === "loading"
        ? "AI LOADING"
        : inferenceStatus === "disabled"
          ? "AI DISABLED"
          : inferenceStatus === "stale"
            ? "AI STALE"
            : inferenceStatus === "error"
              ? "AI ERROR"
              : "AI UNKNOWN";
  const aiClass = streamDisabled
    ? "text-amber-300"
    : inferenceStatus === "running"
      ? "text-emerald-300"
      : inferenceStatus === "loading"
        ? "text-blue-300"
        : inferenceStatus === "disabled"
          ? "text-zinc-400"
          : inferenceStatus === "error"
            ? "text-red-300"
            : "text-amber-300";

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
          ref={imgRef}
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

      {/* Zone drawing surface — only intercepts events while in zone mode */}
      {zoneMode && src && (
        <div
          className="absolute inset-0 z-20 cursor-crosshair"
          onMouseDown={handleMouseDown}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
          onMouseLeave={(e) => drag && handleMouseUp(e)}
        >
          {dragRect && (
            <div
              className="absolute border-2 border-fuchsia-400 bg-fuchsia-400/10 pointer-events-none"
              style={{ left: dragRect.left, top: dragRect.top, width: dragRect.width, height: dragRect.height }}
            />
          )}
        </div>
      )}

      {/* Scan line on hero */}
      {isHero && (
        <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-blue-500/30 to-transparent animate-scan pointer-events-none" />
      )}

      {/* Top bar */}
      <div className="absolute top-2.5 left-3 right-3 flex justify-between items-center z-30">
        <span className="text-[10px] font-semibold text-zinc-400">{camera.name}{camera.location ? ` — ${camera.location}` : ""}</span>
        <div className="flex items-center gap-2">
          {!streamDisabled && (
            <button
              onClick={(e) => { e.stopPropagation(); setZoneMode((v) => !v); }}
              className={`text-[8px] font-semibold rounded px-1.5 py-0.5 border transition-colors ${
                zoneMode
                  ? "text-fuchsia-300 bg-fuchsia-500/20 border-fuchsia-500/40"
                  : "text-zinc-400 bg-zinc-800/60 border-zinc-700 hover:text-fuchsia-300"
              }`}
              title="Draw people-counting zones"
            >
              ZONES
            </button>
          )}
          <span className={`text-[8px] font-semibold ${aiClass}`}>{aiLabel}</span>
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

      {/* Zone management panel */}
      {zoneMode && (
        <div
          className="absolute top-9 right-3 z-30 w-44 bg-zinc-950/90 border border-fuchsia-500/30 rounded-lg p-2 text-zinc-300"
          onClick={(e) => e.stopPropagation()}
        >
          <div className="text-[8px] uppercase tracking-wider text-fuchsia-300/80 mb-1.5">Counting Zones</div>
          {zones.length === 0 ? (
            <p className="text-[9px] text-zinc-500 leading-snug">Drag on the feed to draw a zone.</p>
          ) : (
            <div className="space-y-1">
              {zones.map((z) => (
                <div key={z.id} className="flex items-center justify-between gap-1 bg-zinc-900/70 rounded px-1.5 py-1">
                  <div className="min-w-0">
                    <div className="text-[9px] font-semibold truncate">{z.name}</div>
                    <div className="text-[8px] text-fuchsia-300">{z.count} passed</div>
                  </div>
                  <div className="flex items-center gap-1 shrink-0">
                    <button
                      onClick={() => handleReset(z.id)}
                      className="text-[8px] text-zinc-400 hover:text-fuchsia-300"
                      title="Reset count"
                    >
                      ↺
                    </button>
                    <button
                      onClick={() => handleDeleteZone(z.id)}
                      className="text-[8px] text-zinc-500 hover:text-red-400"
                      title="Delete zone"
                    >
                      ✕
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Bottom badges */}
      <div className="absolute bottom-2.5 left-3 right-3 flex justify-between items-end z-10">
        <div className="flex gap-1 flex-wrap">
          {badges.map((b, i) => (
            <Badge key={i} variant={b.variant}>{b.label}</Badge>
          ))}
          {badges.length === 0 && status === "live" && (
            <Badge variant={inferenceStatus === "running" ? "success" : inferenceStatus === "error" ? "danger" : "muted"}>
              {inferenceStatus === "running"
                ? "Inference running"
                : inferenceStatus === "loading"
                  ? "Models loading"
                  : inferenceStatus === "disabled"
                    ? "Inference disabled"
                    : inferenceStatus === "stale"
                      ? "Inference stale"
                      : inferenceStatus === "error"
                        ? "Inference error"
                        : "Inference unknown"}
            </Badge>
          )}
        </div>
      </div>
    </div>
  );
}

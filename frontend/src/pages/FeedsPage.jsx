import { useState, useEffect } from "react";
import { api } from "../api";
import CameraFeed from "../components/CameraFeed";
import AlertCard from "../components/AlertCard";
import Toggle from "../components/Toggle";

const ALL_MODELS = ["helmet", "fatigue", "vest", "gloves", "goggles", "face_shield", "safety_suit"];

export default function FeedsPage() {
  const [cameras, setCameras] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [heroId, setHeroId] = useState(null);
  const [showAdd, setShowAdd] = useState(false);
  const [overlays, setOverlays] = useState([...ALL_MODELS]);
  const [deletingIds, setDeletingIds] = useState([]);

  function loadCameras() {
    api.listCameras().then((data) => {
      const list = data.results || data;
      setCameras(list);
      if (list.length > 0 && !heroId) setHeroId(list[0].id);
    });
  }

  useEffect(() => {
    loadCameras();
    api.listAlerts({ status: "open", limit: 20 }).then((data) => {
      setAlerts(data.results || data);
    });
    const interval = setInterval(() => {
      api.listAlerts({ status: "open", limit: 20 }).then((data) => setAlerts(data.results || data));
    }, 5000);
    return () => clearInterval(interval);
  }, []);

  async function handleAddCamera(form) {
    // Duplicate check — reject if source_url already exists
    const existing = cameras.find((c) => c.source_url === form.source_url);
    if (existing) {
      alert(`Camera "${existing.name}" already uses source ${form.source_url}`);
      return;
    }
    await api.createCamera(form);
    setShowAdd(false);
    loadCameras();
  }

  async function handleDeleteCamera(id) {
    if (deletingIds.includes(id)) return;

    const previousCameras = cameras;
    const remainingCameras = cameras.filter((c) => c.id !== id);
    setDeletingIds((prev) => [...prev, id]);
    setCameras(remainingCameras);
    if (heroId === id) {
      setHeroId(remainingCameras.length > 0 ? remainingCameras[0].id : null);
    }

    try {
      await api.deleteCamera(id);
      loadCameras();
    } catch {
      setCameras(previousCameras);
      if (heroId === id) setHeroId(id);
      alert("Failed to remove camera. Please try again.");
    } finally {
      setDeletingIds((prev) => prev.filter((x) => x !== id));
    }
  }

  function toggleOverlay(key) {
    setOverlays((prev) => (prev.includes(key) ? prev.filter((k) => k !== key) : [...prev, key]));
  }

  async function handleAcknowledge(id) {
    // Optimistic update: remove from local state immediately
    setAlerts((prev) => prev.filter((a) => a.id !== id));
    try {
      await api.acknowledgeAlert(id);
    } catch (err) {
      console.error("Failed to acknowledge alert:", err);
      // Optional: Re-fetch or toast error
    }
  }

  async function handleClearAll() {
    const ids = alerts.map((a) => a.id);
    if (ids.length === 0) return;
    
    // Clear state immediately for best snappy feel
    setAlerts([]);
    try {
      // Clear all in background
      await Promise.all(ids.map((id) => api.acknowledgeAlert(id)));
    } catch (err) {
      console.error("Failed to clear all alerts:", err);
      loadAlerts(); // Re-fetch on total failure
    }
  }

  function loadAlerts() {
    api.listAlerts({ status: "open", limit: 20 }).then((data) => {
      setAlerts(data.results || data);
    });
  }

  const hero = cameras.find((c) => c.id === heroId);
  const others = cameras.filter((c) => c.id !== heroId);

  const grouped = { high: [], medium: [], low: [] };
  alerts.forEach((a) => (grouped[a.severity] || grouped.low).push(a));

  return (
    <>
      <div className="px-5 py-4 flex justify-between items-center border-b border-zinc-800/60 shrink-0">
        <div className="flex items-baseline gap-2">
          <h1 className="text-base font-semibold text-zinc-50">Live Feeds</h1>
          <span className="text-xs text-zinc-600">{cameras.length} cameras</span>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => setShowAdd(true)}
            className="flex items-center gap-1.5 text-[10px] font-semibold text-blue-400 bg-blue-500/10 border border-blue-500/25 rounded-lg px-3 py-1.5 hover:bg-blue-500/20 transition-colors"
          >
            <svg viewBox="0 0 16 16" className="w-3 h-3" fill="none" stroke="currentColor" strokeWidth="2"><line x1="8" y1="2" x2="8" y2="14" /><line x1="2" y1="8" x2="14" y2="8" /></svg>
            Add Camera
          </button>
          <div className="flex items-center gap-1.5 text-[10px] text-zinc-500 bg-zinc-900 border border-zinc-800 rounded-full px-3 py-1">
            <span className="w-1.5 h-1.5 bg-green-500 rounded-full shadow-[0_0_6px_rgba(34,197,94,.5)]" />
            {cameras.length > 0 ? "Systems online" : "No cameras"}
          </div>
        </div>
      </div>

      {/* Overlay toggle bar */}
      {cameras.length > 0 && (
        <div className="px-5 py-2 border-b border-zinc-800/60 flex items-center gap-4 shrink-0">
          <span className="text-[9px] text-zinc-600 uppercase tracking-wider">Overlays</span>
          {ALL_MODELS.map((key) => (
            <label key={key} className="flex items-center gap-1.5 cursor-pointer select-none">
              <Toggle enabled={overlays.includes(key)} onChange={() => toggleOverlay(key)} size="sm" />
              <span className={`text-[10px] capitalize ${overlays.includes(key) ? "text-zinc-300" : "text-zinc-600"}`}>{key}</span>
            </label>
          ))}
        </div>
      )}

      <div className="flex-1 flex overflow-hidden">
        {/* Camera grid */}
        <div className="flex-1 p-3 overflow-auto">
          {cameras.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center gap-3">
              <div className="text-zinc-700 text-3xl">
                <svg viewBox="0 0 24 24" className="w-12 h-12" fill="none" stroke="currentColor" strokeWidth="1.2">
                  <path d="M23 19a2 2 0 01-2 2H3a2 2 0 01-2-2V8a2 2 0 012-2h4l2-3h6l2 3h4a2 2 0 012 2z" />
                  <circle cx="12" cy="13" r="4" />
                </svg>
              </div>
              <p className="text-[11px] text-zinc-600">No cameras configured</p>
              <button
                onClick={() => setShowAdd(true)}
                className="text-[10px] font-semibold text-blue-400 bg-blue-500/10 border border-blue-500/25 rounded-lg px-4 py-2 hover:bg-blue-500/20 transition-colors"
              >
                Add your first camera
              </button>
            </div>
          ) : (
            <div className="grid grid-cols-2 gap-2 h-full" style={{ gridTemplateRows: cameras.length > 1 ? "1.6fr 1fr" : "1fr" }}>
              {hero && (
                <CameraFeed
                  camera={hero}
                  isHero
                  overlays={overlays}
                  badges={getBadges(alerts, hero.id)}
                  isDeleting={deletingIds.includes(hero.id)}
                  onDelete={() => handleDeleteCamera(hero.id)}
                />
              )}
              {others.slice(0, 2).map((cam) => (
                <CameraFeed
                  key={cam.id}
                  camera={cam}
                  overlays={overlays}
                  onClick={() => setHeroId(cam.id)}
                  badges={getBadges(alerts, cam.id)}
                  isDeleting={deletingIds.includes(cam.id)}
                  onDelete={() => handleDeleteCamera(cam.id)}
                />
              ))}
            </div>
          )}
        </div>

        {/* Right Sidebar: Models & Alerts */}
        <div className="w-[300px] bg-[#0c0c0f] border-l border-zinc-800/60 flex flex-col shrink-0 overflow-hidden">
          {/* Top Half: Engine Toggles */}
          <div className="flex-none p-4 border-b border-zinc-800/60 bg-black/40">
            <h2 className="text-[10px] uppercase tracking-[0.2em] font-black text-blue-500/80 mb-3">Intelligence Layers</h2>
            <div className="grid grid-cols-2 gap-2">
              {ALL_MODELS.map((key) => (
                <label key={key} className="flex items-center justify-between gap-1 cursor-pointer bg-zinc-900/40 px-2.5 py-2 rounded-md border border-zinc-800/50 hover:border-zinc-700 transition-colors">
                  <span className={`text-[9px] font-bold uppercase tracking-tighter ${overlays.includes(key) ? "text-zinc-300" : "text-zinc-600"}`}>
                    {key.replace('_', ' ')}
                  </span>
                  <Toggle enabled={overlays.includes(key)} onChange={() => toggleOverlay(key)} size="sm" />
                </label>
              ))}
            </div>
          </div>

          {/* Bottom Half: Live Queue (Alerts) */}
          <div className="flex-none px-4 py-3 border-b border-zinc-800/60 flex justify-between items-center bg-zinc-950">
            <div className="flex items-center gap-2">
              <span className="text-[10px] font-black uppercase tracking-widest text-zinc-400">Live Violations</span>
              {alerts.length > 0 && (
                <span className="text-[9px] font-bold bg-red-500/10 text-red-500/80 px-2 py-0.5 rounded-full border border-red-500/20">
                  {alerts.length}
                </span>
              )}
            </div>
            {alerts.length > 0 && (
              <button 
                onClick={handleClearAll}
                className="text-[9px] font-bold text-zinc-500 hover:text-zinc-200 transition-colors uppercase tracking-tight"
              >
                Clear All
              </button>
            )}
          </div>
          <div className="flex-1 overflow-y-auto px-3 py-3 space-y-3 bg-[#101014]">
            {["high", "medium", "low"].map(
              (sev) =>
                grouped[sev].length > 0 && (
                  <div key={sev}>
                    <div className="text-[8px] font-black text-zinc-600 uppercase tracking-widest px-1 py-1.5 mb-1">
                      {sev === "high" ? "Critical Priority" : sev === "medium" ? "Warning" : "Info"}
                    </div>
                    {grouped[sev].map((alert) => (
                      <AlertCard 
                        key={alert.id} 
                        alert={alert} 
                        compact 
                        onAcknowledge={handleAcknowledge}
                      />
                    ))}
                  </div>
                )
            )}
            {alerts.length === 0 && (
              <div className="text-[10px] text-zinc-700 text-center py-8">No active violations detected.</div>
            )}
          </div>
        </div>
      </div>

      {showAdd && <AddCameraDialog onClose={() => setShowAdd(false)} onSubmit={handleAddCamera} />}
    </>
  );
}

function AddCameraDialog({ onClose, onSubmit }) {
  const [form, setForm] = useState({ name: "", source_url: "", location: "" });
  const [devices, setDevices] = useState([]);
  const [scanning, setScanning] = useState(false);
  const [preview, setPreview] = useState(null);       // object URL for preview image
  const [probing, setProbing] = useState(false);
  const [probeError, setProbeError] = useState("");

  useEffect(() => {
    scanDevices();
  }, []);

  // Clean up preview blob URL
  useEffect(() => () => { if (preview) URL.revokeObjectURL(preview); }, [preview]);

  async function scanDevices() {
    setScanning(true);
    try {
      const data = await api.discoverDevices();
      setDevices(data);
    } catch {
      setDevices([]);
    }
    setScanning(false);
  }

  async function probeSource() {
    if (!form.source_url) return;
    setProbing(true);
    setProbeError("");
    if (preview) {
      URL.revokeObjectURL(preview);
    }
    setPreview(null);

    try {
      const result = await api.probeSource(form.source_url);
      if (result?.ok && result.url) {
        setPreview(result.url);
        return true;
      }
      setProbeError(result?.error || "Could not connect to this source");
      return false;
    } catch {
      setProbeError("Could not connect to this source");
      return false;
    } finally {
      setProbing(false);
    }
  }

  function handleSubmit(e) {
    e.preventDefault();
    if (!form.name || !form.source_url) return;
    // For manual entries (non-device-index), require successful probe
    const isDeviceIndex = /^\d+$/.test(form.source_url);
    if (!isDeviceIndex && !preview) {
      probeSource().then((ok) => {
        if (ok) onSubmit(form);
      });
      return;
    }
    onSubmit(form);
  }

  function quickAdd(device) {
    onSubmit({ name: device.name, source_url: String(device.index), location: "Local device" });
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60" onClick={onClose}>
      <div
        className="bg-zinc-900 border border-zinc-800 rounded-xl w-[440px] p-5 animate-slide-in"
        onClick={(e) => e.stopPropagation()}
      >
        <h2 className="text-sm font-semibold text-zinc-50 mb-4">Add Camera</h2>

        {/* Discovered devices */}
        <div className="mb-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-[9px] text-zinc-500 uppercase tracking-wider">Detected Devices</span>
            <button onClick={scanDevices} disabled={scanning} className="text-[9px] text-blue-400 hover:text-blue-300 disabled:opacity-40">
              {scanning ? "Scanning..." : "Rescan"}
            </button>
          </div>
          {devices.length > 0 || !scanning ? (
            <div className="space-y-1.5">
              {devices.map((d) => (
                <div key={d.index} className="flex items-center justify-between bg-surface-alt border border-zinc-800 rounded-lg px-3 py-2">
                  <div>
                    <div className="text-[10px] text-zinc-300">{d.name}</div>
                    <div className="text-[9px] text-zinc-600">Index {d.index} &middot; {d.width}x{d.height}</div>
                  </div>
                  <button
                    onClick={() => quickAdd(d)}
                    className="text-[9px] font-semibold text-blue-400 bg-blue-500/10 border border-blue-500/25 rounded px-2 py-1 hover:bg-blue-500/20"
                  >
                    Quick Add
                  </button>
                </div>
              ))}
              {devices.length === 0 && !scanning && (
                <div className="flex items-center justify-between bg-surface-alt border border-zinc-800 rounded-lg px-3 py-2">
                  <div>
                    <div className="text-[10px] pl-1 font-bold text-zinc-300">Local Laptop Camera (Fallback)</div>
                    <div className="text-[9px] pl-1 text-zinc-600">Index 0 &middot; Default Device</div>
                  </div>
                  <button
                    onClick={() => onSubmit({ name: "Local Webcam", source_url: "0", location: "Local Device" })}
                    className="text-[9px] font-bold text-blue-400 bg-blue-500/10 border border-blue-500/25 rounded px-2 py-1 hover:bg-blue-500/20 shadow-lg shadow-blue-500/10"
                  >
                    Quick Add
                  </button>
                </div>
              )}
            </div>
          ) : (
            <div className="text-[10px] text-zinc-700 bg-surface-alt border border-zinc-800 rounded-lg px-3 py-3 text-center">
              Scanning for hardware devices...
            </div>
          )}
        </div>

        <div className="flex items-center gap-2 mb-4">
          <div className="flex-1 h-px bg-zinc-800" />
          <span className="text-[8px] text-zinc-600 uppercase tracking-wider">or add manually</span>
          <div className="flex-1 h-px bg-zinc-800" />
        </div>

        <form onSubmit={handleSubmit} className="space-y-3">
          <FormField
            label="Camera Name"
            placeholder="e.g. Warehouse A — Entry"
            value={form.name}
            onChange={(v) => setForm((f) => ({ ...f, name: v }))}
            required
          />
          <div>
            <label className="text-[9px] text-zinc-500 uppercase tracking-wider block mb-1">Source URL</label>
            <div className="flex gap-2">
              <input
                type="text"
                placeholder="rtsp://192.168.1.100:554/stream or 0 for webcam"
                value={form.source_url}
                onChange={(v) => {
                  setForm((f) => ({ ...f, source_url: v.target.value }));
                  if (preview) {
                    URL.revokeObjectURL(preview);
                  }
                  setPreview(null);
                  setProbeError("");
                }}
                required
                className="flex-1 bg-surface-alt border border-zinc-800 rounded-lg px-3 py-2 text-[11px] text-zinc-300 placeholder-zinc-700 focus:border-blue-500/40 focus:outline-none transition-colors"
              />
              <button
                type="button"
                onClick={probeSource}
                disabled={probing || !form.source_url}
                className="text-[9px] font-semibold text-blue-400 bg-blue-500/10 border border-blue-500/25 rounded-lg px-3 hover:bg-blue-500/20 disabled:opacity-40 transition-colors whitespace-nowrap"
              >
                {probing ? "Testing..." : "Test"}
              </button>
            </div>
          </div>

          {/* Preview / probe result */}
          {(preview || probeError) && (
            <div className={`rounded-lg overflow-hidden border ${probeError ? "border-red-500/30" : "border-green-500/30"}`}>
              {preview ? (
                <img src={preview} alt="Camera preview" className="w-full h-32 object-cover" />
              ) : (
                <div className="flex items-center justify-center h-20 bg-red-500/5">
                  <span className="text-[10px] text-red-400">{probeError}</span>
                </div>
              )}
            </div>
          )}

          <FormField
            label="Location"
            placeholder="e.g. Building B, Floor 2 (optional)"
            value={form.location}
            onChange={(v) => setForm((f) => ({ ...f, location: v }))}
          />
          <div className="flex gap-2 pt-2">
            <button type="button" onClick={onClose} className="flex-1 py-2 rounded-lg border border-zinc-800 text-zinc-500 text-[10px] font-semibold hover:bg-white/[0.02] transition-colors">
              Cancel
            </button>
            <button
              type="submit"
              disabled={probing}
              className="flex-1 py-2 rounded-lg bg-blue-500/15 text-blue-400 border border-blue-500/25 text-[10px] font-semibold hover:bg-blue-500/25 disabled:opacity-40 transition-colors"
            >
              {!/^\d+$/.test(form.source_url) && !preview ? "Test & Add" : "Add Camera"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

function FormField({ label, placeholder, value, onChange, required }) {
  return (
    <div>
      <label className="text-[9px] text-zinc-500 uppercase tracking-wider block mb-1">{label}</label>
      <input
        type="text"
        placeholder={placeholder}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        required={required}
        className="w-full bg-surface-alt border border-zinc-800 rounded-lg px-3 py-2 text-[11px] text-zinc-300 placeholder-zinc-700 focus:border-blue-500/40 focus:outline-none transition-colors"
      />
    </div>
  );
}

function getBadges(alerts, cameraId) {
  const camAlerts = alerts.filter((a) => a.camera === cameraId);
  // Deduplicate by message to keep the video feed neat
  const uniqueAlerts = Array.from(new Map(camAlerts.map(a => [a.message, a])).values());
  
  return uniqueAlerts.map((a) => ({
    variant: a.severity === "high" ? "danger" : a.severity === "medium" ? "warning" : "info",
    label: a.message,
  }));
}

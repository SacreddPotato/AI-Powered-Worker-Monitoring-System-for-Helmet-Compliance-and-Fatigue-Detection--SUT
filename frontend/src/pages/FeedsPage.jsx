import { useState, useEffect } from "react";
import { api } from "../api";
import CameraFeed from "../components/CameraFeed";
import AlertCard from "../components/AlertCard";
import Toggle from "../components/Toggle";

const ALL_MODELS = ["helmet", "fatigue", "vest", "gloves", "goggles"];

export default function FeedsPage() {
  const [cameras, setCameras] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [heroId, setHeroId] = useState(null);
  const [showAdd, setShowAdd] = useState(false);
  const [overlays, setOverlays] = useState([...ALL_MODELS]);
<<<<<<< HEAD
  const [deletingIds, setDeletingIds] = useState([]);
=======
>>>>>>> 8115fdcf9d162b5e5dee45a08428c0476c2fa649

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
<<<<<<< HEAD
    // Duplicate check — reject if source_url already exists
    const existing = cameras.find((c) => c.source_url === form.source_url);
    if (existing) {
      alert(`Camera "${existing.name}" already uses source ${form.source_url}`);
      return;
    }
=======
>>>>>>> 8115fdcf9d162b5e5dee45a08428c0476c2fa649
    await api.createCamera(form);
    setShowAdd(false);
    loadCameras();
  }

  async function handleDeleteCamera(id) {
<<<<<<< HEAD
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
=======
    await api.deleteCamera(id);
    if (heroId === id) setHeroId(null);
    loadCameras();
>>>>>>> 8115fdcf9d162b5e5dee45a08428c0476c2fa649
  }

  function toggleOverlay(key) {
    setOverlays((prev) => (prev.includes(key) ? prev.filter((k) => k !== key) : [...prev, key]));
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
<<<<<<< HEAD
                  isDeleting={deletingIds.includes(hero.id)}
=======
>>>>>>> 8115fdcf9d162b5e5dee45a08428c0476c2fa649
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
<<<<<<< HEAD
                  isDeleting={deletingIds.includes(cam.id)}
=======
>>>>>>> 8115fdcf9d162b5e5dee45a08428c0476c2fa649
                  onDelete={() => handleDeleteCamera(cam.id)}
                />
              ))}
            </div>
          )}
        </div>

        {/* Alert sidebar */}
        <div className="w-[280px] bg-[#0c0c0f] border-l border-zinc-800/60 flex flex-col shrink-0">
          <div className="px-3.5 py-3 border-b border-zinc-800/60 flex justify-between items-center">
            <span className="text-xs font-semibold text-zinc-400">Alerts</span>
            <span className="text-[9px] font-semibold bg-red-500/15 text-red-500 px-2 py-0.5 rounded-full">
              {alerts.length} active
            </span>
          </div>
          <div className="flex-1 overflow-y-auto px-2.5 py-2">
            {["high", "medium", "low"].map(
              (sev) =>
                grouped[sev].length > 0 && (
                  <div key={sev}>
                    <div className="text-[8px] text-zinc-600 uppercase tracking-widest px-1 py-1.5">
                      {sev === "high" ? "Critical" : sev === "medium" ? "Warning" : "Info"}
                    </div>
                    {grouped[sev].map((alert) => (
                      <AlertCard key={alert.id} alert={alert} compact />
                    ))}
                  </div>
                )
            )}
            {alerts.length === 0 && (
              <div className="text-[10px] text-zinc-700 text-center py-8">No active alerts</div>
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
<<<<<<< HEAD
  const [preview, setPreview] = useState(null);       // object URL for preview image
  const [probing, setProbing] = useState(false);
  const [probeError, setProbeError] = useState("");
=======
>>>>>>> 8115fdcf9d162b5e5dee45a08428c0476c2fa649

  useEffect(() => {
    scanDevices();
  }, []);

<<<<<<< HEAD
  // Clean up preview blob URL
  useEffect(() => () => { if (preview) URL.revokeObjectURL(preview); }, [preview]);

=======
>>>>>>> 8115fdcf9d162b5e5dee45a08428c0476c2fa649
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

<<<<<<< HEAD
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
=======
  function handleSubmit(e) {
    e.preventDefault();
    if (!form.name || !form.source_url) return;
>>>>>>> 8115fdcf9d162b5e5dee45a08428c0476c2fa649
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
          {devices.length > 0 ? (
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
            </div>
          ) : (
            <div className="text-[10px] text-zinc-700 bg-surface-alt border border-zinc-800 rounded-lg px-3 py-3 text-center">
              {scanning ? "Scanning for devices..." : "No local video devices found"}
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
<<<<<<< HEAD
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

=======
          <FormField
            label="Source URL"
            placeholder="rtsp://192.168.1.100:554/stream or 0 for webcam"
            value={form.source_url}
            onChange={(v) => setForm((f) => ({ ...f, source_url: v }))}
            required
          />
>>>>>>> 8115fdcf9d162b5e5dee45a08428c0476c2fa649
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
<<<<<<< HEAD
            <button
              type="submit"
              disabled={probing}
              className="flex-1 py-2 rounded-lg bg-blue-500/15 text-blue-400 border border-blue-500/25 text-[10px] font-semibold hover:bg-blue-500/25 disabled:opacity-40 transition-colors"
            >
              {!/^\d+$/.test(form.source_url) && !preview ? "Test & Add" : "Add Camera"}
=======
            <button type="submit" className="flex-1 py-2 rounded-lg bg-blue-500/15 text-blue-400 border border-blue-500/25 text-[10px] font-semibold hover:bg-blue-500/25 transition-colors">
              Add Camera
>>>>>>> 8115fdcf9d162b5e5dee45a08428c0476c2fa649
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
  return alerts
    .filter((a) => a.camera === cameraId)
    .map((a) => ({
      variant: a.severity === "high" ? "danger" : a.severity === "medium" ? "warning" : "info",
      label: a.message,
    }));
}

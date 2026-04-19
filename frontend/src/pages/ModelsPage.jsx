import { useState, useEffect } from "react";
import { api } from "../api";
import Toggle from "../components/Toggle";
import LoadingCircle from "../components/LoadingCircle";

const SEVERITY_LEVELS = ["high", "medium", "low"];

export default function ModelsPage() {
  const [models, setModels] = useState([]);
  const [cameras, setCameras] = useState([]);
  const [overrides, setOverrides] = useState({});
  const [severityMatrix, setSeverityMatrix] = useState({});
  const [globalSeverityDraft, setGlobalSeverityDraft] = useState({});
  const [globalSeverityOpen, setGlobalSeverityOpen] = useState(false);
  const [applyingGlobalSeverity, setApplyingGlobalSeverity] = useState(false);
  const [savingSeverityKey, setSavingSeverityKey] = useState("");
  const [loading, setLoading] = useState(true);
  const [loadMs, setLoadMs] = useState(null);

  useEffect(() => {
    let active = true;
    (async () => {
      setLoading(true);
      const startedAt = performance.now();
      try {
        const [modelsData, camerasData, overridesData, severityData] = await Promise.all([
          api.listModels(),
          api.listCameras(),
          api.listCameraModelsBulk(),
          api.getAlertSeverityMatrix(),
        ]);
        if (!active) return;
        const modelList = modelsData.results || modelsData;
        const cameraList = camerasData.results || camerasData;
        setModels(modelList);
        setCameras(cameraList);
        setOverrides(overridesData || {});
        setSeverityMatrix(severityData?.matrix || {});
        const defaults = severityData?.defaults || {};
        const draft = {};
        modelList.forEach((m) => {
          draft[m.key] = defaults[m.key] || "low";
        });
        setGlobalSeverityDraft(draft);
        setLoadMs(Math.round(performance.now() - startedAt));
      } finally {
        if (active) setLoading(false);
      }
    })();

    return () => {
      active = false;
    };
  }, []);

  async function toggleGlobal(key, current) {
    await api.updateModel(key, { enabled: !current });
    const data = await api.listModels();
    setModels(data.results || data);
  }

  async function toggleCameraModel(camId, modelKey, current, globallyEnabled) {
    if (!globallyEnabled) return;
    await api.updateCameraModel(camId, modelKey, { enabled: !current });
    const ov = await api.listCameraModels(camId);
    setOverrides((prev) => ({ ...prev, [camId]: ov }));
  }

  function getOverride(camId, modelKey) {
    const ovs = overrides[camId] || [];
    const found = ovs.find((o) => o.model_key === modelKey);
    return found ? found.is_enabled : true;
  }

  function getCameraSeverity(camId, modelKey) {
    return severityMatrix?.[camId]?.[modelKey] || globalSeverityDraft?.[modelKey] || "low";
  }

  async function updateCameraSeverity(camId, modelKey, severity) {
    const previous = severityMatrix;
    setSeverityMatrix((prev) => ({
      ...prev,
      [camId]: {
        ...(prev[camId] || {}),
        [modelKey]: severity,
      },
    }));
    setSavingSeverityKey(`${camId}:${modelKey}`);
    try {
      await api.updateCameraAlertSeverity(camId, modelKey, severity);
    } catch {
      setSeverityMatrix(previous);
      alert("Failed to update camera alert severity.");
    } finally {
      setSavingSeverityKey("");
    }
  }

  async function applyGlobalSeverityOverride() {
    if (!Object.keys(globalSeverityDraft).length) return;
    setApplyingGlobalSeverity(true);
    try {
      await api.applyGlobalAlertSeverity(globalSeverityDraft);
      const severityData = await api.getAlertSeverityMatrix();
      setSeverityMatrix(severityData?.matrix || {});
    } catch {
      alert("Failed to apply global severity override.");
    } finally {
      setApplyingGlobalSeverity(false);
    }
  }

  function severityButtonClass(isActive, level) {
    if (!isActive) {
      return "text-zinc-500 hover:text-zinc-300";
    }
    if (level === "high") {
      return "text-red-300 bg-red-500/10";
    }
    if (level === "medium") {
      return "text-amber-300 bg-amber-500/10";
    }
    return "text-emerald-300 bg-emerald-500/10";
  }

  return (
    <>
      <div className="px-5 py-4 flex justify-between items-center border-b border-zinc-800/60 shrink-0">
        <div className="flex items-baseline gap-2">
          <h1 className="text-base font-semibold text-zinc-50">Model Management</h1>
          <span className="text-xs text-zinc-600">
            {loading
              ? "Loading..."
              : `${models.length} models · ${models.filter((m) => m.is_enabled).length} active${loadMs != null ? ` · ${loadMs} ms` : ""}`}
          </span>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto px-5 py-5">
        {loading ? (
          <div className="h-full border border-zinc-800 rounded-xl bg-surface-alt/50">
            <LoadingCircle label="Loading model settings..." />
          </div>
        ) : (
          <>
        <h2 className="text-sm font-semibold text-zinc-50 mb-1">Global Model Settings</h2>
        <p className="text-[10px] text-zinc-600 mb-4">Toggle models on/off globally. Per-camera overrides below.</p>

        <div className="grid grid-cols-[repeat(auto-fill,minmax(220px,1fr))] gap-2.5 mb-8">
          {models.map((model) => (
            <div key={model.key} className="bg-surface-alt border border-zinc-800 rounded-lg p-3.5 hover:border-zinc-700 transition-colors">
              <div className="flex justify-between items-center mb-2.5">
                <span className="text-xs font-semibold text-zinc-100 capitalize">{model.display_name || model.key}</span>
                <span className={`text-[8px] font-semibold px-2 py-0.5 rounded border ${
                  model.is_enabled
                    ? "bg-green-500/10 text-green-400 border-green-500/20"
                    : "bg-zinc-800 text-zinc-500 border-zinc-700"
                }`}>
                  {model.is_enabled ? "Active" : "Disabled"}
                </span>
              </div>
              {model.description && (
                <p className="text-[10px] text-zinc-500 leading-relaxed mb-3">{model.description}</p>
              )}
              <Toggle enabled={model.is_enabled} onChange={() => toggleGlobal(model.key, model.is_enabled)} />
            </div>
          ))}
        </div>

        <h2 className="text-sm font-semibold text-zinc-50 mb-1">Per-Camera Overrides</h2>
        <p className="text-[10px] text-zinc-600 mb-4">Override global settings for individual cameras.</p>

        <div className="overflow-x-auto">
          <table className="w-full border-collapse">
            <thead>
              <tr>
                <th className="text-left text-[9px] text-zinc-600 uppercase tracking-wider px-3 py-2 border-b border-zinc-800">Camera</th>
                {models.map((m) => (
                  <th key={m.key} className="text-center text-[9px] text-zinc-600 uppercase tracking-wider px-3 py-2 border-b border-zinc-800 capitalize">
                    {m.key}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {cameras.map((cam) => (
                <tr key={cam.id}>
                  <td className="px-3 py-2 border-b border-zinc-800/50">
                    <div className="flex items-center gap-2">
                      <span className={`w-1.5 h-1.5 rounded-full ${cam.is_active ? "bg-green-500" : "bg-zinc-600"}`} />
                      <span className="text-[11px] text-zinc-400">{cam.name}</span>
                    </div>
                  </td>
                  {models.map((m) => (
                    <td key={m.key} className="text-center px-3 py-2 border-b border-zinc-800/50">
                      <div className="flex flex-col items-center justify-center gap-1">
                        {(() => {
                          const cameraOverrideEnabled = getOverride(cam.id, m.key);
                          const effectiveEnabled = m.is_enabled && cameraOverrideEnabled;
                          return (
                            <>
                              <Toggle
                                size="sm"
                                enabled={effectiveEnabled}
                                disabled={!m.is_enabled}
                                onChange={() => toggleCameraModel(cam.id, m.key, cameraOverrideEnabled, m.is_enabled)}
                                title={!m.is_enabled ? "Enable this model globally to change camera-level override" : ""}
                              />
                              {!m.is_enabled && (
                                <span className="text-[8px] leading-none text-zinc-500">Locked by global setting</span>
                              )}
                            </>
                          );
                        })()}
                      </div>
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <h2 className="text-sm font-semibold text-zinc-50 mt-9 mb-1">Alert Severity Settings</h2>
        <p className="text-[10px] text-zinc-600 mb-4">
          Edit alert severity per camera/model. The global action applies a one-time overwrite to all camera severities and does not lock per-camera edits.
        </p>

        <div className="max-w-[560px] mb-4">
          <button
            type="button"
            onClick={() => setGlobalSeverityOpen((v) => !v)}
            className="w-full flex items-center justify-between gap-2 bg-surface-alt border border-zinc-800 rounded-lg px-3 py-2 text-left hover:border-zinc-700 transition-colors"
          >
            <span className="text-[10px] text-zinc-300 uppercase tracking-wider">One-time global override</span>
            <span className="flex items-center gap-1 text-[10px] text-zinc-500">
              {globalSeverityOpen ? "Hide" : "Configure"}
              <svg
                viewBox="0 0 16 16"
                className={`w-3 h-3 transition-transform ${globalSeverityOpen ? "rotate-180" : ""}`}
                fill="none"
                stroke="currentColor"
                strokeWidth="1.8"
              >
                <polyline points="3 6 8 11 13 6" />
              </svg>
            </span>
          </button>

          {globalSeverityOpen && (
            <div className="mt-2 bg-surface-alt border border-zinc-800 rounded-lg p-3">
              <div className="max-h-[280px] overflow-y-auto pr-1 space-y-2">
                {models.map((m) => {
                  const selected = globalSeverityDraft[m.key] || "low";
                  return (
                    <div
                      key={`global-${m.key}`}
                      className="flex items-center justify-between gap-2 bg-zinc-900 border border-zinc-800 rounded-lg px-2.5 py-1.5"
                    >
                      <span className="text-[10px] text-zinc-300 whitespace-nowrap">{m.display_name || m.key}</span>
                      <div className="inline-flex rounded-md border border-zinc-800 bg-zinc-950 overflow-hidden">
                        {SEVERITY_LEVELS.map((level) => {
                          const active = selected === level;
                          return (
                            <button
                              key={`${m.key}-${level}`}
                              type="button"
                              onClick={() => setGlobalSeverityDraft((prev) => ({ ...prev, [m.key]: level }))}
                              className={`px-1.5 py-0.5 text-[9px] font-semibold transition-colors ${severityButtonClass(active, level)}`}
                              title={`${m.display_name || m.key}: ${level}`}
                            >
                              {level === "high" ? "H" : level === "medium" ? "M" : "L"}
                            </button>
                          );
                        })}
                      </div>
                    </div>
                  );
                })}
              </div>
              <div className="mt-3 flex justify-end">
                <button
                  onClick={applyGlobalSeverityOverride}
                  disabled={applyingGlobalSeverity}
                  className="px-3 py-1 rounded-lg border text-[10px] font-medium bg-amber-500/10 text-amber-400 border-amber-500/30 hover:bg-amber-500/20 disabled:opacity-40"
                >
                  {applyingGlobalSeverity ? "Applying..." : "Apply to all cameras"}
                </button>
              </div>
            </div>
          )}
        </div>

        <div className="overflow-x-auto">
          <table className="w-full border-collapse">
            <thead>
              <tr>
                <th className="text-left text-[9px] text-zinc-600 uppercase tracking-wider px-3 py-2 border-b border-zinc-800">Camera</th>
                {models.map((m) => (
                  <th key={`sev-${m.key}`} className="text-center text-[9px] text-zinc-600 uppercase tracking-wider px-3 py-2 border-b border-zinc-800 capitalize">
                    {m.key}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {cameras.map((cam) => (
                <tr key={`sev-row-${cam.id}`}>
                  <td className="px-3 py-2 border-b border-zinc-800/50">
                    <span className="text-[11px] text-zinc-400">{cam.name}</span>
                  </td>
                  {models.map((m) => {
                    const cellKey = `${cam.id}:${m.key}`;
                    return (
                      <td key={`sev-cell-${cam.id}-${m.key}`} className="text-center px-3 py-2 border-b border-zinc-800/50">
                        <select
                          value={getCameraSeverity(cam.id, m.key)}
                          onChange={(e) => updateCameraSeverity(cam.id, m.key, e.target.value)}
                          className="bg-zinc-950 border border-zinc-800 rounded-md px-2 py-1 text-[10px] text-zinc-300"
                        >
                          <option value="high">High</option>
                          <option value="medium">Medium</option>
                          <option value="low">Low</option>
                        </select>
                        {savingSeverityKey === cellKey && (
                          <div className="text-[8px] text-zinc-500 mt-1">Saving...</div>
                        )}
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
          </>
        )}
      </div>
    </>
  );
}

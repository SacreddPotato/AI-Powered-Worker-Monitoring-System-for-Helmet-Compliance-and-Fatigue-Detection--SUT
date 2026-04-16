import { useState, useEffect } from "react";
import { api } from "../api";
import Toggle from "../components/Toggle";

export default function ModelsPage() {
  const [models, setModels] = useState([]);
  const [cameras, setCameras] = useState([]);
  const [overrides, setOverrides] = useState({});

  useEffect(() => {
    api.listModels().then((data) => setModels(data.results || data));
    api.listCameras().then((data) => {
      const cams = data.results || data;
      setCameras(cams);
      cams.forEach((cam) => {
        api.listCameraModels(cam.id).then((ov) => {
          setOverrides((prev) => ({ ...prev, [cam.id]: ov }));
        });
      });
    });
  }, []);

  async function toggleGlobal(key, current) {
    await api.updateModel(key, { enabled: !current });
    const data = await api.listModels();
    setModels(data.results || data);
  }

  async function toggleCameraModel(camId, modelKey, current) {
    await api.updateCameraModel(camId, modelKey, { enabled: !current });
    const ov = await api.listCameraModels(camId);
    setOverrides((prev) => ({ ...prev, [camId]: ov }));
  }

  function getOverride(camId, modelKey) {
    const ovs = overrides[camId] || [];
    const found = ovs.find((o) => o.model_key === modelKey);
    return found ? found.is_enabled : true;
  }

  return (
    <>
      <div className="px-5 py-4 flex justify-between items-center border-b border-zinc-800/60 shrink-0">
        <div className="flex items-baseline gap-2">
          <h1 className="text-base font-semibold text-zinc-50">Model Management</h1>
          <span className="text-xs text-zinc-600">
            {models.length} models &middot; {models.filter((m) => m.is_enabled).length} active
          </span>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto px-5 py-5">
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
                      <div className="flex justify-center">
                        <Toggle
                          size="sm"
                          enabled={getOverride(cam.id, m.key)}
                          onChange={() => toggleCameraModel(cam.id, m.key, getOverride(cam.id, m.key))}
                        />
                      </div>
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </>
  );
}

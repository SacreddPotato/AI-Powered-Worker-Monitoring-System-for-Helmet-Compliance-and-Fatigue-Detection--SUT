import { useState, useEffect } from "react";
import { api } from "../api";

const GROUP_MODES = ["severity", "camera", "model", "time"];

export default function AlertsPage() {
  const [alerts, setAlerts] = useState([]);
  const [groupBy, setGroupBy] = useState("severity");
  const [selected, setSelected] = useState(null);

  useEffect(() => {
    loadAlerts();
    const interval = setInterval(loadAlerts, 5000);
    return () => clearInterval(interval);
  }, []);

  function loadAlerts() {
    api.listAlerts({ limit: 200 }).then((data) => setAlerts(data.results || data));
  }

  async function handleAcknowledge(id) {
    await api.acknowledgeAlert(id);
    loadAlerts();
    if (selected?.id === id) setSelected((s) => ({ ...s, status: "acknowledged" }));
  }

  const groups = groupAlerts(alerts, groupBy);
  const detail = selected || alerts[0];

  return (
    <>
      <div className="px-5 py-4 flex justify-between items-center border-b border-zinc-800/60 shrink-0">
        <div className="flex items-baseline gap-2">
          <h1 className="text-base font-semibold text-zinc-50">Alert Center</h1>
          <span className="text-xs text-zinc-600">
            {alerts.filter((a) => a.status === "open").length} active
          </span>
        </div>
        <div className="flex gap-1.5">
          {GROUP_MODES.map((mode) => (
            <button
              key={mode}
              onClick={() => setGroupBy(mode)}
              className={`px-3 py-1.5 rounded-lg border text-[10px] font-medium capitalize transition-colors ${
                groupBy === mode
                  ? "bg-blue-500/10 text-blue-400 border-blue-500/30"
                  : "bg-transparent text-zinc-500 border-zinc-800 hover:text-zinc-400"
              }`}
            >
              {mode}
            </button>
          ))}
        </div>
      </div>

      <div className="flex-1 flex overflow-hidden">
        {/* Alert list */}
        <div className="flex-1 overflow-y-auto px-5 py-4">
          {groups.map(({ label, items, count }) => (
            <div key={label} className="mb-4">
              <div className="flex justify-between items-center text-[9px] text-zinc-600 uppercase tracking-widest pb-1.5 mb-2 border-b border-zinc-800/60">
                <span>{label}</span>
                <span>{count} alerts</span>
              </div>
              {items.map((alert) => (
                <div
                  key={alert.id}
                  onClick={() => setSelected(alert)}
                  className={`grid grid-cols-[6px_1fr_140px_100px_80px] gap-3 items-center px-3 py-2.5 rounded-lg mb-1 cursor-pointer transition-colors ${
                    selected?.id === alert.id ? "bg-white/[0.03]" : "hover:bg-white/[0.02]"
                  }`}
                >
                  <div className={`w-1 h-7 rounded-sm ${sevColor(alert.severity)}`} />
                  <div>
                    <div className="text-[11px] font-medium text-zinc-100">{alert.message}</div>
                    <div className="text-[9px] text-zinc-600 mt-0.5">{alert.model_key} detection</div>
                  </div>
                  <div className="text-[10px] text-zinc-500">{alert.camera_name}</div>
                  <div className="text-[10px] text-zinc-600">{formatTime(alert.created_at)}</div>
                  {alert.status === "open" ? (
                    <button
                      onClick={(e) => { e.stopPropagation(); handleAcknowledge(alert.id); }}
                      className="text-[9px] text-blue-400 bg-blue-500/8 border border-blue-500/20 px-2.5 py-1 rounded-md text-center hover:bg-blue-500/15"
                    >
                      Acknowledge
                    </button>
                  ) : (
                    <span className="text-[9px] text-zinc-600 text-center">Acknowledged</span>
                  )}
                </div>
              ))}
            </div>
          ))}
        </div>

        {/* Detail panel */}
        {detail && (
          <div className="w-80 bg-[#0c0c0f] border-l border-zinc-800/60 p-5 overflow-y-auto shrink-0">
            <h2 className="text-sm font-semibold text-zinc-50 mb-1">{detail.message}</h2>
            <span className={`inline-block text-[9px] font-semibold px-2.5 py-0.5 rounded mb-4 ${sevBadge(detail.severity)}`}>
              {detail.severity.toUpperCase()}
            </span>

            <Field label="Source" value={detail.camera_name} />
            <Field label="Model" value={detail.model_key} />
            <Field label="Status" value={detail.status} />
            <Field label="Timestamp" value={new Date(detail.created_at).toLocaleString()} />

            {detail.payload && Object.keys(detail.payload).length > 0 && (
              <div className="mt-4">
                <div className="text-[9px] text-zinc-600 uppercase tracking-wider mb-1">Payload</div>
                <pre className="bg-surface-alt border border-zinc-800 rounded-lg p-3 text-[10px] text-zinc-500 font-mono overflow-auto max-h-48 whitespace-pre-wrap">
                  {JSON.stringify(detail.payload, null, 2)}
                </pre>
              </div>
            )}

            {detail.status === "open" && (
              <div className="flex gap-2 mt-5">
                <button
                  onClick={() => handleAcknowledge(detail.id)}
                  className="flex-1 py-2 rounded-lg bg-blue-500/15 text-blue-400 text-[10px] font-semibold hover:bg-blue-500/25 transition-colors"
                >
                  Acknowledge
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </>
  );
}

function Field({ label, value }) {
  return (
    <div className="mb-3">
      <div className="text-[9px] text-zinc-600 uppercase tracking-wider mb-0.5">{label}</div>
      <div className="text-xs text-zinc-400">{value}</div>
    </div>
  );
}

function sevColor(sev) {
  return { high: "bg-red-500", medium: "bg-amber-500", low: "bg-blue-500" }[sev] || "bg-zinc-600";
}
function sevBadge(sev) {
  return { high: "bg-red-500/15 text-red-400", medium: "bg-amber-500/12 text-amber-400", low: "bg-blue-500/10 text-blue-400" }[sev] || "";
}
function formatTime(iso) {
  if (!iso) return "";
  const diff = (Date.now() - new Date(iso)) / 1000;
  if (diff < 60) return `${Math.round(diff)}s ago`;
  if (diff < 3600) return `${Math.round(diff / 60)}m ago`;
  return `${Math.round(diff / 3600)}h ago`;
}

function groupAlerts(alerts, mode) {
  const map = {};
  alerts.forEach((a) => {
    let key;
    if (mode === "severity") key = a.severity;
    else if (mode === "camera") key = a.camera_name || `Camera ${a.camera}`;
    else if (mode === "model") key = a.model_key;
    else {
      const diff = (Date.now() - new Date(a.created_at)) / 1000;
      if (diff < 60) key = "Last minute";
      else if (diff < 300) key = "Last 5 minutes";
      else if (diff < 3600) key = "Last hour";
      else key = "Older";
    }
    if (!map[key]) map[key] = [];
    map[key].push(a);
  });
  return Object.entries(map).map(([label, items]) => ({ label, items, count: items.length }));
}

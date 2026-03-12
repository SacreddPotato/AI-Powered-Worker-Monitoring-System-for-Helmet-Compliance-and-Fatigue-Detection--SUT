import { useState, useEffect } from "react";
import { api } from "../api";
import CameraFeed from "../components/CameraFeed";
import AlertCard from "../components/AlertCard";

export default function FeedsPage() {
  const [cameras, setCameras] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [heroId, setHeroId] = useState(null);

  useEffect(() => {
    api.listCameras().then((data) => {
      const list = data.results || data;
      setCameras(list);
      if (list.length > 0 && !heroId) setHeroId(list[0].id);
    });
    api.listAlerts({ status: "open", limit: 20 }).then((data) => {
      setAlerts(data.results || data);
    });
    const interval = setInterval(() => {
      api.listAlerts({ status: "open", limit: 20 }).then((data) => setAlerts(data.results || data));
    }, 5000);
    return () => clearInterval(interval);
  }, []);

  const hero = cameras.find((c) => c.id === heroId);
  const others = cameras.filter((c) => c.id !== heroId);

  // Group alerts by severity
  const grouped = { high: [], medium: [], low: [] };
  alerts.forEach((a) => (grouped[a.severity] || grouped.low).push(a));

  return (
    <>
      <div className="px-5 py-4 flex justify-between items-center border-b border-zinc-800/60 shrink-0">
        <div className="flex items-baseline gap-2">
          <h1 className="text-base font-semibold text-zinc-50">Live Feeds</h1>
          <span className="text-xs text-zinc-600">{cameras.length} cameras</span>
        </div>
        <div className="flex items-center gap-1.5 text-[10px] text-zinc-500 bg-zinc-900 border border-zinc-800 rounded-full px-3 py-1">
          <span className="w-1.5 h-1.5 bg-green-500 rounded-full shadow-[0_0_6px_rgba(34,197,94,.5)]" />
          All systems online
        </div>
      </div>

      <div className="flex-1 flex overflow-hidden">
        {/* Camera grid */}
        <div className="flex-1 p-3 overflow-auto">
          <div className="grid grid-cols-2 gap-2 h-full" style={{ gridTemplateRows: "1.6fr 1fr" }}>
            {hero && (
              <CameraFeed camera={hero} isHero badges={getBadges(alerts, hero.id)} />
            )}
            {others.slice(0, 2).map((cam) => (
              <CameraFeed
                key={cam.id}
                camera={cam}
                onClick={() => setHeroId(cam.id)}
                badges={getBadges(alerts, cam.id)}
              />
            ))}
          </div>
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
          </div>
        </div>
      </div>
    </>
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

import { useState, useEffect, useCallback } from "react";
import { Routes, Route } from "react-router-dom";
import IconRail from "./components/IconRail";
import Toast from "./components/Toast";
import { createAlertSocket } from "./ws";
import { api } from "./api";
import FeedsPage from "./pages/FeedsPage";

// Lazy page placeholders (will be built in Tasks 11-13)
function AlertsPage() {
  return <div className="flex-1 flex items-center justify-center text-zinc-600">Alerts — coming next</div>;
}
function ModelsPage() {
  return <div className="flex-1 flex items-center justify-center text-zinc-600">Models — coming next</div>;
}
function DevLabPage() {
  return <div className="flex-1 flex items-center justify-center text-zinc-600">Dev Lab — coming next</div>;
}

export default function App() {
  const [toasts, setToasts] = useState([]);
  const [alertCount, setAlertCount] = useState(0);

  // Fetch initial alert count
  useEffect(() => {
    api.listAlerts({ status: "open", limit: 1 }).then((data) => {
      setAlertCount(data.count ?? data.results?.length ?? 0);
    }).catch(() => {});
  }, []);

  // WebSocket connection
  useEffect(() => {
    const socket = createAlertSocket((msg) => {
      if (msg.type === "alert.new") {
        setToasts((prev) => [...prev.slice(-4), msg.alert]);
        setAlertCount((c) => c + 1);
      }
      if (msg.type === "alert.acknowledged") {
        setAlertCount((c) => Math.max(0, c - 1));
      }
    });
    return () => socket.close();
  }, []);

  const dismissToast = useCallback((id) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  return (
    <div className="h-screen flex overflow-hidden">
      <IconRail alertCount={alertCount} />
      <main className="flex-1 flex flex-col overflow-hidden">
        <Routes>
          <Route path="/" element={<FeedsPage />} />
          <Route path="/alerts" element={<AlertsPage />} />
          <Route path="/models" element={<ModelsPage />} />
          <Route path="/devlab" element={<DevLabPage />} />
        </Routes>
      </main>
      <Toast alerts={toasts} onDismiss={dismissToast} />
    </div>
  );
}

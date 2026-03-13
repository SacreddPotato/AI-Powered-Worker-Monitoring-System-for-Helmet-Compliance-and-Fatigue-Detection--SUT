import { useState, useEffect, useCallback } from "react";
import { Outlet } from "react-router-dom";
import IconRail from "../components/IconRail";
import Toast from "../components/Toast";
import { createAlertSocket } from "../ws";
import { api } from "../api";

export default function DashboardLayout() {
  const [toasts, setToasts] = useState([]);
  const [alertCount, setAlertCount] = useState(0);

  useEffect(() => {
    api.listAlerts({ status: "open", limit: 1 }).then((data) => {
      setAlertCount(data.count ?? data.results?.length ?? 0);
    }).catch(() => {});
  }, []);

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
        <Outlet />
      </main>
      <Toast alerts={toasts} onDismiss={dismissToast} />
    </div>
  );
}

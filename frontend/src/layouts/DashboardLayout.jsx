import { useState, useEffect, useCallback } from "react";
import { Outlet, useLocation } from "react-router-dom";
import IconRail from "../components/IconRail";
import Toast from "../components/Toast";
import LoadingCircle from "../components/LoadingCircle";
import { createAlertSocket } from "../ws";
import { api } from "../api";

const ROUTE_LOADING_MIN_MS = 420;

export default function DashboardLayout() {
  const [toasts, setToasts] = useState([]);
  const [alertCount, setAlertCount] = useState(0);
  const [routeLoading, setRouteLoading] = useState(false);
  const [pendingPath, setPendingPath] = useState(null);
  const location = useLocation();

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

  const handleNavigateStart = useCallback((nextPath) => {
    if (!nextPath || nextPath === location.pathname) return;
    setPendingPath(nextPath);
    setRouteLoading(true);
  }, [location.pathname]);

  useEffect(() => {
    if (!routeLoading || !pendingPath || location.pathname !== pendingPath) return;
    const t = setTimeout(() => {
      setRouteLoading(false);
      setPendingPath(null);
    }, ROUTE_LOADING_MIN_MS);
    return () => clearTimeout(t);
  }, [routeLoading, pendingPath, location.pathname]);

  return (
    <div className="h-screen flex overflow-hidden">
      <IconRail alertCount={alertCount} currentPath={location.pathname} onNavigateStart={handleNavigateStart} />
      <main className="flex-1 flex flex-col overflow-hidden relative">
        <Outlet />
        {routeLoading && (
          <div className="absolute inset-0 bg-[#09090b]/65 backdrop-blur-[1px] z-40">
            <LoadingCircle label="Switching view..." />
          </div>
        )}
      </main>
      <Toast alerts={toasts} onDismiss={dismissToast} />
    </div>
  );
}

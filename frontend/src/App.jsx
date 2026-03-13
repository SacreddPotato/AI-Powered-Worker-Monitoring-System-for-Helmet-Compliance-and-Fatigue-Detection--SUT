import { Routes, Route, Navigate } from "react-router-dom";
import DashboardLayout from "./layouts/DashboardLayout";
import LandingPage from "./pages/LandingPage";
import FeedsPage from "./pages/FeedsPage";
import AlertsPage from "./pages/AlertsPage";
import ModelsPage from "./pages/ModelsPage";
import DevLabPage from "./pages/DevLabPage";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route element={<DashboardLayout />}>
        <Route path="/feeds" element={<FeedsPage />} />
        <Route path="/alerts" element={<AlertsPage />} />
        <Route path="/models" element={<ModelsPage />} />
        <Route path="/devlab" element={<DevLabPage />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

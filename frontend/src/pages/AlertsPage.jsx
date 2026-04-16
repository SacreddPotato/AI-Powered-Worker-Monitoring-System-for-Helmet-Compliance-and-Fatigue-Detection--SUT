import { useState, useEffect } from "react";
import { api } from "../api";

const GROUP_MODES = ["severity", "camera", "model", "time"];
<<<<<<< HEAD
const DATE_RANGE_MODES = ["today", "week", "month", "custom"];
const CUSTOM_DATE_PRESETS = [
  { label: "Last 24h", daysBack: 1 },
  { label: "Last 3 days", daysBack: 2 },
  { label: "Last 7 days", daysBack: 6 },
];
const CALENDAR_PRESETS = [
  { label: "This week", mode: "weekStart" },
  { label: "This month", mode: "monthStart" },
];
const CHART_COLORS = ["#ef4444", "#f59e0b", "#3b82f6", "#22c55e", "#06b6d4", "#71717a", "#a1a1aa"];
=======
>>>>>>> 8115fdcf9d162b5e5dee45a08428c0476c2fa649

export default function AlertsPage() {
  const [alerts, setAlerts] = useState([]);
  const [groupBy, setGroupBy] = useState("severity");
<<<<<<< HEAD
  const [dateRange, setDateRange] = useState("today");
  const [customStart, setCustomStart] = useState("");
  const [customEnd, setCustomEnd] = useState("");
  const [selected, setSelected] = useState(null);
  const [chartData, setChartData] = useState({ labels: [], values: [], total: 0 });
  const [chartLoading, setChartLoading] = useState(false);
  const [excelExporting, setExcelExporting] = useState(false);
  const [chartExporting, setChartExporting] = useState(false);
=======
  const [selected, setSelected] = useState(null);
>>>>>>> 8115fdcf9d162b5e5dee45a08428c0476c2fa649

  useEffect(() => {
    loadAlerts();
    const interval = setInterval(loadAlerts, 5000);
    return () => clearInterval(interval);
<<<<<<< HEAD
  }, [dateRange, customStart, customEnd]);

  useEffect(() => {
    loadChart(groupBy);
  }, [groupBy, dateRange, customStart, customEnd]);

  function buildDateParams() {
    if (dateRange !== "custom") {
      return { date_range: dateRange };
    }
    if (!customStart || !customEnd) {
      return null;
    }
    return { date_range: "custom", start: customStart, end: customEnd };
  }

  function applyCustomPreset(daysBack) {
    const end = new Date();
    const start = new Date();
    start.setDate(end.getDate() - daysBack);
    setDateRange("custom");
    setCustomStart(toDateInputValue(start));
    setCustomEnd(toDateInputValue(end));
  }

  function applyCalendarPreset(mode) {
    const end = new Date();
    let start = new Date();

    if (mode === "weekStart") {
      const day = end.getDay();
      const offsetFromMonday = (day + 6) % 7;
      start.setDate(end.getDate() - offsetFromMonday);
    } else if (mode === "monthStart") {
      start = new Date(end.getFullYear(), end.getMonth(), 1);
    }

    setDateRange("custom");
    setCustomStart(toDateInputValue(start));
    setCustomEnd(toDateInputValue(end));
  }

  function loadAlerts() {
    const dateParams = buildDateParams();
    if (!dateParams) {
      setAlerts([]);
      return;
    }
    api.listAlerts({ limit: 500, ...dateParams }).then((data) => {
      const list = data.results || data;
      setAlerts(list);
      if (selected && !list.some((a) => a.id === selected.id)) {
        setSelected(null);
      }
    });
  }

  async function loadChart(mode) {
    setChartLoading(true);
    const dateParams = buildDateParams();
    if (!dateParams) {
      setChartData({ labels: [], values: [], total: 0 });
      setChartLoading(false);
      return;
    }
    try {
      const data = await api.getAlertsChartData(mode, dateParams);
      setChartData({
        labels: data?.labels || [],
        values: data?.values || [],
        total: data?.total || 0,
      });
    } catch {
      setChartData({ labels: [], values: [], total: 0 });
    } finally {
      setChartLoading(false);
    }
=======
  }, []);

  function loadAlerts() {
    api.listAlerts({ limit: 200 }).then((data) => setAlerts(data.results || data));
>>>>>>> 8115fdcf9d162b5e5dee45a08428c0476c2fa649
  }

  async function handleAcknowledge(id) {
    await api.acknowledgeAlert(id);
    loadAlerts();
<<<<<<< HEAD
    loadChart(groupBy);
    if (selected?.id === id) setSelected((s) => ({ ...s, status: "acknowledged" }));
  }

  async function handleExportExcel() {
    const dateParams = buildDateParams();
    if (!dateParams) return;

    setExcelExporting(true);
    try {
      const { blob, filename } = await api.exportAlertsExcel(dateParams);
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = filename;
      document.body.appendChild(anchor);
      anchor.click();
      anchor.remove();
      URL.revokeObjectURL(url);
    } finally {
      setExcelExporting(false);
    }
  }

  function handleExportChart() {
    const dateParams = buildDateParams();
    if (!dateParams) return;

    setChartExporting(true);
    try {
      const rangeLabel = getDateRangeLabel(dateRange, customStart, customEnd);
      const svg = buildPieSvgMarkup(chartData.labels, chartData.values, `Alerts grouped by ${groupBy} (${rangeLabel})`);
      const blob = new Blob([svg], { type: "image/svg+xml;charset=utf-8" });
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = `alerts_${groupBy}_chart.svg`;
      document.body.appendChild(anchor);
      anchor.click();
      anchor.remove();
      URL.revokeObjectURL(url);
    } finally {
      setChartExporting(false);
    }
  }

=======
    if (selected?.id === id) setSelected((s) => ({ ...s, status: "acknowledged" }));
  }

>>>>>>> 8115fdcf9d162b5e5dee45a08428c0476c2fa649
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
<<<<<<< HEAD
          <select
            value={dateRange}
            onChange={(e) => setDateRange(e.target.value)}
            className="px-2.5 py-1.5 rounded-lg border border-zinc-800 bg-zinc-950 text-zinc-300 text-[10px] font-medium capitalize"
          >
            {DATE_RANGE_MODES.map((mode) => (
              <option key={mode} value={mode}>{mode}</option>
            ))}
          </select>
          <button
            onClick={handleExportExcel}
            disabled={excelExporting || (dateRange === "custom" && (!customStart || !customEnd))}
            className="px-3 py-1.5 rounded-lg border text-[10px] font-medium bg-green-500/10 text-green-400 border-green-500/30 hover:bg-green-500/20 disabled:opacity-40"
          >
            {excelExporting ? "Exporting..." : "Export Excel"}
          </button>
          <button
            onClick={handleExportChart}
            disabled={chartExporting || chartData.total === 0 || (dateRange === "custom" && (!customStart || !customEnd))}
            className="px-3 py-1.5 rounded-lg border text-[10px] font-medium bg-blue-500/10 text-blue-400 border-blue-500/30 hover:bg-blue-500/20 disabled:opacity-40"
          >
            {chartExporting ? "Exporting..." : "Export Chart"}
          </button>
        </div>
      </div>

      {dateRange === "custom" && (
        <div className="px-5 py-2 border-b border-zinc-800/60 flex items-center gap-2 shrink-0">
          <span className="text-[10px] text-zinc-500">Custom Range</span>
          <div className="flex items-center gap-1">
            {CUSTOM_DATE_PRESETS.map((preset) => (
              <button
                key={preset.label}
                type="button"
                onClick={() => applyCustomPreset(preset.daysBack)}
                className="px-2 py-1 rounded-md border border-zinc-800 text-[9px] text-zinc-400 hover:text-zinc-200 hover:border-zinc-700"
              >
                {preset.label}
              </button>
            ))}
            <span className="mx-1 text-[9px] text-zinc-700">|</span>
            {CALENDAR_PRESETS.map((preset) => (
              <button
                key={preset.label}
                type="button"
                onClick={() => applyCalendarPreset(preset.mode)}
                className="px-2 py-1 rounded-md border border-zinc-800 text-[9px] text-zinc-400 hover:text-zinc-200 hover:border-zinc-700"
              >
                {preset.label}
              </button>
            ))}
          </div>
          <input
            type="date"
            value={customStart}
            onChange={(e) => setCustomStart(e.target.value)}
            className="bg-zinc-950 border border-zinc-800 rounded-md px-2 py-1 text-[10px] text-zinc-300"
          />
          <span className="text-[10px] text-zinc-600">to</span>
          <input
            type="date"
            value={customEnd}
            onChange={(e) => setCustomEnd(e.target.value)}
            className="bg-zinc-950 border border-zinc-800 rounded-md px-2 py-1 text-[10px] text-zinc-300"
          />
          {(!customStart || !customEnd) && (
            <span className="text-[10px] text-amber-500">Select start and end dates</span>
          )}
        </div>
      )}

      <div className="flex-1 flex overflow-hidden">
        {/* Alert list */}
        <div className="flex-1 overflow-y-auto px-5 py-4">
          <div className="mb-4 bg-surface-alt border border-zinc-800 rounded-lg p-3.5">
            <div className="flex items-center justify-between mb-3">
              <div>
                <div className="text-[11px] font-semibold text-zinc-200 capitalize">Alert Distribution ({groupBy})</div>
                <div className="text-[9px] text-zinc-600">{chartData.total} total alerts · {getDateRangeLabel(dateRange, customStart, customEnd)}</div>
              </div>
            </div>
            {chartLoading ? (
              <div className="text-[10px] text-zinc-600">Loading chart...</div>
            ) : chartData.total === 0 ? (
              <div className="text-[10px] text-zinc-600">No alerts to visualize yet.</div>
            ) : (
              <div className="flex items-center gap-6">
                <PieChart labels={chartData.labels} values={chartData.values} />
                <div className="grid gap-1.5 text-[10px] text-zinc-400">
                  {chartData.labels.map((label, index) => (
                    <div key={label + index} className="flex items-center gap-2">
                      <span className="w-2.5 h-2.5 rounded-sm" style={{ backgroundColor: CHART_COLORS[index % CHART_COLORS.length] }} />
                      <span className="capitalize">{label}</span>
                      <span className="text-zinc-600">({chartData.values[index] || 0})</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

=======
        </div>
      </div>

      <div className="flex-1 flex overflow-hidden">
        {/* Alert list */}
        <div className="flex-1 overflow-y-auto px-5 py-4">
>>>>>>> 8115fdcf9d162b5e5dee45a08428c0476c2fa649
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

<<<<<<< HEAD
function PieChart({ labels, values }) {
  const total = values.reduce((sum, value) => sum + value, 0);
  if (!total) {
    return <div className="text-[10px] text-zinc-600">No data</div>;
  }

  let start = 0;
  const r = 58;
  const c = 72;
  const paths = values.map((value, index) => {
    const angle = (value / total) * 360;
    const end = start + angle;
    const path = describeSlice(c, c, r, start, end);
    start = end;
    return (
      <path
        key={`${labels[index]}-${index}`}
        d={path}
        fill={CHART_COLORS[index % CHART_COLORS.length]}
        stroke="#111113"
        strokeWidth="1"
      />
    );
  });

  return (
    <svg viewBox="0 0 144 144" className="w-36 h-36 shrink-0">
      {paths}
      <circle cx="72" cy="72" r="32" fill="#111113" />
      <text x="72" y="68" textAnchor="middle" className="fill-zinc-300 text-[10px] font-semibold">Total</text>
      <text x="72" y="84" textAnchor="middle" className="fill-zinc-100 text-[12px] font-semibold">{total}</text>
    </svg>
  );
}

function describeSlice(cx, cy, radius, startAngle, endAngle) {
  const sweep = endAngle - startAngle;
  if (sweep <= 0) return "";
  if (sweep >= 359.999) {
    return [
      "M", cx - radius, cy,
      "A", radius, radius, 0, 1, 0, cx + radius, cy,
      "A", radius, radius, 0, 1, 0, cx - radius, cy,
      "Z",
    ].join(" ");
  }

  const start = polarToCartesian(cx, cy, radius, endAngle);
  const end = polarToCartesian(cx, cy, radius, startAngle);
  const largeArc = sweep <= 180 ? "0" : "1";
  return [
    "M", cx, cy,
    "L", start.x, start.y,
    "A", radius, radius, 0, largeArc, 0, end.x, end.y,
    "Z",
  ].join(" ");
}

function polarToCartesian(cx, cy, radius, angleInDegrees) {
  const angleInRadians = ((angleInDegrees - 90) * Math.PI) / 180.0;
  return {
    x: cx + radius * Math.cos(angleInRadians),
    y: cy + radius * Math.sin(angleInRadians),
  };
}

function buildPieSvgMarkup(labels, values, title) {
  const total = values.reduce((sum, value) => sum + value, 0);
  const center = 220;
  const radius = 160;
  const inner = 90;
  let start = 0;

  const slices = values.map((value, index) => {
    const angle = total > 0 ? (value / total) * 360 : 0;
    const end = start + angle;
    const path = describeSlice(center, center, radius, start, end);
    start = end;
    return `<path d="${path}" fill="${CHART_COLORS[index % CHART_COLORS.length]}" stroke="#111113" stroke-width="2" />`;
  }).join("\n");

  const legend = labels.map((label, index) => {
    const y = 80 + index * 28;
    return `<rect x="460" y="${y}" width="14" height="14" fill="${CHART_COLORS[index % CHART_COLORS.length]}" />\n` +
      `<text x="482" y="${y + 12}" fill="#d4d4d8" font-size="13">${escapeXml(label)} (${values[index] || 0})</text>`;
  }).join("\n");

  return `<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="760" height="500" viewBox="0 0 760 500">
  <rect width="760" height="500" fill="#09090b" />
  <text x="40" y="40" fill="#f4f4f5" font-size="20" font-family="Arial, sans-serif">${escapeXml(title)}</text>
  ${slices}
  <circle cx="${center}" cy="${center}" r="${inner}" fill="#111113" />
  <text x="${center}" y="${center - 8}" text-anchor="middle" fill="#a1a1aa" font-size="12" font-family="Arial, sans-serif">Total</text>
  <text x="${center}" y="${center + 16}" text-anchor="middle" fill="#f4f4f5" font-size="24" font-family="Arial, sans-serif">${total}</text>
  ${legend}
</svg>`;
}

function escapeXml(input) {
  return String(input)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/\"/g, "&quot;")
    .replace(/'/g, "&apos;");
}

=======
>>>>>>> 8115fdcf9d162b5e5dee45a08428c0476c2fa649
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
<<<<<<< HEAD

function getDateRangeLabel(mode, start, end) {
  if (mode === "custom") {
    if (!start || !end) return "Custom (incomplete)";
    return `Custom ${start} → ${end}`;
  }
  if (mode === "today") return "Today";
  if (mode === "week") return "Last 7 days";
  if (mode === "month") return "Last 30 days";
  return mode;
}

function toDateInputValue(dateValue) {
  const year = dateValue.getFullYear();
  const month = String(dateValue.getMonth() + 1).padStart(2, "0");
  const day = String(dateValue.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}
=======
>>>>>>> 8115fdcf9d162b5e5dee45a08428c0476c2fa649

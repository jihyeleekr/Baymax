import React, { useEffect, useState, useRef, useMemo } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  ResponsiveContainer,
  BarChart,
  Bar,
} from "recharts";
import { supabase } from "../SupabaseClient"; 
import "./Graph.css";

// Base URL for the backend API
const API_BASE = process.env.REACT_APP_API_BASE_URL || "http://127.0.0.1:5001";

// Category options for the filter UI
const CATEGORY_OPTIONS = [
  { id: "sleep", label: "Sleep" },
  { id: "vital", label: "Heart rate" },
  { id: "mood", label: "Mood" },
  { id: "medication", label: "Medication" },
];

// X-axis resolution options
const RESOLUTION_OPTIONS = [
  { id: "daily", label: "Daily" },
  { id: "weekly", label: "Weekly" },
  { id: "monthly", label: "Monthly" },
  { id: "yearly", label: "Yearly" },
];

// Aggregate raw daily data into weekly / monthly / yearly buckets
function aggregateData(items, resolution) {
  if (!items || items.length === 0) return [];

  // Sort by date ascending
  const sorted = [...items].sort(
    (a, b) => a.fullDate.getTime() - b.fullDate.getTime()
  );

  // Daily mode: just format dateLabel and return
  if (resolution === "daily") {
    return sorted.map((item) => ({
      ...item,
      dateLabel: item.fullDate.toLocaleDateString("en-US", {
        month: "2-digit",
        day: "2-digit",
      }),
    }));
  }

  const metricKeys = ["sleep", "vital", "mood", "medicNumeric"];
  const groups = new Map();

  sorted.forEach((item) => {
    const d = item.fullDate;
    if (!(d instanceof Date) || isNaN(d)) return;

    let bucketKey = "";
    let bucketDate = null;

    if (resolution === "weekly") {
      // Use Sunday as the start of the week
      const weekStart = new Date(d);
      weekStart.setHours(0, 0, 0, 0);
      const day = weekStart.getDay(); // 0 = Sunday
      weekStart.setDate(weekStart.getDate() - day);
      bucketKey = `week-${weekStart.toISOString().slice(0, 10)}`;
      bucketDate = weekStart;
    } else if (resolution === "monthly") {
      bucketKey = `month-${d.getFullYear()}-${d.getMonth()}`;
      bucketDate = new Date(d.getFullYear(), d.getMonth(), 1);
    } else if (resolution === "yearly") {
      bucketKey = `year-${d.getFullYear()}`;
      bucketDate = new Date(d.getFullYear(), 0, 1);
    }

    if (!groups.has(bucketKey)) {
      const sums = {};
      const counts = {};
      metricKeys.forEach((k) => {
        sums[k] = 0;
        counts[k] = 0;
      });

      groups.set(bucketKey, {
        dateForLabel: bucketDate,
        sums,
        counts,
      });
    }

    const bucket = groups.get(bucketKey);
    metricKeys.forEach((key) => {
      const v = item[key];
      if (typeof v === "number" && !Number.isNaN(v)) {
        bucket.sums[key] += v;
        bucket.counts[key] += 1;
      }
    });
  });

  // Build aggregated list
  const result = Array.from(groups.values())
    .sort((a, b) => a.dateForLabel - b.dateForLabel)
    .map((group) => {
      const { sums, counts, dateForLabel } = group;
      const point = {};

      // Average each numeric metric
      metricKeys.forEach((key) => {
        const c = counts[key];
        point[key] = c > 0 ? sums[key] / c : null;
      });

      // Build label for X axis
      let dateLabel = "";
      const d = dateForLabel;

      if (resolution === "weekly") {
        const end = new Date(d);
        end.setDate(d.getDate() + 6);
        dateLabel = `${d.toLocaleDateString("en-US", {
          month: "2-digit",
          day: "2-digit",
        })}–${end.toLocaleDateString("en-US", {
          month: "2-digit",
          day: "2-digit",
        })}`;
      } else if (resolution === "monthly") {
        dateLabel = d.toLocaleDateString("en-US", {
          month: "short",
          year: "numeric",
        });
      } else if (resolution === "yearly") {
        dateLabel = String(d.getFullYear());
      }

      return {
        ...point,
        dateLabel,
      };
    });

  return result;
}

function Graph() {
  const today = new Date();
  const thirtyDaysAgo = new Date();
  thirtyDaysAgo.setDate(today.getDate() - 30);
  const [userId, setUserId] = useState(null);

  // ✅ UPDATE: Get user on mount (allow anonymous)
useEffect(() => {
  supabase.auth.getUser().then(({ data: { user } }) => {
    setUserId(user?.id || "anonymous");  // ✅ Changed: default to "anonymous"
  });
}, []);

  // Date values from <input type="date"> (YYYY-MM-DD)
  const [startDate, setStartDate] = useState(
    thirtyDaysAgo.toISOString().slice(0, 10)
  );
  const [endDate, setEndDate] = useState(today.toISOString().slice(0, 10));

  // Raw daily data from backend (includes fullDate for aggregation)
  const [rawData, setRawData] = useState([]);

  // Status flags
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // Which categories are currently visible (default: only Sleep)
  const [selectedCategories, setSelectedCategories] = useState(["sleep"]);

  // X-axis resolution (default: Daily)
  const [resolution, setResolution] = useState("daily");

  const startInputRef = useRef(null);
  const endInputRef = useRef(null);

  // ✅ ADD: Get user on mount (same pattern as chatbot)
  useEffect(() => {
    supabase.auth.getUser().then(({ data: { user } }) => {
      setUserId(user?.id);
    });
  }, []);

  // Helper to open the native date picker
  const openPicker = (el) => {
    if (!el) return;
    if (typeof el.showPicker === "function") {
      el.showPicker();
    } else {
      el.focus();
    }
  };

  // Front-end validation: "From" must be <= "To"
  const isRangeInvalid = startDate && endDate && startDate > endDate;

  // Toggle a category on/off (but keep at least one selected)
  const handleToggleCategory = (id) => {
    setSelectedCategories((prev) => {
      const isActive = prev.includes(id);

      // Prevent turning off the last active category
      if (isActive && prev.length === 1) {
        return prev;
      }

      if (isActive) {
        return prev.filter((c) => c !== id);
      }

      return [...prev, id];
    });
  };

  // Aggregated data based on the selected resolution
  const aggregatedData = useMemo(
    () => aggregateData(rawData, resolution),
    [rawData, resolution]
  );

  // Tooltip
  const tooltipFormatter = (value) => {
    if (value == null) return value;
    if (resolution === "daily") return value;
    // weekly / monthly / yearly 일 때만 반올림
    return Number(value.toFixed(2));
  };

  
  useEffect(() => {
    const fetchData = async () => {
     

      if (isRangeInvalid) {
        setRawData([]);
        setError("");
        setLoading(false);
        return;
      }

      try {
        setLoading(true);
        setError("");

         // ✅ ADD user_id to query params (will be "anonymous" if not logged in)
      const params = new URLSearchParams();
      if (userId) params.append("user_id", userId);  // ✅ Only add if userId exists
      if (startDate) params.append("start", startDate);
      if (endDate) params.append("end", endDate);

      const url = `${API_BASE}/api/health-logs?${params.toString()}`;
      const res = await fetch(url);

        if (!res.ok) {
          setRawData([]);
          throw new Error(`Failed to load logs (status ${res.status})`);
        }

        const raw = await res.json();

        // Handle both array and { data: [...] } shapes
        const items = Array.isArray(raw) ? raw : raw.data || [];

        // Normalize fields and keep a real Date object for each record
        const formatted = items.map((item) => {
          // item.date is "MM-DD-YYYY" from MongoDB
          const [mm, dd, yyyy] = item.date.split("-");
          const fullDate = new Date(Number(yyyy), Number(mm) - 1, Number(dd));
          fullDate.setHours(0, 0, 0, 0);

          return {
            fullDate,
            // dateLabel is only used directly in "daily" mode
            dateLabel: fullDate.toLocaleDateString("en-US", {
              month: "2-digit",
              day: "2-digit",
            }),
            // Normalized numeric fields for charts
            sleep:
              typeof item.sleepHours === "number"
                ? item.sleepHours
                : null,
            vital:
              typeof item.vital_bpm === "number" ? item.vital_bpm : null,
            mood: typeof item.mood === "number" ? item.mood : null,
            medicNumeric:
              item.tookMedication === true
                ? 1
                : item.tookMedication === false
                  ? 0
                  : null,
          };
        });

        setRawData(formatted);
      } catch (err) {
        console.error(err);
        setError("An error occurred while loading data.");
        setRawData([]);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [userId, startDate, endDate, isRangeInvalid]); 

  const hasData = aggregatedData.length > 0;

  return (
    <div className="graph-page">
      {/* ---------- HEADER ---------- */}
      <div className="graph-header-row">
        <div>
          <h1 className="graph-title">Health Trends</h1>
          <p className="graph-subtitle">
            See how your sleep, medication, mood, and heart rate
            change over the selected date range.
          </p>
        </div>

        {/* Date range picker */}
        <div className="date-range">
          <label className="date-label">
            From
            <div className="date-input-wrapper">
              <input
                ref={startInputRef}
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
              />
              <span
                className="calendar-icon"
                onClick={() => openPicker(startInputRef.current)}
              >
                calendar_month
              </span>
            </div>
          </label>

          <span className="date-separator">–</span>

          <label className="date-label">
            To
            <div className="date-input-wrapper">
              <input
                ref={endInputRef}
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
              />
              <span
                className="calendar-icon"
                onClick={() => openPicker(endInputRef.current)}
              >
                calendar_month
              </span>
            </div>
          </label>
        </div>
      </div>

      {/* ---------- CATEGORY FILTERS ---------- */}
      <div className="graph-filters-row">
        <span className="graph-filters-label">Show:</span>
        <div className="graph-filters-chips">
          {CATEGORY_OPTIONS.map((cat) => {
            const active = selectedCategories.includes(cat.id);
            return (
              <button
                key={cat.id}
                type="button"
                className={`graph-filter-chip ${active ? "graph-filter-chip-active" : ""
                  }`}
                onClick={() => handleToggleCategory(cat.id)}
              >
                {cat.label}
              </button>
            );
          })}
        </div>
      </div>

      {/* ---------- RESOLUTION FILTERS ---------- */}
      <div className="graph-filters-row">
        <span className="graph-filters-label">Date Range:</span>
        <div className="graph-filters-chips">
          {RESOLUTION_OPTIONS.map((opt) => {
            const active = resolution === opt.id;
            return (
              <button
                key={opt.id}
                type="button"
                className={`graph-filter-chip ${active ? "graph-filter-chip-active" : ""
                  }`}
                onClick={() => setResolution(opt.id)}
              >
                {opt.label}
              </button>
            );
          })}
        </div>
      </div>

      {/* ---------- MAIN CONTENT / STATUS ---------- */}
      {isRangeInvalid ? (
        // Invalid range message
        <div className="graph-status-center">
          <div className="graph-card graph-card-status graph-card-error">
            <p className="graph-status-title">
              The selected date range is invalid.
            </p>
            <p className="graph-status-subtitle">
              &quot;From&quot; must be earlier than or equal to &quot;To&quot;.
            </p>
          </div>
        </div>
      ) : loading ? (
        // Loading state
        <div className="graph-status-center">
          <div className="graph-card graph-card-status">
            <p className="graph-status-title">Loading data…</p>
            <p className="graph-status-subtitle">
              Fetching your health logs for the selected date range.
            </p>
          </div>
        </div>
      ) : !hasData ? (
        // No data state
        <div className="graph-status-center">
          <div className="graph-card graph-card-status">
            {error && <p className="graph-status-error">{error}</p>}
            <p className="graph-status-title">
              No data found for the selected date range.
            </p>
            <p className="graph-status-subtitle">
              Try choosing a different range or resolution.
            </p>
          </div>
        </div>
      ) : (
        // Charts
        <>
          {error && <div className="graph-error">{error}</div>}

          <div className="graph-grid">
            {/* Sleep */}
            {selectedCategories.includes("sleep") && (
              <GraphCard
                title="Sleep (hours)"
                description="Total sleep per day"
              >
                <ResponsiveContainer width="100%" height={220}>
                  <LineChart data={aggregatedData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#33363f" />
                    <XAxis dataKey="dateLabel" stroke="#9ea5ad" />
                    <YAxis stroke="#9ea5ad" />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: "#1f242b",
                        border: "none",
                      }} formatter={tooltipFormatter}
                    />
                    <Line
                      type="monotone"
                      dataKey="sleep"
                      stroke="#76abae"
                      strokeWidth={2}
                      dot={false}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </GraphCard>
            )}

            {/* Heart rate */}
            {selectedCategories.includes("vital") && (
              <GraphCard
                title="Heart Rate (vital)"
                description="Average heart rate per day"
              >
                <ResponsiveContainer width="100%" height={220}>
                  <LineChart data={aggregatedData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#33363f" />
                    <XAxis dataKey="dateLabel" stroke="#9ea5ad" />
                    <YAxis stroke="#9ea5ad" />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: "#1f242b",
                        border: "none",
                      }} formatter={tooltipFormatter}
                    />
                    <Line
                      type="monotone"
                      dataKey="vital"
                      stroke="#f2b880"
                      strokeWidth={2}
                      dot={false}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </GraphCard>
            )}

            {/* Mood */}
            {selectedCategories.includes("mood") && (
              <GraphCard title="Mood" description="Daily mood score (1–5)">
                <ResponsiveContainer width="100%" height={220}>
                  <BarChart data={aggregatedData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#33363f" />
                    <XAxis dataKey="dateLabel" stroke="#9ea5ad" />
                    <YAxis
                      domain={[0, 5]}
                      ticks={[1, 2, 3, 4, 5]}
                      stroke="#9ea5ad"
                    />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: "#1f242b",
                        border: "none",
                      }} formatter={tooltipFormatter}
                    />
                    <Bar
                      dataKey="mood"
                      fill="#76abae"
                      radius={[6, 6, 0, 0]}
                    />
                  </BarChart>
                </ResponsiveContainer>
              </GraphCard>
            )}

            {/* Medication */}
            {selectedCategories.includes("medication") && (
              <GraphCard
                title="Medication"
                description="1 = taken, 0 = not taken"
              >
                <ResponsiveContainer width="100%" height={220}>
                  <BarChart data={aggregatedData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#33363f" />
                    <XAxis dataKey="dateLabel" stroke="#9ea5ad" />
                    <YAxis domain={[0, 1]} ticks={[0, 1]} stroke="#9ea5ad" />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: "#1f242b",
                        border: "none",
                      }}
                      formatter={(value) =>
                        value === 1 ? "Taken" : "Not taken"
                      }
                    />
                    <Bar
                      dataKey="medicNumeric"
                      fill="#7dd3fc"
                      radius={[6, 6, 0, 0]}
                    />
                  </BarChart>
                </ResponsiveContainer>
              </GraphCard>
            )}
          </div>
        </>
      )}
    </div>
  );
}

function GraphCard({ title, description, children }) {
  return (
    <div className="graph-card">
      <div className="graph-card-header">
        <h2>{title}</h2>
        {description && <p>{description}</p>}
      </div>
      {children}
    </div>
  );
}

export default Graph;

import React, { useEffect, useState, useRef } from "react";
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
import "./Graph.css";

const API_BASE = process.env.REACT_APP_API_BASE_URL || "http://127.0.0.1:5001";

// Convert "YYYY-MM-DD" (from <input type="date">) to "MM-DD-YYYY" (API format)
const formatDateForApi = (isoStr) => {
  if (!isoStr) return null;
  const [yyyy, mm, dd] = isoStr.split("-");
  return `${mm}-${dd}-${yyyy}`; // e.g. "11-17-2025"
};

function Graph() {
  const today = new Date();
  const thirtyDaysAgo = new Date();
  thirtyDaysAgo.setDate(today.getDate() - 30);

  const [startDate, setStartDate] = useState(
    thirtyDaysAgo.toISOString().slice(0, 10) // "YYYY-MM-DD"
  );
  const [endDate, setEndDate] = useState(today.toISOString().slice(0, 10));
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const startInputRef = useRef(null);
  const endInputRef = useRef(null);

  const openPicker = (el) => {
    if (!el) return;
    if (typeof el.showPicker === "function") {
      el.showPicker();
    } else {
      el.focus();
    }
  };

  const isRangeInvalid = startDate && endDate && startDate > endDate;

  useEffect(() => {
    const fetchData = async () => {
      if (isRangeInvalid) {
        setData([]);
        setError("");
        setLoading(false);
        return;
      }

      try {
        setLoading(true);
        setError("");

        const params = new URLSearchParams();
        const from = formatDateForApi(startDate);
        const to = formatDateForApi(endDate);

        if (from) params.append("from", from);
        if (to) params.append("to", to);

        const url = `${API_BASE}/api/health-logs?${params.toString()}`;

        const res = await fetch(url);
        if (!res.ok) {
          throw new Error("Failed to load logs");
        }

        const raw = await res.json();

        // Map backend fields to the shape the charts expect
        const formatted = raw.map((item) => {
          // item.date is "MM-DD-YYYY"
          const [mm, dd, yyyy] = item.date.split("-");
          const jsDate = new Date(`${yyyy}-${mm}-${dd}`);

          return {
            ...item,
            // label for the X axis, e.g. "11/01"
            dateLabel: jsDate.toLocaleDateString("en-US", {
              month: "2-digit",
              day: "2-digit",
            }),
            // charts expect these keys:
            sleep: item.hours_of_sleep ?? null,
            vital: item.vital_bpm ?? null,
            mood: item.mood ?? null,
            medicNumeric: item.took_medication ? 1 : 0,
            // for now use mood as "condition" (can change later)
            condition: item.mood ?? null,
          };
        });

        setData(formatted);
      } catch (err) {
        console.error(err);
        setError("An error occurred while loading data.");
        setData([]);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [startDate, endDate, isRangeInvalid]);

  return (
    <div className="graph-page">
      {/* ---------- HEADER ---------- */}
      <div className="graph-header-row">
        <div>
          <h1 className="graph-title">Health Trends</h1>
          <p className="graph-subtitle">
            See how your sleep, medication, mood, heart rate, and condition
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

      {/* ---------- MAIN CONTENT / STATUS ---------- */}
      {isRangeInvalid ? (
        <div className="graph-status-center">
          <div className="graph-error">
            The selected date range is invalid. &quot;From&quot; must be earlier
            than or equal to &quot;To&quot;.
          </div>
        </div>
      ) : loading ? (
        <div className="graph-status-center">
          <div className="graph-loading">Loading data…</div>
        </div>
      ) : data.length === 0 ? (
        <div className="graph-status-center">
          {error && <div className="graph-error">{error}</div>}
          <div className="graph-empty">
            No data found for the selected date range.
            <br />
            Try choosing a different range.
          </div>
        </div>
      ) : (
        <>
          {error && <div className="graph-error">{error}</div>}

          <div className="graph-grid">
            {/* Sleep */}
            <GraphCard title="Sleep (hours)" description="Total sleep per day">
              <ResponsiveContainer width="100%" height={220}>
                <LineChart data={data}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#33363f" />
                  <XAxis dataKey="dateLabel" stroke="#9ea5ad" />
                  <YAxis stroke="#9ea5ad" />
                  <Tooltip
                    contentStyle={{ backgroundColor: "#1f242b", border: "none" }}
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

            {/* Heart rate */}
            <GraphCard
              title="Heart Rate (vital)"
              description="Average heart rate per day"
            >
              <ResponsiveContainer width="100%" height={220}>
                <LineChart data={data}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#33363f" />
                  <XAxis dataKey="dateLabel" stroke="#9ea5ad" />
                  <YAxis stroke="#9ea5ad" />
                  <Tooltip
                    contentStyle={{ backgroundColor: "#1f242b", border: "none" }}
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

            {/* Mood */}
            <GraphCard title="Mood" description="Daily mood score (1–5)">
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={data}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#33363f" />
                  <XAxis dataKey="dateLabel" stroke="#9ea5ad" />
                  <YAxis
                    domain={[0, 5]}
                    ticks={[1, 2, 3, 4, 5]}
                    stroke="#9ea5ad"
                  />
                  <Tooltip
                    contentStyle={{ backgroundColor: "#1f242b", border: "none" }}
                  />
                  <Bar dataKey="mood" fill="#76abae" radius={[6, 6, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </GraphCard>

            {/* Medication */}
            <GraphCard
              title="Medication"
              description="1 = taken, 0 = not taken"
            >
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={data}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#33363f" />
                  <XAxis dataKey="dateLabel" stroke="#9ea5ad" />
                  <YAxis domain={[0, 1]} ticks={[0, 1]} stroke="#9ea5ad" />
                  <Tooltip
                    contentStyle={{ backgroundColor: "#1f242b", border: "none" }}
                    formatter={(value) => (value === 1 ? "Taken" : "Not taken")}
                  />
                  <Bar
                    dataKey="medicNumeric"
                    fill="#7dd3fc"
                    radius={[6, 6, 0, 0]}
                  />
                </BarChart>
              </ResponsiveContainer>
            </GraphCard>

            {/* Condition */}
            <GraphCard
              title="Condition"
              description="Overall condition score (1–5)"
            >
              <ResponsiveContainer width="100%" height={220}>
                <LineChart data={data}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#33363f" />
                  <XAxis dataKey="dateLabel" stroke="#9ea5ad" />
                  <YAxis
                    domain={[0, 5]}
                    ticks={[1, 2, 3, 4, 5]}
                    stroke="#9ea5ad"
                  />
                  <Tooltip
                    contentStyle={{ backgroundColor: "#1f242b", border: "none" }}
                  />
                  <Line
                    type="monotone"
                    dataKey="condition"
                    stroke="#a5b4fc"
                    strokeWidth={2}
                    dot={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            </GraphCard>
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

import { useState, useEffect } from "react";
import { supabase } from "../../SupabaseClient"; 
import "./HealthLogCalendar.css";

const dayOfWeek = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
const monthsOfYear = [
  "January",
  "February",
  "March",
  "April",
  "May",
  "June",
  "July",
  "August",
  "September",
  "October",
  "November",
  "December",
];

const API_BASE = process.env.REACT_APP_API_BASE_URL || "";

const defaultForm = {
  tookMedication: false,
  sleepHours: "",
  vital_bpm: "",
  mood: 3,
  symptom: "none",
  note: "",
};

function HealthLogCalendar() {
  const now = new Date();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());

  // ✅ ADD: Get current user ID
  const [userId, setUserId] = useState(null);

  const [currentMonth, setCurrentMonth] = useState(today.getMonth());
  const [currentYear, setCurrentYear] = useState(today.getFullYear());
  const [selectedDate, setSelectedDate] = useState(null);
  const [showEventPopup, setShowEventPopup] = useState(false);
  const [form, setForm] = useState(defaultForm);
  const [events, setEvents] = useState([]);
  const [saving, setSaving] = useState(false);

  const daysInMonth = new Date(currentYear, currentMonth + 1, 0).getDate();
  const firstDayOfMonth = new Date(currentYear, currentMonth, 1).getDay();

  const isSameDate = (date1, date2) =>
    date1.getFullYear() === date2.getFullYear() &&
    date1.getMonth() === date2.getMonth() &&
    date1.getDate() === date2.getDate();

  const isFutureDate = (date) => date.getTime() > today.getTime();

  /* ============================
     0) Get user on mount
     ============================ */
  useEffect(() => {
    supabase.auth.getUser().then(({ data: { user } }) => {
      setUserId(user?.id || "anonymous");  // ✅ Changed: default to "anonymous"
    });
  }, []);

  /* ============================
     1) Load existing logs from backend
     ============================ */
  useEffect(() => {
   

    const fetchLogs = async () => {
      try {
      // ✅ ADD user_id to query (will be "anonymous" if not logged in)
      const url = userId 
        ? `${API_BASE}/api/health-logs?user_id=${userId}`
        : `${API_BASE}/api/health-logs?user_id=anonymous`;
      
      const res = await fetch(url);
      if (!res.ok) {
        console.error("❌ Failed to fetch health logs:", res.status);
        return;
      }
      const data = await res.json();

        const byId = {};

        data.forEach((log) => {
          const [mm, dd, yyyy] = log.date.split("-");
          const d = new Date(Number(yyyy), Number(mm) - 1, Number(dd));
          const idKey = d.toISOString().slice(0, 10);

          byId[idKey] = {
            id: idKey,
            date: d.toISOString(),
            tookMedication: !!log.tookMedication,
            sleepHours:
              log.sleepHours === null || log.sleepHours === undefined
                ? ""
                : log.sleepHours,
            vital_bpm: log.vital_bpm !== undefined && log.vital_bpm !== null
              ? log.vital_bpm : "",
            mood: log.mood ?? 3,
            symptom: log.symptom ?? "none",
            note: log.note ?? "",
          };
        });

        const mapped = Object.values(byId).sort(
          (a, b) => new Date(a.date) - new Date(b.date)
        );

        setEvents(mapped);
      } catch (err) {
        console.error("❌ Error loading health logs:", err);
      }
    };

    fetchLogs();
  }, [userId]); 

  /* ============================
     2) Month navigation
     ============================ */

  const prevMonth = () => {
    setCurrentMonth((prev) => {
      if (prev === 0) {
        setCurrentYear((y) => y - 1);
        return 11;
      }
      return prev - 1;
    });
  };

  const nextMonth = () => {
    setCurrentMonth((prev) => {
      if (prev === 11) {
        setCurrentYear((y) => y + 1);
        return 0;
      }
      return prev + 1;
    });
  };

  /* ============================
     3) Day click / popup
     ============================ */

  const handleDayClick = (day) => {
    const clicked = new Date(currentYear, currentMonth, day);

    if (isFutureDate(clicked)) return;

    setSelectedDate(clicked);
    setShowEventPopup(true);

    const existing = events.find((ev) =>
      isSameDate(new Date(ev.date), clicked)
    );

    if (existing) {
      setForm({
        tookMedication: !!existing.tookMedication,
        sleepHours: existing.sleepHours ?? "",
        vital_bpm: existing.vital_bpm ?? "",
        mood: existing.mood ?? 3,
        symptom: existing.symptom ?? "none",
        note: existing.note ?? "",
      });
      return;
    }

    // fetch from backend just in case
    const loadFromBackend = async () => {
    

      try {
        const iso = clicked.toISOString().slice(0, 10);
       
        const effectiveUserId = userId || "anonymous";
        const res = await fetch(`${API_BASE}/api/logs/one?date=${iso}&user_id=${effectiveUserId}`);
        if (!res.ok) {
          setForm(defaultForm);
          return;
        }
        const data = await res.json();
        if (!data || !data.date) {
          setForm(defaultForm);
          return;
        }

        setForm({
          tookMedication: !!data.tookMedication,
          sleepHours: data.sleepHours ?? "",
          vital_bpm: data.vital_bpm ?? "",
          mood: data.mood ?? 3,
          symptom: data.symptom ?? "none",
          note: data.note ?? "",
        });
      } catch (err) {
        console.error("❌ Error fetching single log:", err);
        setForm(defaultForm);
      }
    };

    loadFromBackend();
  };

  const handleInputChange = (e) => {
    const { name, type, checked, value } = e.target;
    setForm((prev) => ({
      ...prev,
      [name]: type === "checkbox" ? checked : value,
    }));
  };

  const handleMoodChange = (m) => {
    setForm((prev) => ({ ...prev, mood: m }));
  };

  /* ============================
     4) Submit (upsert) log
     ============================ */

  const handleSubmit = async (e) => {
    e.preventDefault();
    

    setSaving(true);
    const dateIso = selectedDate.toISOString().slice(0, 10);
    const idKey = dateIso;

     const effectiveUserId = userId || "anonymous";

    const payload = {
      user_id: effectiveUserId,  // ✅ Changed
      date: dateIso,
      tookMedication: !!form.tookMedication,
      sleepHours:
        form.sleepHours === "" ? null : Number.parseFloat(form.sleepHours),
      vital_bpm: form.vital_bpm === "" ? null : Number(form.vital_bpm),
      mood: Number(form.mood),
      symptom: form.symptom,
      note: form.note.trim(),
    };

    try {
      const res = await fetch(`${API_BASE}/api/logs`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      let body = null;
      try {
        body = await res.json();
      } catch (_) {
        // ignore
      }
      console.log("💾 Save log response:", res.status, body);

      if (!res.ok) {
        console.error("❌ Failed to save log");
      } else {
        const updatedEvent = {
          id: idKey,
          date: selectedDate.toISOString(),
          tookMedication: payload.tookMedication,
          sleepHours: payload.sleepHours ?? "",
          vital_bpm: payload.vital_bpm ?? "",
          mood: payload.mood,
          symptom: payload.symptom,
          note: payload.note,
        };

        setEvents((prev) => {
          const idx = prev.findIndex((ev) => ev.id === idKey);
          if (idx === -1) {
            return [...prev, updatedEvent].sort(
              (a, b) => new Date(a.date) - new Date(b.date)
            );
          }
          const clone = [...prev];
          clone[idx] = updatedEvent;
          return clone.sort(
            (a, b) => new Date(a.date) - new Date(b.date)
          );
        });
      }
    } catch (err) {
      console.error("❌ Error saving log:", err);
    } finally {
      setSaving(false);
      setShowEventPopup(false);
    }
  };

  /* ============================
     5) Edit / delete
     ============================ */

  const handleEditEvent = (event) => {
    const d = new Date(event.date);
    if (isFutureDate(d)) return;

    setSelectedDate(d);
    setShowEventPopup(true);
    setForm({
      tookMedication: !!event.tookMedication,
      sleepHours: event.sleepHours ?? "",
      vital_bpm: event.vital_bpm ?? "",
      mood: event.mood ?? 3,
      symptom: event.symptom ?? "none",
      note: event.note ?? "",
    });
  };

  const handleDeleteEvent = (id) => {
    // DELETE from backend
    setEvents((prev) => prev.filter((ev) => ev.id !== id));
  };

  /* ============================
     6) UI helpers
     ============================ */

  const renderMoodEmojis = () => {
    const opts = [
      { v: 1, e: "😞" },
      { v: 2, e: "😕" },
      { v: 3, e: "😐" },
      { v: 4, e: "🙂" },
      { v: 5, e: "😄" },
    ];
    return (
      <div className="mood-options">
        {opts.map((o) => (
          <button
            key={o.v}
            type="button"
            className={
              Number(form.mood) === o.v ? "mood-emoji active" : "mood-emoji"
            }
            onClick={() => handleMoodChange(o.v)}
          >
            {o.e}
          </button>
        ))}
      </div>
    );
  };

  // ============================
  // 7) Events filtered by current month/year
  // ============================
  const visibleEvents = events.filter((event) => {
    const d = new Date(event.date);
    return (
      d.getFullYear() === currentYear &&
      d.getMonth() === currentMonth
    );
  });

  return (
    <div className="container">
      <div className="calendar-app">
        {/* Calendar column */}
        <div className="calendar">
          <h1 className="heading">Health Log</h1>

          <div className="navigate-date">
            <h2 className="month">{monthsOfYear[currentMonth]},</h2>
            <h2 className="year">{currentYear}</h2>
            <div className="buttons">
              <i className="bx bx-chevron-left" onClick={prevMonth}></i>
              <i className="bx bx-chevron-right" onClick={nextMonth}></i>
            </div>
          </div>

          <div className="weekdays">
            {dayOfWeek.map((day) => (
              <span key={day}>{day}</span>
            ))}
          </div>

          <div className="days">
            {Array.from({ length: firstDayOfMonth }).map((_, idx) => (
              <span key={`empty-${idx}`}></span>
            ))}

            {Array.from({ length: daysInMonth }).map((_, idx) => {
              const dayNum = idx + 1;
              const cellDate = new Date(currentYear, currentMonth, dayNum);
              const isToday = isSameDate(cellDate, today);

              return (
                <span
                  key={dayNum}
                  className={isToday ? "current-day" : ""}
                  onClick={() => handleDayClick(dayNum)}
                >
                  {dayNum}
                </span>
              );
            })}
          </div>
        </div>

        {/* Logged days list */}
        <div className="events">
          {visibleEvents.map((event) => {
            const dateObj = new Date(event.date);

            const pieces = [];
            pieces.push(
              event.tookMedication ? "💊 Took meds" : "🚫 Skipped meds"
            );
            if (event.vital_bpm) pieces.push(`❤️ ${event.vital_bpm} bpm`);
            if (event.symptom && event.symptom !== "none")
              pieces.push(`🩺 ${event.symptom}`);
            const mainLine = pieces.join(" · ");

            const sleepLabel =
              typeof event.sleepHours === "number" ||
                (typeof event.sleepHours === "string" &&
                  event.sleepHours !== "")
                ? `${event.sleepHours}h sleep`
                : "-";

            return (
              <div className="event" key={event.id}>
                <div className="event-date-wrapper">
                  <div className="event-date">
                    {dateObj.toLocaleDateString("en-US", {
                      month: "long",
                      day: "numeric",
                      year: "numeric",
                    })}
                  </div>
                  <div className="event-sleep">{sleepLabel}</div>
                </div>

                <div className="event-text">
                  <div className="event-main-line">{mainLine || "-"}</div>
                  {event.note && event.note.trim() !== "" && (
                    <div className="event-note">{event.note}</div>
                  )}
                </div>

                <div className="event-buttons">
                  <i
                    className="bx bxs-edit-alt"
                    onClick={() => handleEditEvent(event)}
                  />
                  <i
                    className="bx bxs-message-alt-x"
                    onClick={() => handleDeleteEvent(event.id)}
                  />
                </div>
              </div>
            );
          })}
        </div>

        {/* Popup */}
        {showEventPopup && selectedDate && (
          <div className="event-popup">
            <button
              className="close-event-popup"
              type="button"
              onClick={() => setShowEventPopup(false)}
            >
              <i className="bx bx-x" />
            </button>

            <div className="popup-row-header">
              <div className="popup-date-label">
                {selectedDate.toLocaleDateString("en-US", {
                  month: "long",
                  day: "numeric",
                  year: "numeric",
                })}
              </div>
            </div>

            <form onSubmit={handleSubmit}>
              <div className="popup-row">
                <div className="popup-field">
                  <span className="popup-label">Took medication?</span>
                  <label className="popup-toggle">
                    <input
                      type="checkbox"
                      name="tookMedication"
                      checked={form.tookMedication}
                      onChange={handleInputChange}
                    />
                    <span>Yes</span>
                  </label>
                </div>
              </div>

              <div className="popup-row">
                <div className="popup-field">
                  <span className="popup-label">Sleep (hrs)</span>
                  <input
                    type="number"
                    min="0"
                    max="24"
                    step="0.5"
                    name="sleepHours"
                    value={form.sleepHours}
                    onChange={handleInputChange}
                  />
                </div>
                <div className="popup-field">
                  <span className="popup-label"> Vital (bpm)</span>
                  <input
                    type="number"
                    min="30"
                    max="220"
                    name="vital_bpm"
                    value={form.vital_bpm}
                    onChange={handleInputChange}
                  />
                </div>
              </div>

              <div className="popup-row">
                <div className="popup-field">
                  <span className="popup-label">Mood</span>
                  {renderMoodEmojis()}
                </div>
              </div>

              <div className="popup-row-two">
                <div className="popup-field">
                  <span className="popup-label">Symptom</span>
                  <select
                    name="symptom"
                    value={form.symptom}
                    onChange={handleInputChange}
                  >
                    <option value="none">None</option>
                    <option value="fever">fever</option>
                    <option value="cough">cough</option>
                    <option value="headache">headache</option>
                    <option value="nausea">nausea</option>
                    <option value="pain">pain</option>
                    <option value="other">other</option>
                  </select>
                </div>

                <div className="popup-field">
                  <span className="popup-label">Note</span>
                  <textarea
                    name="note"
                    rows={3}
                    placeholder="Anything important to remember"
                    value={form.note}
                    onChange={handleInputChange}
                    required={form.symptom === "other"}
                  />
                </div>
              </div>

              <button
                className="event-popup-btn"
                type="submit"
                disabled={saving}
              >
                {saving ? "Saving..." : "Save log"}
              </button>
            </form>
          </div>
        )}
      </div>
    </div>
  );
}

export default HealthLogCalendar;

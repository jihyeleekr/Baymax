import { useState } from "react";
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

const defaultForm = {
  tookMedication: false,
  sleepHours: "",
  heartRate: "",
  mood: 3,
  symptom: "none",
  note: "",
};

function HealthLogCalendar() {
  const today = new Date();

  const [currentMonth, setCurrentMonth] = useState(today.getMonth());
  const [currentYear, setCurrentYear] = useState(today.getFullYear());
  const [selectedDate, setSelectedDate] = useState(null);
  const [showEventPopup, setShowEventPopup] = useState(false);
  const [form, setForm] = useState(defaultForm);
  const [events, setEvents] = useState([]);
  const [saving, setSaving] = useState(false);

  const daysInMonth = new Date(currentYear, currentMonth + 1, 0).getDate();
  const firstDayOfMonth = new Date(currentYear, currentMonth, 1).getDay();

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

  const isSameDate = (date1, date2) =>
    date1.getFullYear() === date2.getFullYear() &&
    date1.getMonth() === date2.getMonth() &&
    date1.getDate() === date2.getDate();

  const handleDayClick = (day) => {
    const clicked = new Date(currentYear, currentMonth, day);
    setSelectedDate(clicked);
    setShowEventPopup(true);

    const existing = events.find((ev) => isSameDate(new Date(ev.date), clicked));
    if (existing) {
      setForm({
        tookMedication: !!existing.tookMedication,
        sleepHours: existing.sleepHours ?? "",
        heartRate: existing.heartRate ?? "",
        mood: existing.mood ?? 3,
        symptom: existing.symptom ?? "none",
        note: existing.note ?? "",
      });
    } else {
      setForm(defaultForm);
    }
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

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!selectedDate) return;

    setSaving(true);

    const idKey = selectedDate.toISOString().slice(0, 10); // YYYY-MM-DD per-day

    const payload = {
      id: idKey,
      date: selectedDate.toISOString(),
      tookMedication: !!form.tookMedication,
      sleepHours:
        form.sleepHours === "" ? null : Number.parseFloat(form.sleepHours),
      heartRate:
        form.heartRate === "" ? null : Number.parseInt(form.heartRate, 10),
      mood: Number(form.mood),
      symptom: form.symptom,
      note: form.note.trim(),
    };

    setEvents((prev) => {
      const idx = prev.findIndex((ev) => ev.id === idKey);
      if (idx === -1) {
        return [...prev, payload].sort(
          (a, b) => new Date(a.date) - new Date(b.date)
        );
      }
      const clone = [...prev];
      clone[idx] = payload;
      return clone.sort((a, b) => new Date(a.date) - new Date(b.date));
    });

    setSaving(false);
    setShowEventPopup(false);
  };

  const handleEditEvent = (event) => {
    const d = new Date(event.date);
    setSelectedDate(d);
    setShowEventPopup(true);
    setForm({
      tookMedication: !!event.tookMedication,
      sleepHours: event.sleepHours ?? "",
      heartRate: event.heartRate ?? "",
      mood: event.mood ?? 3,
      symptom: event.symptom ?? "none",
      note: event.note ?? "",
    });
  };

  const handleDeleteEvent = (id) => {
    setEvents((prev) => prev.filter((ev) => ev.id !== id));
  };

  // mood emoji group
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
              // future dates = strictly after today (today is allowed)
              const isFuture = cellDate > today && !isToday;

              const classes = [
                isToday ? "current-day" : "",
                isFuture ? "future-day" : "",
              ]
                .filter(Boolean)
                .join(" ");

              return (
                <span
                  key={dayNum}
                  className={classes}
                  // block future clicks, but keep same look
                  onClick={() => {
                    if (!isFuture) {
                      handleDayClick(dayNum);
                    }
                  }}
                >
                  {dayNum}
                </span>
              );
            })}
          </div>
        </div>

        {/* Logged days list */}
        <div className="events">
          {events.map((event) => {
            const dateObj = new Date(event.date);

            const pieces = [];
            pieces.push(
              event.tookMedication ? "💊 Took meds" : "🚫 Skipped meds"
            );
            if (event.heartRate) pieces.push(`❤️ ${event.heartRate} bpm`);
            if (event.symptom && event.symptom !== "none")
              pieces.push(`🩺 ${event.symptom}`);
            const mainLine = pieces.join(" · ");

            const sleepLabel =
              typeof event.sleepHours === "number"
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

        {/* Popup for daily log */}
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
                    step="0.1"
                    name="sleepHours"
                    value={form.sleepHours}
                    onChange={handleInputChange}
                  />
                </div>
                <div className="popup-field">
                  <span className="popup-label">Heart rate (bpm)</span>
                  <input
                    type="number"
                    min="30"
                    max="220"
                    name="heartRate"
                    value={form.heartRate}
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

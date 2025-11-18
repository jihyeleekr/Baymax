const API_BASE = process.env.REACT_APP_API_BASE_URL || "http://127.0.0.1:5001";

export async function fetchHealthLogs(from, to) {
  const params = new URLSearchParams();
  if (from) params.append("from", from);
  if (to) params.append("to", to);

  const url = `${API_BASE}/api/health-logs?${params.toString()}`;

  const res = await fetch(url);

  if (!res.ok) {
    throw new Error("Failed to fetch health logs");
  }

  return await res.json();
}

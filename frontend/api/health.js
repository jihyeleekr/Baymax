const API_BASE = process.env.REACT_APP_API_BASE_URL || "http://127.0.0.1:5001";

export async function fetchHealthLogs(userId, from, to) {
  const params = new URLSearchParams();
  
  // ✅ Add user_id (required)
  if (userId) {
    params.append("user_id", userId);
  } else {
    throw new Error("user_id is required");
  }
  
  if (from) params.append("from", from);
  if (to) params.append("to", to);

  const url = `${API_BASE}/api/health-logs?${params.toString()}`;

  const res = await fetch(url);

  if (!res.ok) {
    throw new Error("Failed to fetch health logs");
  }

  return await res.json();
}

// ✅ Add function to create new logs
export async function createHealthLog(userId, logData) {
  if (!userId) {
    throw new Error("user_id is required");
  }

  const res = await fetch(`${API_BASE}/api/health-logs`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      ...logData,
      user_id: userId
    })
  });

  if (!res.ok) {
    throw new Error("Failed to create health log");
  }

  return await res.json();
}

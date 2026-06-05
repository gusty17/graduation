const API_URL = "http://127.0.0.1:5000";

/* ================= DASHBOARD ================= */
export async function predictCSV(file) {
  const formData = new FormData();
  formData.append("file", file);

  const res = await fetch(`${API_URL}/predict`, {
    method: "POST",
    body: formData,
  });

  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.error || "Prediction failed");
  }

  return res.json();
}

/* ================= ANALYTICS ================= */
export async function fetchAnalytics() {
  const res = await fetch(`${API_URL}/analytics`);

  if (!res.ok) {
    throw new Error("Failed to load analytics");
  }

  return res.json();
}

/* ================= REAL-TIME SSE ================= */
// Note: Use useLiveSSE hook in components instead of polling
// The hook handles EventSource connection/disconnection automatically
export function streamRealtimePredictions() {
  // This is handled by useLiveSSE hook - do not poll manually
  return new EventSource(`${API_URL}/realtime/stream`);
}

/* ================= LIVE PREDICTION CONTROL ================= */
export async function startLivePrediction() {
  const res = await fetch(`${API_URL}/realtime/start`, {
    method: "POST",
  });

  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.error || "Failed to start live prediction");
  }

  return res.json();
}

export async function stopLivePrediction() {
  const res = await fetch(`${API_URL}/realtime/stop`, {
    method: "POST",
  });

  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.error || "Failed to stop live prediction");
  }

  return res.json();
}
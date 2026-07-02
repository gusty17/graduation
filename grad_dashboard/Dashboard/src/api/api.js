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

/* ================= TRAINING DATA COLLECTION ================= */
export async function fetchCollectSessions() {
  const res = await fetch(`${API_URL}/collect/sessions`);
  if (!res.ok) throw new Error("Failed to load sessions");
  return res.json();
}

export async function startCollection({ label, session, duration }) {
  const res = await fetch(`${API_URL}/collect/start`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ label, session, duration }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.error || "Failed to start collection");
  }
  return res.json();
}

export async function stopCollection() {
  const res = await fetch(`${API_URL}/collect/stop`, { method: "POST" });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.error || "Failed to stop collection");
  }
  return res.json();
}

export async function fetchCollectStatus() {
  const res = await fetch(`${API_URL}/collect/status`);
  if (!res.ok) throw new Error("Failed to load collection status");
  return res.json();
}
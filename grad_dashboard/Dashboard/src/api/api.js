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

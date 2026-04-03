const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export async function apiFetch(url, token, options = {}) {
  const res = await fetch(`${API_BASE}${url}`, {
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Request failed (${res.status})`);
  }
  return res.json();
}

export const statusColor = (s) => {
  switch (s?.toLowerCase()) {
    case "completed":   return "#059669";
    case "in_progress": return "#6366F1";
    case "missed":      return "#DC2626";
    case "skipped":     return "#9CA3AF";
    case "paused":      return "#9CA3AF";
    default:            return "#F59E0B";
  }
};

export const statusBg = (s) => {
  switch (s?.toLowerCase()) {
    case "completed":   return "rgba(5,150,105,0.09)";
    case "in_progress": return "rgba(99,102,241,0.09)";
    case "missed":      return "rgba(220,38,38,0.09)";
    case "skipped":     return "rgba(156,163,175,0.09)";
    case "paused":      return "rgba(156,163,175,0.09)";
    default:            return "rgba(245,158,11,0.09)";
  }
};

export const categoryIcon = (cat) => {
  const c = (cat || "").toLowerCase();
  if (c.includes("fit"))     return "\u{1F3C3}";
  if (c.includes("career"))  return "\u{1F4BC}";
  if (c.includes("learn"))   return "\u{1F4DA}";
  if (c.includes("health"))  return "\u{2764}\u{FE0F}";
  if (c.includes("finance")) return "\u{1F4B0}";
  return "\u{1F3AF}";
};

export const formatDate = (d) =>
  d ? new Date(d).toLocaleDateString("en-US", { month: "short", day: "numeric" }) : "\u2014";

export const formatDateFull = (d) =>
  d
    ? new Date(d).toLocaleDateString("en-US", {
        month: "short", day: "numeric", year: "numeric",
      })
    : "\u2014";

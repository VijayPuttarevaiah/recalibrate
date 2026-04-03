/**
 * @file Dashboard.jsx
 * Goals displayed as a responsive grid of cards.
 * Now shows "behind schedule" indicator on cards needing replan.
 * Click a card → navigate to GoalTasksPage
 */
import React, { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

async function apiFetch(url, token) {
  const res = await fetch(`${API_BASE}${url}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Request failed (${res.status})`);
  }
  return res.json();
}

const statusColor = (s) => {
  switch (s?.toLowerCase()) {
    case "completed":   return "#059669";
    case "in_progress": return "#6366F1";
    case "paused":      return "#9CA3AF";
    default:            return "#F59E0B";
  }
};
const statusBg = (s) => {
  switch (s?.toLowerCase()) {
    case "completed":   return "rgba(5,150,105,0.09)";
    case "in_progress": return "rgba(99,102,241,0.09)";
    case "paused":      return "rgba(156,163,175,0.09)";
    default:            return "rgba(245,158,11,0.09)";
  }
};
const categoryIcon = (cat) => {
  const c = (cat || "").toLowerCase();
  if (c.includes("fit"))     return "🏃";
  if (c.includes("career"))  return "💼";
  if (c.includes("learn"))   return "📚";
  if (c.includes("health"))  return "❤️";
  if (c.includes("finance")) return "💰";
  return "🎯";
};
const formatDate = (d) =>
  d ? new Date(d).toLocaleDateString("en-US", { month: "short", day: "numeric" }) : "—";

function StatusBadge({ status }) {
  return (
    <span style={{
      display: "inline-flex", alignItems: "center",
      fontSize: 10, fontWeight: 700,
      textTransform: "uppercase", letterSpacing: "0.6px",
      padding: "3px 10px", borderRadius: 99,
      color: statusColor(status),
      background: statusBg(status),
      border: `1px solid ${statusColor(status)}35`,
    }}>
      {status?.replace(/_/g, " ") || "pending"}
    </span>
  );
}

function StatCard({ label, value, color, icon }) {
  return (
    <div className="Panel" style={{ textAlign: "center", padding: "18px 12px" }}>
      <div style={{ fontSize: 22, marginBottom: 4 }}>{icon}</div>
      <div style={{ fontSize: 32, fontWeight: 800, color, lineHeight: 1 }}>{value}</div>
      <div style={{
        fontSize: 10, color: "var(--Muted)", fontWeight: 700,
        textTransform: "uppercase", letterSpacing: "0.6px", marginTop: 4,
      }}>{label}</div>
    </div>
  );
}

function BehindBadge({ missedCount }) {
  if (!missedCount || missedCount === 0) return null;
  return (
    <span style={{
      display: "inline-flex", alignItems: "center", gap: 4,
      fontSize: 10, fontWeight: 700,
      padding: "3px 9px", borderRadius: 99,
      color: "#DC2626",
      background: "rgba(220,38,38,0.08)",
      border: "1px solid rgba(220,38,38,0.2)",
    }}>
      ⚠ {missedCount} behind
    </span>
  );
}

function GoalCard({ goal, replanInfo, onClick }) {
  const [hovered, setHovered] = useState(false);
  const accent = statusColor(goal.status);
  const icon   = categoryIcon(goal.category);
  const isPaused = goal.status === "paused";
  const progress =
    goal.status === "completed"   ? 100 :
    goal.status === "in_progress" ?  55 :
    goal.status === "paused"      ?   0 : 0;

  const needsReplan = replanInfo?.needs_replan;

  return (
    <div
      onClick={() => onClick(goal)}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      style={{
        background: "#FFFFFF",
        border: needsReplan ? "1px solid #FBBF2480" : "1px solid var(--Border)",
        borderRadius: 20,
        padding: "20px 20px 16px",
        cursor: "pointer",
        display: "flex", flexDirection: "column", gap: 13,
        transition: "all 0.22s ease",
        boxShadow: hovered
          ? "0 16px 40px -8px rgba(99,102,241,0.18), 0 4px 12px -2px rgba(0,0,0,0.06)"
          : needsReplan
          ? "0 2px 12px -2px rgba(245,158,11,0.15)"
          : "0 2px 8px -2px rgba(0,0,0,0.05)",
        transform: hovered ? "translateY(-4px)" : "translateY(0)",
        opacity: isPaused ? 0.65 : 1,
        position: "relative", overflow: "hidden",
      }}
    >
      {/* Top color stripe */}
      <div style={{
        position: "absolute", top: 0, left: 0, right: 0, height: 4,
        background: needsReplan ? "#F59E0B" : accent,
        borderRadius: "20px 20px 0 0",
      }} />

      {/* Icon + Badge row */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginTop: 6, gap: 6 }}>
        <div style={{
          width: 44, height: 44, borderRadius: 12,
          background: `${accent}12`, border: `1px solid ${accent}22`,
          display: "flex", alignItems: "center", justifyContent: "center", fontSize: 22,
        }}>{icon}</div>
        <div style={{ display: "flex", gap: 6, flexWrap: "wrap", justifyContent: "flex-end" }}>
          {needsReplan && <BehindBadge missedCount={replanInfo?.missed_count} />}
          <StatusBadge status={goal.status} />
        </div>
      </div>

      {/* Title + Category */}
      <div>
        <h3 style={{
          margin: "0 0 4px", fontSize: 15, fontWeight: 700,
          color: "var(--Text)", lineHeight: 1.35,
          display: "-webkit-box", WebkitLineClamp: 2,
          WebkitBoxOrient: "vertical", overflow: "hidden",
        }}>{goal.title}</h3>
        {goal.category && (
          <span style={{ fontSize: 10, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.5px", color: accent }}>
            {goal.category.replace(/_/g, " ")}
          </span>
        )}
      </div>

      {/* Dates */}
      <div style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 12, color: "var(--Muted)" }}>
        <span>📅</span>
        <span>{formatDate(goal.start_date)} → {formatDate(goal.end_date)}</span>
      </div>

      {/* Progress bar */}
      <div>
        <div style={{ display: "flex", justifyContent: "space-between", fontSize: 11, color: "var(--Muted)", marginBottom: 5 }}>
          <span style={{ fontWeight: 600 }}>Progress</span>
          <span style={{ fontWeight: 700, color: accent }}>{progress}%</span>
        </div>
        <div style={{ height: 5, borderRadius: 99, background: "var(--Border)", overflow: "hidden" }}>
          <div style={{
            height: "100%", width: `${progress}%`, borderRadius: 99,
            background: accent, transition: "width 0.5s ease",
          }} />
        </div>
      </div>

      {/* Footer */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <span style={{
          fontSize: 12, color: "var(--Muted)",
          background: "var(--Bg)", border: "1px solid var(--Border)",
          padding: "3px 10px", borderRadius: 99, fontWeight: 600,
        }}>{goal.task_count || 0} tasks</span>
        <div style={{
          width: 28, height: 28, borderRadius: "50%",
          background: hovered ? accent : "var(--Bg)",
          border: `1px solid ${hovered ? accent : "var(--Border)"}`,
          display: "flex", alignItems: "center", justifyContent: "center",
          fontSize: 13, color: hovered ? "#fff" : "var(--Muted)",
          transition: "all 0.2s ease",
        }}>→</div>
      </div>
    </div>
  );
}

function EmptyState({ onRefresh }) {
  return (
    <div style={{ textAlign: "center", padding: "72px 24px" }}>
      <div style={{ fontSize: 56, marginBottom: 16, opacity: 0.2 }}>🎯</div>
      <h3 style={{ margin: "0 0 8px", fontSize: 20, fontWeight: 700, color: "var(--Text)" }}>No goals yet</h3>
      <p style={{ margin: "0 0 24px", color: "var(--Muted)", fontSize: 14, lineHeight: 1.6, maxWidth: 300, marginInline: "auto" }}>
        Create your first goal to get started with your adaptive plan.
      </p>
      <button className="Button" onClick={onRefresh}>Refresh</button>
    </div>
  );
}

function ErrorState({ message, onRetry }) {
  return (
    <div className="Alert" style={{ margin: "16px 0", display: "flex", alignItems: "center", flexWrap: "wrap", gap: 12 }}>
      <span style={{ flex: 1 }}>{message}</span>
      <button className="Button" onClick={onRetry} style={{ fontSize: 12, padding: "4px 14px" }}>Retry</button>
    </div>
  );
}

export default function Dashboard() {
  const [goals, setGoals]     = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError]     = useState(null);
  const [replanStatuses, setReplanStatuses] = useState({});  // goalId → replanCheck
  const navigate = useNavigate();
  const token = localStorage.getItem("agp_auth_token");

  const fetchGoals = useCallback(async () => {
    setLoading(true); setError(null);
    try {
      const data = await apiFetch("/goals/", token);
      setGoals(data);

      // Check replan status for each active (non-completed) goal
      const statuses = {};
      const activeGoals = data.filter(
        (g) => g.status !== "completed" && g.status !== "paused"
      );
      await Promise.allSettled(
        activeGoals.map(async (g) => {
          try {
            const check = await apiFetch(
              `/goals/${g.id}/replan/check?threshold=3`,
              token
            );
            statuses[g.id] = check;
          } catch {
            // silently skip — replan check is non-critical
          }
        })
      );
      setReplanStatuses(statuses);
    } catch (e) { setError(e.message); }
    finally { setLoading(false); }
  }, [token]);

  useEffect(() => { fetchGoals(); }, [fetchGoals]);

  const handleGoalClick = (goal) =>
    navigate(`/goals/${goal.id}/tasks`, { state: { goal } });

  const totalGoals     = goals.length;
  const completedGoals = goals.filter((g) => g.status === "completed").length;
  const pausedGoals    = goals.filter((g) => g.status === "paused").length;
  const totalTasks     = goals.reduce((sum, g) => sum + (g.task_count || 0), 0);
  const goalsBehind    = Object.values(replanStatuses).filter(
    (r) => r?.needs_replan
  ).length;

  return (
    <section style={{ maxWidth: 960, margin: "0 auto", padding: "32px 24px", minHeight: "calc(100vh - 64px)" }}>
      <div style={{ marginBottom: 32 }}>
        <h2 style={{ margin: "0 0 4px", fontSize: 28, fontWeight: 800, color: "var(--Text)", letterSpacing: "-0.5px" }}>
          My Goals
        </h2>
        <p style={{ margin: 0, color: "var(--Muted)", fontSize: 14, lineHeight: 1.6 }}>
          Track your progress and stay on course.
        </p>
      </div>

      {/* Stat cards */}
      {!loading && goals.length > 0 && (
        <div style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(130px, 1fr))",
          gap: 14,
          marginBottom: 32,
        }}>
          <StatCard label="Total Goals" value={totalGoals}     color="var(--Primary)" icon="" />
          <StatCard label="Completed"   value={completedGoals} color="#059669"        icon="" />
          <StatCard label="Total Tasks" value={totalTasks}     color="var(--Accent)"  icon="" />
          {pausedGoals > 0 && (
            <StatCard label="Paused"         value={pausedGoals}  color="#9CA3AF"       icon="⏸" />
          )}
          {goalsBehind > 0 && (
            <StatCard label="Need Attention" value={goalsBehind}  color="#DC2626"       icon="" />
          )}
        </div>
      )}

      {loading  && <div style={{ textAlign: "center", padding: 64, color: "var(--Muted)" }}>Loading your goals…</div>}
      {error    && <ErrorState message={error} onRetry={fetchGoals} />}
      {!loading && !error && goals.length === 0 && <EmptyState onRefresh={fetchGoals} />}

      {/* Goal cards grid */}
      {!loading && !error && goals.length > 0 && (
        <div style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fill, minmax(260px, 1fr))",
          gap: 18,
        }}>
          {goals.map((goal) => (
            <GoalCard
              key={goal.id}
              goal={goal}
              replanInfo={replanStatuses[goal.id]}
              onClick={handleGoalClick}
            />
          ))}
        </div>
      )}
    </section>
  );
}
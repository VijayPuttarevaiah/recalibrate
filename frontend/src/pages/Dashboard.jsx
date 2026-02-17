/**
 * @file Dashboard.jsx
 * @description Primary Landing Page for authenticated users.
 * Fetches and displays user goals and their associated tasks.
 */

import React, { useState, useEffect, useCallback } from "react";

/* ─── API Configuration ─── */
const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

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

/* ─── Tiny Helpers ─── */
const statusColor = (s) => {
  switch (s?.toLowerCase()) {
    case "completed": return "#059669";
    case "in_progress": return "#6366F1";
    case "pending": default: return "#F59E0B";
  }
};

const formatDate = (d) =>
  d ? new Date(d).toLocaleDateString("en-US", { month: "short", day: "numeric" }) : "";

/* ─── Sub-Components ─── */

function StatusBadge({ status }) {
  return (
    <span
      style={{
        display: "inline-block",
        fontSize: 11,
        fontWeight: 700,
        textTransform: "uppercase",
        letterSpacing: "0.5px",
        padding: "3px 10px",
        borderRadius: 99,
        color: statusColor(status),
        background: `${statusColor(status)}15`,
        border: `1px solid ${statusColor(status)}30`,
      }}
    >
      {status?.replace("_", " ") || "pending"}
    </span>
  );
}

function EmptyState({ onRefresh }) {
  return (
    <div style={{ textAlign: "center", padding: "48px 24px" }}>
      <div style={{ fontSize: 48, marginBottom: 16, opacity: 0.3 }}>🎯</div>
      <h3 style={{ margin: "0 0 8px", fontSize: 18, fontWeight: 700, color: "var(--Text)" }}>
        No goals yet
      </h3>
      <p style={{ margin: "0 0 20px", color: "var(--Muted)", fontSize: 14, lineHeight: 1.6 }}>
        Create your first goal to get started with your adaptive plan.
      </p>
      <button className="Button" onClick={onRefresh} style={{ fontSize: 13, padding: "8px 20px" }}>
        Refresh
      </button>
    </div>
  );
}

function LoadingState() {
  return (
    <div style={{ textAlign: "center", padding: "48px 24px" }}>
      <div className="Spinner" />
      <p style={{ color: "var(--Muted)", fontSize: 14, marginTop: 16 }}>Loading your goals…</p>
    </div>
  );
}

function ErrorState({ message, onRetry }) {
  return (
    <div className="Alert" style={{ margin: "16px 0" }}>
      {message}
      <button
        className="Button"
        onClick={onRetry}
        style={{ marginLeft: 12, fontSize: 12, padding: "4px 14px" }}
      >
        Retry
      </button>
    </div>
  );
}

/* ─── Task List (expanded inside a goal) ─── */

function TaskList({ tasks }) {
  if (!tasks || tasks.length === 0) {
    return <p style={{ color: "var(--Muted)", fontSize: 13, padding: "8px 0" }}>No tasks found.</p>;
  }

  return (
    <div style={{ display: "grid", gap: 6, marginTop: 12 }}>
      {tasks.map((task) => (
        <div
          key={task.id}
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            padding: "10px 14px",
            borderRadius: 10,
            background: "var(--Bg)",
            border: "1px solid var(--Border)",
            fontSize: 13,
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: 10, flex: 1, minWidth: 0 }}>
            <span
              style={{
                width: 6,
                height: 6,
                borderRadius: "50%",
                background: statusColor(task.status),
                flexShrink: 0,
              }}
            />
            <span
              style={{
                fontWeight: 500,
                color: "var(--Text)",
                overflow: "hidden",
                textOverflow: "ellipsis",
                whiteSpace: "nowrap",
              }}
            >
              {task.title}
            </span>
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: 10, flexShrink: 0 }}>
            <span style={{ color: "var(--Muted)", fontSize: 12 }}>{formatDate(task.due_date)}</span>
            <StatusBadge status={task.status} />
          </div>
        </div>
      ))}
    </div>
  );
}

/* ─── Goal Card ─── */

function GoalCard({ goal, isExpanded, onToggle, tasks, loadingTasks }) {
  const progress = goal.task_count > 0
    ? Math.round((tasks?.filter((t) => t.status === "completed").length / goal.task_count) * 100)
    : 0;

  return (
    <div
      className="Panel"
      style={{
        cursor: "pointer",
        transition: "all 0.2s ease",
        borderLeft: `3px solid ${statusColor(goal.status)}`,
      }}
      onClick={onToggle}
    >
      {/* Header row */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
        <div style={{ flex: 1, minWidth: 0 }}>
          <h3
            style={{
              margin: "0 0 6px",
              fontSize: 16,
              fontWeight: 700,
              color: "var(--Text)",
              overflow: "hidden",
              textOverflow: "ellipsis",
              whiteSpace: "nowrap",
            }}
          >
            {goal.title}
          </h3>

          <div style={{ display: "flex", gap: 16, fontSize: 12, color: "var(--Muted)" }}>
            {goal.category && (
              <span style={{ fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.3px" }}>
                {goal.category}
              </span>
            )}
            <span>
              {formatDate(goal.start_date)} → {formatDate(goal.end_date)}
            </span>
            <span>{goal.task_count} tasks</span>
          </div>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <StatusBadge status={goal.status} />
          <span
            style={{
              fontSize: 16,
              color: "var(--Muted)",
              transition: "transform 0.2s",
              transform: isExpanded ? "rotate(180deg)" : "rotate(0deg)",
            }}
          >
            ▾
          </span>
        </div>
      </div>

      {/* Progress bar */}
      {isExpanded && goal.task_count > 0 && (
        <div style={{ marginTop: 12 }}>
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              fontSize: 11,
              color: "var(--Muted)",
              marginBottom: 4,
            }}
          >
            <span>Progress</span>
            <span>{progress}%</span>
          </div>
          <div
            style={{
              height: 4,
              borderRadius: 99,
              background: "var(--Border)",
              overflow: "hidden",
            }}
          >
            <div
              style={{
                height: "100%",
                width: `${progress}%`,
                borderRadius: 99,
                background: "var(--Primary)",
                transition: "width 0.4s ease",
              }}
            />
          </div>
        </div>
      )}

      {/* Notes */}
      {isExpanded && goal.notes && (
        <p style={{ margin: "12px 0 0", fontSize: 13, color: "var(--Muted)", lineHeight: 1.5 }}>
          {goal.notes}
        </p>
      )}

      {/* Tasks */}
      {isExpanded && (
        <div onClick={(e) => e.stopPropagation()}>
          {loadingTasks ? (
            <p style={{ color: "var(--Muted)", fontSize: 13, padding: "12px 0" }}>
              Loading tasks…
            </p>
          ) : (
            <TaskList tasks={tasks} />
          )}
        </div>
      )}
    </div>
  );
}

/* ─── Main Dashboard ─── */

export default function Dashboard() {
  const [goals, setGoals] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Track expanded goal and its tasks
  const [expandedGoalId, setExpandedGoalId] = useState(null);
  const [taskCache, setTaskCache] = useState({}); // { goalId: tasks[] }
  const [loadingTasks, setLoadingTasks] = useState(false);

  const token = localStorage.getItem("agp_auth_token");

  /* Fetch all goals */
  const fetchGoals = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await apiFetch("/goals/", token);
      setGoals(data);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    fetchGoals();
  }, [fetchGoals]);

  /* Fetch tasks for a goal (with cache) */
  const fetchTasks = useCallback(
    async (goalId) => {
      if (taskCache[goalId]) return; // already cached
      setLoadingTasks(true);
      try {
        const data = await apiFetch(`/goals/${goalId}/tasks`, token);
        setTaskCache((prev) => ({ ...prev, [goalId]: data.tasks || [] }));
      } catch (e) {
        console.error("Failed to fetch tasks:", e);
        setTaskCache((prev) => ({ ...prev, [goalId]: [] }));
      } finally {
        setLoadingTasks(false);
      }
    },
    [token, taskCache]
  );

  /* Toggle expand/collapse */
  const handleToggle = (goalId) => {
    if (expandedGoalId === goalId) {
      setExpandedGoalId(null);
    } else {
      setExpandedGoalId(goalId);
      fetchTasks(goalId);
    }
  };

  /* Summary stats */
  const totalGoals = goals.length;
  const completedGoals = goals.filter((g) => g.status === "completed").length;
  const totalTasks = goals.reduce((sum, g) => sum + (g.task_count || 0), 0);

  return (
    <section style={{ maxWidth: 720, margin: "0 auto" }}>
      {/* Page Header */}
      <div style={{ marginBottom: 24 }}>
        <h2 className="PanelTitle" style={{ margin: "0 0 4px" }}>
          My Goals
        </h2>
        <p className="PanelText" style={{ fontSize: 14 }}>
          Track your progress and stay on course.
        </p>
      </div>

      {/* Stats Row */}
      {!loading && goals.length > 0 && (
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(3, 1fr)",
            gap: 12,
            marginBottom: 20,
          }}
        >
          {[
            { label: "Goals", value: totalGoals, color: "var(--Primary)" },
            { label: "Completed", value: completedGoals, color: "#059669" },
            { label: "Total Tasks", value: totalTasks, color: "var(--Accent)" },
          ].map((stat) => (
            <div
              key={stat.label}
              className="Panel"
              style={{ textAlign: "center", padding: "16px 12px" }}
            >
              <div style={{ fontSize: 28, fontWeight: 800, color: stat.color }}>{stat.value}</div>
              <div style={{ fontSize: 11, color: "var(--Muted)", fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.5px", marginTop: 2 }}>
                {stat.label}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Content */}
      {loading && <LoadingState />}
      {error && <ErrorState message={error} onRetry={fetchGoals} />}
      {!loading && !error && goals.length === 0 && <EmptyState onRefresh={fetchGoals} />}

      {!loading && !error && goals.length > 0 && (
        <div style={{ display: "grid", gap: 12 }}>
          {goals.map((goal) => (
            <GoalCard
              key={goal.id}
              goal={goal}
              isExpanded={expandedGoalId === goal.id}
              onToggle={() => handleToggle(goal.id)}
              tasks={taskCache[goal.id] || []}
              loadingTasks={loadingTasks && expandedGoalId === goal.id}
            />
          ))}
        </div>
      )}
    </section>
  );
}
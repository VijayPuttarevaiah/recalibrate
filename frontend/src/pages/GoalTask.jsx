/**
 * @file GoalTasksPage.jsx
 * @description Full tasks view with REPLAN functionality.
 * - Detects missed tasks and shows replan banner
 * - Allows marking tasks as completed/pending
 * - Shows trade-off explanation after replan
 * - Adjustment history panel
 */
import React, { useState, useEffect, useCallback } from "react";
import { useParams, useLocation, useNavigate } from "react-router-dom";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

/* ───── API helpers ───── */

async function apiFetch(url, token, options = {}) {
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

/* ───── Design tokens (matching your system) ───── */

const statusColor = (s) => {
  switch (s?.toLowerCase()) {
    case "completed":   return "#059669";
    case "in_progress": return "#6366F1";
    case "missed":      return "#DC2626";
    case "skipped":     return "#9CA3AF";
    default:            return "#F59E0B";
  }
};
const statusBg = (s) => {
  switch (s?.toLowerCase()) {
    case "completed":   return "rgba(5,150,105,0.09)";
    case "in_progress": return "rgba(99,102,241,0.09)";
    case "missed":      return "rgba(220,38,38,0.09)";
    case "skipped":     return "rgba(156,163,175,0.09)";
    default:            return "rgba(245,158,11,0.09)";
  }
};
const formatDate = (d) =>
  d
    ? new Date(d).toLocaleDateString("en-US", {
        month: "short",
        day: "numeric",
        year: "numeric",
      })
    : "—";

/* ───── Reusable components ───── */

function StatusBadge({ status }) {
  return (
    <span
      style={{
        display: "inline-flex",
        alignItems: "center",
        fontSize: 11,
        fontWeight: 700,
        textTransform: "uppercase",
        letterSpacing: "0.5px",
        padding: "4px 12px",
        borderRadius: 99,
        color: statusColor(status),
        background: statusBg(status),
        border: `1px solid ${statusColor(status)}30`,
        whiteSpace: "nowrap",
      }}
    >
      {status?.replace(/_/g, " ") || "pending"}
    </span>
  );
}

function FilterPill({ label, active, onClick, count }) {
  return (
    <button
      onClick={onClick}
      style={{
        padding: "6px 14px",
        borderRadius: 99,
        border: active
          ? "1.5px solid var(--Primary)"
          : "1px solid var(--Border)",
        background: active ? "var(--Primary)" : "#fff",
        color: active ? "#fff" : "var(--Muted)",
        fontSize: 13,
        fontWeight: 600,
        cursor: "pointer",
        transition: "all 0.18s ease",
        display: "inline-flex",
        alignItems: "center",
        gap: 6,
        whiteSpace: "nowrap",
      }}
    >
      {label}
      {count !== undefined && (
        <span
          style={{
            background: active ? "rgba(255,255,255,0.25)" : "var(--Border)",
            color: active ? "#fff" : "var(--Muted)",
            padding: "1px 7px",
            borderRadius: 99,
            fontSize: 11,
            fontWeight: 700,
          }}
        >
          {count}
        </span>
      )}
    </button>
  );
}

/* ───── Replan Banner ───── */

function ReplanBanner({ replanStatus, onReplan, replanning }) {
  if (!replanStatus || !replanStatus.needs_replan) return null;

  return (
    <div
      style={{
        background: "linear-gradient(135deg, #FEF3C7 0%, #FDE68A 100%)",
        border: "1px solid #F59E0B55",
        borderRadius: 16,
        padding: "18px 22px",
        marginBottom: 20,
        display: "flex",
        alignItems: "center",
        flexWrap: "wrap",
        gap: 14,
      }}
    >
      <div
        style={{
          width: 42,
          height: 42,
          borderRadius: 12,
          background: "rgba(245,158,11,0.15)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontSize: 20,
          flexShrink: 0,
        }}
      >
        ⚠️
      </div>
      <div style={{ flex: "1 1 200px", minWidth: 0 }}>
        <p
          style={{
            margin: 0,
            fontWeight: 700,
            fontSize: 14,
            color: "#92400E",
          }}
        >
          You're {replanStatus.missed_count} tasks behind schedule
        </p>
        <p
          style={{
            margin: "4px 0 0",
            fontSize: 12,
            color: "#A16207",
            lineHeight: 1.5,
          }}
        >
          {replanStatus.completed_count} of {replanStatus.total_past_tasks} past
          tasks completed. Want to adjust your plan?
        </p>
      </div>
      <button
        onClick={onReplan}
        disabled={replanning}
        style={{
          padding: "10px 22px",
          borderRadius: 12,
          border: "none",
          background: "#F59E0B",
          color: "#fff",
          fontWeight: 700,
          fontSize: 13,
          cursor: replanning ? "not-allowed" : "pointer",
          opacity: replanning ? 0.7 : 1,
          transition: "all 0.2s ease",
          boxShadow: "0 4px 8px -2px rgba(245,158,11,0.4)",
          display: "flex",
          alignItems: "center",
          gap: 8,
          whiteSpace: "nowrap",
          flexShrink: 0,
        }}
      >
        {replanning ? (
          <>
            <span
              style={{
                display: "inline-block",
                width: 14,
                height: 14,
                border: "2px solid rgba(255,255,255,0.3)",
                borderTopColor: "#fff",
                borderRadius: "50%",
                animation: "spin 0.8s linear infinite",
              }}
            />
            Adjusting…
          </>
        ) : (
          "Adjust My Plan"
        )}
      </button>
    </div>
  );
}

/* ───── Replan Explanation Modal ───── */

function ReplanExplanation({ result, onDismiss }) {
  if (!result) return null;

  return (
    <div
      style={{
        background: "linear-gradient(135deg, #ECFDF5 0%, #D1FAE5 100%)",
        border: "1px solid #05966940",
        borderRadius: 16,
        padding: "22px",
        marginBottom: 20,
        position: "relative",
      }}
    >
      <button
        onClick={onDismiss}
        style={{
          position: "absolute",
          top: 12,
          right: 14,
          background: "none",
          border: "none",
          fontSize: 18,
          cursor: "pointer",
          color: "#065F46",
          opacity: 0.5,
          lineHeight: 1,
        }}
      >
        ✕
      </button>

      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 10,
          marginBottom: 14,
        }}
      >
        <div
          style={{
            width: 36,
            height: 36,
            borderRadius: 10,
            background: "rgba(5,150,105,0.12)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            fontSize: 18,
          }}
        >
          ✅
        </div>
        <h3
          style={{
            margin: 0,
            fontWeight: 700,
            fontSize: 15,
            color: "#065F46",
          }}
        >
          Plan Adjusted Successfully
        </h3>
      </div>

      <p
        style={{
          margin: "0 0 16px",
          fontSize: 13,
          color: "#047857",
          lineHeight: 1.7,
        }}
      >
        {result.explanation}
      </p>

      {/* Stats row */}
      <div
        style={{
          display: "flex",
          flexWrap: "wrap",
          gap: 10,
        }}
      >
        {[
          {
            label: "Missed Found",
            value: result.stats?.missed_tasks_found,
            color: "#DC2626",
          },
          {
            label: "Old Removed",
            value: result.stats?.old_future_tasks_removed,
            color: "#9CA3AF",
          },
          {
            label: "New Created",
            value: result.stats?.new_tasks_generated,
            color: "#059669",
          },
          {
            label: "Days Left",
            value: result.stats?.remaining_days,
            color: "#6366F1",
          },
        ].map((stat) => (
          <div
            key={stat.label}
            style={{
              background: "#fff",
              border: "1px solid #D1FAE5",
              borderRadius: 10,
              padding: "8px 14px",
              textAlign: "center",
              flex: "1 1 80px",
            }}
          >
            <div
              style={{ fontSize: 20, fontWeight: 800, color: stat.color }}
            >
              {stat.value ?? "—"}
            </div>
            <div
              style={{
                fontSize: 9,
                fontWeight: 700,
                textTransform: "uppercase",
                letterSpacing: "0.4px",
                color: "#6B7280",
                marginTop: 2,
              }}
            >
              {stat.label}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

/* ───── Adjustment History Panel ───── */

function AdjustmentHistory({ history, show, onToggle }) {
  if (!history || history.length === 0) return null;

  return (
    <div style={{ marginBottom: 20 }}>
      <button
        onClick={onToggle}
        className="ButtonGhost"
        style={{
          border: "1px solid var(--Border)",
          borderRadius: 10,
          padding: "7px 14px",
          fontSize: 12,
          fontWeight: 600,
          cursor: "pointer",
          display: "inline-flex",
          alignItems: "center",
          gap: 6,
          marginBottom: show ? 12 : 0,
        }}
      >
        🕘 Adjustment History ({history.length})
        <span style={{ fontSize: 10 }}>{show ? "▲" : "▼"}</span>
      </button>

      {show && (
        <div style={{ display: "grid", gap: 10 }}>
          {history.map((adj) => (
            <div
              key={adj.id}
              style={{
                background: "#fff",
                border: "1px solid var(--Border)",
                borderRadius: 14,
                padding: "14px 18px",
                borderLeft: "3px solid #6366F1",
              }}
            >
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  flexWrap: "wrap",
                  gap: 8,
                  marginBottom: 8,
                }}
              >
                <span
                  style={{ fontSize: 12, fontWeight: 700, color: "var(--Text)" }}
                >
                  {adj.missed_task_count} missed →{" "}
                  {adj.tasks_created} new tasks
                </span>
                <span
                  style={{
                    fontSize: 11,
                    color: "var(--Muted)",
                    whiteSpace: "nowrap",
                  }}
                >
                  {new Date(adj.created_at).toLocaleDateString("en-US", {
                    month: "short",
                    day: "numeric",
                    hour: "2-digit",
                    minute: "2-digit",
                  })}
                </span>
              </div>
              <p
                style={{
                  margin: 0,
                  fontSize: 12,
                  color: "var(--Muted)",
                  lineHeight: 1.6,
                }}
              >
                {adj.explanation}
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

/* ───── Task Card with completion toggle ───── */

function TaskCard({ task, onToggleStatus }) {
  const [hovered, setHovered] = useState(false);
  const [toggling, setToggling] = useState(false);
  const accent = statusColor(task.status);
  const isCompleted = task.status === "completed";
  const isMissed = task.status === "missed";

  const handleToggle = async () => {
    if (toggling) return;
    setToggling(true);
    const newStatus = isCompleted ? "pending" : "completed";
    await onToggleStatus(task.id, newStatus);
    setToggling(false);
  };

  return (
    <div
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      style={{
        background: isMissed ? "#FEF2F2" : "#fff",
        border: "1px solid var(--Border)",
        borderRadius: 14,
        padding: "14px 18px",
        display: "flex",
        alignItems: "flex-start",
        gap: 12,
        boxShadow: hovered
          ? "0 4px 12px -2px rgba(0,0,0,0.08)"
          : "0 1px 4px -1px rgba(0,0,0,0.06)",
        borderLeft: `3px solid ${accent}`,
        transition: "box-shadow 0.2s ease",
        flexWrap: "wrap",
        opacity: isMissed ? 0.7 : 1,
      }}
    >
      {/* Completion checkbox */}
      <button
        onClick={handleToggle}
        disabled={isMissed || toggling}
        title={
          isMissed
            ? "This task was missed"
            : isCompleted
            ? "Mark as pending"
            : "Mark as completed"
        }
        style={{
          width: 22,
          height: 22,
          borderRadius: 6,
          border: `2px solid ${isCompleted ? "#059669" : isMissed ? "#DC2626" : "var(--Border)"}`,
          background: isCompleted
            ? "#059669"
            : isMissed
            ? "#DC262620"
            : "transparent",
          cursor: isMissed ? "not-allowed" : "pointer",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontSize: 12,
          color: "#fff",
          flexShrink: 0,
          marginTop: 2,
          transition: "all 0.15s ease",
        }}
      >
        {isCompleted && "✓"}
        {isMissed && (
          <span style={{ color: "#DC2626", fontSize: 11 }}>✕</span>
        )}
      </button>

      {/* Title + description */}
      <div
        style={{
          display: "flex",
          alignItems: "flex-start",
          gap: 12,
          flex: "1 1 200px",
          minWidth: 0,
        }}
      >
        <div style={{ minWidth: 0, flex: 1 }}>
          <p
            style={{
              margin: 0,
              fontWeight: 600,
              fontSize: 14,
              color: isCompleted ? "var(--Muted)" : "var(--Text)",
              wordBreak: "break-word",
              textDecoration: isCompleted ? "line-through" : "none",
            }}
          >
            {task.title}
          </p>
          {task.description && (
            <p
              style={{
                margin: "4px 0 0",
                fontSize: 12,
                color: "var(--Muted)",
                lineHeight: 1.5,
                display: "-webkit-box",
                WebkitLineClamp: 2,
                WebkitBoxOrient: "vertical",
                overflow: "hidden",
              }}
            >
              {task.description}
            </p>
          )}
        </div>
      </div>

      {/* Date + badge */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 10,
          flexShrink: 0,
          marginLeft: "auto",
        }}
      >
        {task.due_date && (
          <span
            style={{
              fontSize: 12,
              color: "var(--Muted)",
              whiteSpace: "nowrap",
            }}
          >
            📅 {formatDate(task.due_date)}
          </span>
        )}
        <StatusBadge status={task.status} />
      </div>
    </div>
  );
}

/* ───── Main Page Component ───── */

export default function GoalTasksPage() {
  const { goalId } = useParams();
  const { state } = useLocation();
  const navigate = useNavigate();
  const token = localStorage.getItem("agp_auth_token");

  const [goal, setGoal] = useState(state?.goal || null);
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filter, setFilter] = useState("all");
  const [search, setSearch] = useState("");

  // Replan state
  const [replanStatus, setReplanStatus] = useState(null);
  const [replanning, setReplanning] = useState(false);
  const [replanResult, setReplanResult] = useState(null);
  const [adjustmentHistory, setAdjustmentHistory] = useState([]);
  const [showHistory, setShowHistory] = useState(false);

  /* ── Fetch tasks ── */
  const fetchTasks = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await apiFetch(`/goals/${goalId}/tasks`, token);
      setGoal(data);
      setTasks(data.tasks || []);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, [goalId, token]);

  /* ── Check replan status ── */
  const checkReplan = useCallback(async () => {
    try {
      const data = await apiFetch(
        `/goals/${goalId}/replan/check?threshold=3`,
        token
      );
      setReplanStatus(data);
    } catch (e) {
      console.warn("Replan check failed:", e.message);
    }
  }, [goalId, token]);

  /* ── Fetch adjustment history ── */
  const fetchHistory = useCallback(async () => {
    try {
      const data = await apiFetch(
        `/goals/${goalId}/replan/history`,
        token
      );
      setAdjustmentHistory(data);
    } catch (e) {
      console.warn("History fetch failed:", e.message);
    }
  }, [goalId, token]);

  /* ── Initial load ── */
  useEffect(() => {
    fetchTasks();
    checkReplan();
    fetchHistory();
  }, [fetchTasks, checkReplan, fetchHistory]);

  /* ── Trigger replan ── */
  const handleReplan = async () => {
    setReplanning(true);
    setReplanResult(null);
    try {
      const data = await apiFetch(`/goals/${goalId}/replan`, token, {
        method: "POST",
      });
      setReplanResult(data);
      setReplanStatus(null); // dismiss the banner

      // Refresh tasks + history
      await fetchTasks();
      await fetchHistory();
    } catch (e) {
      setError(`Replan failed: ${e.message}`);
    } finally {
      setReplanning(false);
    }
  };

  /* ── Toggle task status ── */
  const handleToggleStatus = async (taskId, newStatus) => {
    try {
      await apiFetch(`/tasks/${taskId}/status`, token, {
        method: "PATCH",
        body: JSON.stringify({ status: newStatus }),
      });
      // Update local state
      setTasks((prev) =>
        prev.map((t) => (t.id === taskId ? { ...t, status: newStatus } : t))
      );
      // Re-check if replan is needed
      await checkReplan();
    } catch (e) {
      console.error("Toggle failed:", e.message);
    }
  };

  /* ── Filter + search ── */
  const visible = tasks.filter((t) => {
    const matchFilter = filter === "all" || t.status === filter;
    const matchSearch = t.title
      ?.toLowerCase()
      .includes(search.toLowerCase());
    return matchFilter && matchSearch;
  });

  const counts = {
    all: tasks.length,
    pending: tasks.filter((t) => t.status === "pending").length,
    completed: tasks.filter((t) => t.status === "completed").length,
    missed: tasks.filter((t) => t.status === "missed").length,
    in_progress: tasks.filter((t) => t.status === "in_progress").length,
  };

  const completedCount = counts.completed;
  const progress =
    tasks.length > 0
      ? Math.round((completedCount / tasks.length) * 100)
      : 0;
  const accent = statusColor(goal?.status);

  return (
    <section
      style={{
        maxWidth: 760,
        margin: "0 auto",
        padding: "32px 24px",
        minHeight: "calc(100vh - 64px)",
      }}
    >
      {/* Spinner keyframe (for replan button) */}
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>

      {/* Back button */}
      <button
        onClick={() => navigate(-1)}
        className="ButtonGhost"
        style={{
          border: "1px solid var(--Border)",
          borderRadius: 10,
          padding: "8px 16px",
          fontSize: 13,
          cursor: "pointer",
          display: "inline-flex",
          alignItems: "center",
          gap: 6,
          marginBottom: 24,
        }}
      >
        ← Back to Goals
      </button>

      {/* Goal Header Card */}
      {goal && (
        <div
          className="Panel"
          style={{
            marginBottom: 24,
            borderLeft: `4px solid ${accent}`,
            position: "relative",
            overflow: "hidden",
          }}
        >
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "flex-start",
              flexWrap: "wrap",
              gap: 12,
            }}
          >
            <div style={{ flex: "1 1 250px", minWidth: 0 }}>
              <h1
                style={{
                  margin: "0 0 6px",
                  fontSize: 22,
                  fontWeight: 800,
                  color: "var(--Text)",
                  letterSpacing: "-0.4px",
                  wordBreak: "break-word",
                }}
              >
                {goal.title}
              </h1>
              <div
                style={{
                  display: "flex",
                  flexWrap: "wrap",
                  gap: "8px 14px",
                  fontSize: 13,
                  color: "var(--Muted)",
                  alignItems: "center",
                }}
              >
                {goal.category && (
                  <span
                    style={{
                      fontWeight: 700,
                      textTransform: "uppercase",
                      fontSize: 11,
                      color: accent,
                      letterSpacing: "0.4px",
                    }}
                  >
                    {goal.category.replace(/_/g, " ")}
                  </span>
                )}
                <span>
                  📅 {formatDate(goal.start_date)} →{" "}
                  {formatDate(goal.end_date)}
                </span>
              </div>
            </div>
            <StatusBadge status={goal.status} />
          </div>

          {goal.notes && (
            <p
              style={{
                margin: "12px 0 0",
                fontSize: 13,
                color: "var(--Muted)",
                lineHeight: 1.6,
              }}
            >
              {goal.notes}
            </p>
          )}

          {/* Progress */}
          <div style={{ marginTop: 18 }}>
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                flexWrap: "wrap",
                fontSize: 12,
                color: "var(--Muted)",
                marginBottom: 6,
                gap: 4,
              }}
            >
              <span style={{ fontWeight: 600 }}>Overall Progress</span>
              <span style={{ fontWeight: 700, color: accent }}>
                {progress}% · {completedCount}/{tasks.length} tasks done
                {counts.missed > 0 && (
                  <span style={{ color: "#DC2626", marginLeft: 8 }}>
                    · {counts.missed} missed
                  </span>
                )}
              </span>
            </div>
            <div
              style={{
                height: 6,
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
                  background: accent,
                  transition: "width 0.6s ease",
                }}
              />
            </div>
          </div>
        </div>
      )}

      {/* ── Replan Banner ── */}
      <ReplanBanner
        replanStatus={replanStatus}
        onReplan={handleReplan}
        replanning={replanning}
      />

      {/* ── Replan Explanation (shown after successful replan) ── */}
      <ReplanExplanation
        result={replanResult}
        onDismiss={() => setReplanResult(null)}
      />

      {/* ── Adjustment History ── */}
      <AdjustmentHistory
        history={adjustmentHistory}
        show={showHistory}
        onToggle={() => setShowHistory((prev) => !prev)}
      />

      {/* Search + Filters */}
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          gap: 12,
          marginBottom: 20,
        }}
      >
        <input
          className="Input"
          placeholder="Search tasks…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          style={{ width: "100%", padding: "10px 14px", fontSize: 13 }}
        />
        <div
          style={{
            display: "flex",
            gap: 8,
            flexWrap: "wrap",
          }}
        >
          {[
            { key: "all", label: "All" },
            { key: "pending", label: "Pending" },
            { key: "in_progress", label: "In Progress" },
            { key: "completed", label: "Completed" },
            { key: "missed", label: "Missed" },
          ].map(({ key, label }) => (
            <FilterPill
              key={key}
              label={label}
              count={counts[key]}
              active={filter === key}
              onClick={() => setFilter(key)}
            />
          ))}
        </div>
      </div>

      {/* Task List */}
      {loading && (
        <div
          style={{
            textAlign: "center",
            padding: 48,
            color: "var(--Muted)",
          }}
        >
          Loading tasks…
        </div>
      )}
      {error && (
        <div
          className="Alert"
          style={{
            display: "flex",
            alignItems: "center",
            flexWrap: "wrap",
            gap: 12,
          }}
        >
          <span style={{ flex: 1 }}>{error}</span>
          <button
            className="Button"
            onClick={() => {
              setError(null);
              fetchTasks();
            }}
            style={{ fontSize: 12, padding: "4px 14px" }}
          >
            Retry
          </button>
        </div>
      )}

      {!loading && !error && (
        <>
          {visible.length === 0 ? (
            <div
              style={{
                textAlign: "center",
                padding: "48px 24px",
                color: "var(--Muted)",
              }}
            >
              <div
                style={{ fontSize: 40, marginBottom: 12, opacity: 0.3 }}
              >
                📭
              </div>
              <p style={{ margin: 0, fontWeight: 600 }}>
                No tasks match your filter.
              </p>
            </div>
          ) : (
            <div style={{ display: "grid", gap: 10 }}>
              {visible.map((task) => (
                <TaskCard
                  key={task.id}
                  task={task}
                  onToggleStatus={handleToggleStatus}
                />
              ))}
            </div>
          )}
        </>
      )}
    </section>
  );
}
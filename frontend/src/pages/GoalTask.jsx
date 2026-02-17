/**
 * @file GoalTasksPage.jsx
 * @description Full tasks view for a specific goal.
 * Navigated to from Dashboard when a GoalCard is clicked.
 * Fully responsive and aligned.
 */
import React, { useState, useEffect, useCallback } from "react";
import { useParams, useLocation, useNavigate } from "react-router-dom";

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

const statusColor = (s) => {
  switch (s?.toLowerCase()) {
    case "completed":   return "#059669";
    case "in_progress": return "#6366F1";
    default:            return "#F59E0B";
  }
};
const statusBg = (s) => {
  switch (s?.toLowerCase()) {
    case "completed":   return "rgba(5,150,105,0.09)";
    case "in_progress": return "rgba(99,102,241,0.09)";
    default:            return "rgba(245,158,11,0.09)";
  }
};
const formatDate = (d) =>
  d ? new Date(d).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" }) : "—";

function StatusBadge({ status }) {
  return (
    <span style={{
      display: "inline-flex", alignItems: "center",
      fontSize: 11, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.5px",
      padding: "4px 12px", borderRadius: 99,
      color: statusColor(status), background: statusBg(status),
      border: `1px solid ${statusColor(status)}30`,
      whiteSpace: "nowrap",
    }}>
      {status?.replace(/_/g, " ") || "pending"}
    </span>
  );
}

function TaskCard({ task }) {
  const [hovered, setHovered] = useState(false);
  const accent = statusColor(task.status);

  return (
    <div
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      style={{
        background: "#fff",
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
        /* Responsive: stack on small screens */
        flexWrap: "wrap",
      }}
    >
      {/* Left: dot + title */}
      <div style={{ display: "flex", alignItems: "flex-start", gap: 12, flex: "1 1 200px", minWidth: 0 }}>
        <div style={{
          width: 8, height: 8, borderRadius: "50%",
          background: accent, flexShrink: 0,
          marginTop: 5,
        }} />
        <div style={{ minWidth: 0, flex: 1 }}>
          <p style={{
            margin: 0, fontWeight: 600, fontSize: 14,
            color: "var(--Text)",
            wordBreak: "break-word",
          }}>{task.title}</p>
          {task.description && (
            <p style={{
              margin: "4px 0 0", fontSize: 12, color: "var(--Muted)",
              lineHeight: 1.5,
              display: "-webkit-box",
              WebkitLineClamp: 2,
              WebkitBoxOrient: "vertical",
              overflow: "hidden",
            }}>{task.description}</p>
          )}
        </div>
      </div>

      {/* Right: date + badge */}
      <div style={{
        display: "flex", alignItems: "center", gap: 10, flexShrink: 0,
        /* On wrap, push to the right */
        marginLeft: "auto",
      }}>
        {task.due_date && (
          <span style={{ fontSize: 12, color: "var(--Muted)", whiteSpace: "nowrap" }}>
            📅 {formatDate(task.due_date)}
          </span>
        )}
        <StatusBadge status={task.status} />
      </div>
    </div>
  );
}

function FilterPill({ label, active, onClick, count }) {
  return (
    <button
      onClick={onClick}
      style={{
        padding: "6px 14px", borderRadius: 99,
        border: active ? "1.5px solid var(--Primary)" : "1px solid var(--Border)",
        background: active ? "var(--Primary)" : "#fff",
        color: active ? "#fff" : "var(--Muted)",
        fontSize: 13, fontWeight: 600, cursor: "pointer",
        transition: "all 0.18s ease",
        display: "inline-flex", alignItems: "center", gap: 6,
        whiteSpace: "nowrap",
      }}
    >
      {label}
      {count !== undefined && (
        <span style={{
          background: active ? "rgba(255,255,255,0.25)" : "var(--Border)",
          color: active ? "#fff" : "var(--Muted)",
          padding: "1px 7px", borderRadius: 99, fontSize: 11, fontWeight: 700,
        }}>{count}</span>
      )}
    </button>
  );
}

export default function GoalTasksPage() {
  const { goalId }  = useParams();
  const { state }   = useLocation();
  const navigate    = useNavigate();
  const token       = localStorage.getItem("agp_auth_token");

  const [goal, setGoal]     = useState(state?.goal || null);
  const [tasks, setTasks]   = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError]   = useState(null);
  const [filter, setFilter] = useState("all");
  const [search, setSearch] = useState("");

  const fetchTasks = useCallback(async () => {
    setLoading(true); setError(null);
    try {
      const data = await apiFetch(`/goals/${goalId}/tasks`, token);
      setTasks(data.tasks || []);
    } catch (e) { setError(e.message); }
    finally { setLoading(false); }
  }, [goalId, token]);

  useEffect(() => { fetchTasks(); }, [fetchTasks]);

  // Filter + search
  const visible = tasks.filter((t) => {
    const matchFilter = filter === "all" || t.status === filter;
    const matchSearch = t.title?.toLowerCase().includes(search.toLowerCase());
    return matchFilter && matchSearch;
  });

  const counts = {
    all:         tasks.length,
    pending:     tasks.filter((t) => t.status === "pending").length,
    in_progress: tasks.filter((t) => t.status === "in_progress").length,
    completed:   tasks.filter((t) => t.status === "completed").length,
  };

  const completedCount = counts.completed;
  const progress = tasks.length > 0 ? Math.round((completedCount / tasks.length) * 100) : 0;
  const accent   = statusColor(goal?.status);

  return (
    <section style={{ maxWidth: 760, margin: "0 auto", padding: "32px 24px", minHeight: "calc(100vh - 64px)" }}>
      {/* Back button */}
      <button
        onClick={() => navigate(-1)}
        className="ButtonGhost"
        style={{
          border: "1px solid var(--Border)",
          borderRadius: 10, padding: "8px 16px",
          fontSize: 13, cursor: "pointer",
          display: "inline-flex", alignItems: "center", gap: 6, marginBottom: 24,
        }}
      >
        ← Back to Goals
      </button>

      {/* Goal Header Card */}
      {goal && (
        <div className="Panel" style={{ marginBottom: 24, borderLeft: `4px solid ${accent}`, position: "relative", overflow: "hidden" }}>
          {/* Title row - wraps on mobile */}
          <div style={{
            display: "flex", justifyContent: "space-between", alignItems: "flex-start",
            flexWrap: "wrap", gap: 12,
          }}>
            <div style={{ flex: "1 1 250px", minWidth: 0 }}>
              <h1 style={{
                margin: "0 0 6px", fontSize: 22, fontWeight: 800,
                color: "var(--Text)", letterSpacing: "-0.4px",
                wordBreak: "break-word",
              }}>
                {goal.title}
              </h1>
              <div style={{
                display: "flex", flexWrap: "wrap", gap: "8px 14px",
                fontSize: 13, color: "var(--Muted)", alignItems: "center",
              }}>
                {goal.category && (
                  <span style={{
                    fontWeight: 700, textTransform: "uppercase", fontSize: 11,
                    color: accent, letterSpacing: "0.4px",
                  }}>
                    {goal.category.replace(/_/g, " ")}
                  </span>
                )}
                <span>📅 {formatDate(goal.start_date)} → {formatDate(goal.end_date)}</span>
              </div>
            </div>
            <StatusBadge status={goal.status} />
          </div>

          {goal.notes && (
            <p style={{ margin: "12px 0 0", fontSize: 13, color: "var(--Muted)", lineHeight: 1.6 }}>
              {goal.notes}
            </p>
          )}

          {/* Progress */}
          <div style={{ marginTop: 18 }}>
            <div style={{
              display: "flex", justifyContent: "space-between", flexWrap: "wrap",
              fontSize: 12, color: "var(--Muted)", marginBottom: 6, gap: 4,
            }}>
              <span style={{ fontWeight: 600 }}>Overall Progress</span>
              <span style={{ fontWeight: 700, color: accent }}>{progress}% · {completedCount}/{tasks.length} tasks done</span>
            </div>
            <div style={{ height: 6, borderRadius: 99, background: "var(--Border)", overflow: "hidden" }}>
              <div style={{
                height: "100%", width: `${progress}%`, borderRadius: 99,
                background: accent, transition: "width 0.6s ease",
              }} />
            </div>
          </div>
        </div>
      )}

      {/* Search + Filters - stacks vertically on mobile */}
      <div style={{
        display: "flex", flexDirection: "column", gap: 12,
        marginBottom: 20,
      }}>
        <input
          className="Input"
          placeholder="Search tasks…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          style={{ width: "100%", padding: "10px 14px", fontSize: 13 }}
        />
        <div style={{
          display: "flex", gap: 8, flexWrap: "wrap",
        }}>
          {[
            { key: "all",         label: "All" },
            { key: "pending",     label: "Pending" },
            { key: "in_progress", label: "In Progress" },
            { key: "completed",   label: "Completed" },
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
        <div style={{ textAlign: "center", padding: 48, color: "var(--Muted)" }}>Loading tasks…</div>
      )}
      {error && (
        <div className="Alert" style={{ display: "flex", alignItems: "center", flexWrap: "wrap", gap: 12 }}>
          <span style={{ flex: 1 }}>{error}</span>
          <button className="Button" onClick={fetchTasks} style={{ fontSize: 12, padding: "4px 14px" }}>Retry</button>
        </div>
      )}

      {!loading && !error && (
        <>
          {visible.length === 0 ? (
            <div style={{ textAlign: "center", padding: "48px 24px", color: "var(--Muted)" }}>
              <div style={{ fontSize: 40, marginBottom: 12, opacity: 0.3 }}>📭</div>
              <p style={{ margin: 0, fontWeight: 600 }}>No tasks match your filter.</p>
            </div>
          ) : (
            <div style={{ display: "grid", gap: 10 }}>
              {visible.map((task) => (
                <TaskCard key={task.id} task={task} />
              ))}
            </div>
          )}
        </>
      )}
    </section>
  );
}
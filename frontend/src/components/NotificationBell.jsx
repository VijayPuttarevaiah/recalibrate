import { useState, useEffect, useRef } from "react";
import { use_auth } from "../hooks/use_auth.js";
import { useParams } from "react-router-dom";  

const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export default function NotificationBell() {
  const { user_id: userId } = use_auth();
  const { goalId } = useParams();  
  const [notifications, setNotifications] = useState([]);
  const [open, setOpen] = useState(false);
  const [triggering, setTriggering] = useState(false);
  const dropdownRef = useRef(null);

  const unread = notifications.filter((n) => !n.is_read).length;

  // ── Fetch notifications ─────────────────────────────────────────────────── 
  const fetchNotifications = async () => {
    if (!userId) return;
    try {
      const url = goalId
        ? `${API_BASE}/notifications/${userId}?goal_id=${goalId}`
        : `${API_BASE}/notifications/${userId}`;
      const res = await fetch(url);
      const json = await res.json();
      if (json.success) setNotifications(json.data || []);
    } catch (err) {
      console.error("Failed to fetch notifications:", err);
    }
};

  // Poll every 30 seconds so new cron-created notifications appear automatically
  useEffect(() => {
    fetchNotifications();
    const interval = setInterval(fetchNotifications, 30_000);
    return () => clearInterval(interval);
  }, [userId]);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handler = (e) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  // ── Mark as read ──────────────────────────────────────────────────────────
  const markRead = async (id) => {
    try {
      await fetch(`${API_BASE}/notifications/${id}/read`, { method: "PATCH" });
      setNotifications((prev) =>
        prev.map((n) => (n.id === id ? { ...n, is_read: true } : n))
      );
    } catch (err) {
      console.error("Failed to mark notification as read:", err);
    }
  };

  const markAllRead = () => {
    notifications.filter((n) => !n.is_read).forEach((n) => markRead(n.id));
  };

  // ── Trigger cron manually (demo button) ───────────────────────────────────
  const triggerCheck = async () => {
    setTriggering(true);
    try {
      await fetch(`${API_BASE}/notifications/trigger-check`, { method: "POST" });
      await fetchNotifications();
    } catch (err) {
      console.error("Trigger failed:", err);
    } finally {
      setTriggering(false);
    }
  };

  // ── Badge style based on notification type ────────────────────────────────
  const getBadgeStyle = (title) => {
    if (title?.includes("Overdue"))   return { bg: "#FEE2E2", color: "#DC2626", dot: "#DC2626" };
    if (title?.includes("Deadline"))  return { bg: "#FEF3C7", color: "#D97706", dot: "#D97706" };
    if (title?.includes("Completed")) return { bg: "#D1FAE5", color: "#059669", dot: "#059669" };
    return { bg: "#EFF6FF", color: "#2563EB", dot: "#2563EB" };
  };

  const formatTime = (iso) => {
    if (!iso) return "";
    return new Date(iso).toLocaleString(undefined, {
      month: "short", day: "numeric",
      hour: "2-digit", minute: "2-digit",
    });
  };

  return (
    <div ref={dropdownRef} style={{ position: "relative", display: "inline-block" }}>

      {/* ── Bell button ── */}
      <button
        onClick={() => setOpen((o) => !o)}
        style={{
          position: "relative", background: "none", border: "none",
          cursor: "pointer", padding: "6px", borderRadius: "8px",
        }}
        title="Notifications"
      >
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none"
          stroke={unread > 0 ? "#4F46E5" : "#6B7280"} strokeWidth="2"
          strokeLinecap="round" strokeLinejoin="round">
          <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/>
          <path d="M13.73 21a2 2 0 0 1-3.46 0"/>
        </svg>
        {unread > 0 && (
          <span style={{
            position: "absolute", top: "2px", right: "2px",
            background: "#EF4444", color: "white", borderRadius: "999px",
            fontSize: "10px", fontWeight: 700, minWidth: "16px", height: "16px",
            display: "flex", alignItems: "center", justifyContent: "center",
            padding: "0 3px",
          }}>
            {unread > 9 ? "9+" : unread}
          </span>
        )}
      </button>

      {/* ── Dropdown panel ── */}
      {open && (
        <div style={{
          position: "absolute", right: 0, top: "calc(100% + 8px)",
          width: "360px", maxHeight: "480px", background: "white",
          borderRadius: "12px", boxShadow: "0 10px 40px rgba(0,0,0,0.15)",
          border: "1px solid #E5E7EB", zIndex: 9999, overflow: "hidden",
          display: "flex", flexDirection: "column",
        }}>

          {/* Header */}
          <div style={{
            padding: "14px 16px", borderBottom: "1px solid #F3F4F6",
            display: "flex", alignItems: "center", justifyContent: "space-between",
          }}>
            <span style={{ fontWeight: 700, fontSize: "15px", color: "#111827" }}>
              Notifications{" "}
              {unread > 0 && (
                <span style={{
                  marginLeft: "6px", background: "#4F46E5", color: "white",
                  borderRadius: "999px", fontSize: "11px", padding: "1px 7px",
                }}>
                  {unread} new
                </span>
              )}
            </span>
            <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
              {unread > 0 && (
                <button onClick={markAllRead} style={{
                  fontSize: "12px", color: "#4F46E5", background: "none",
                  border: "none", cursor: "pointer", fontWeight: 600,
                }}>
                  Mark all read
                </button>
              )}
              <button
                onClick={triggerCheck}
                disabled={triggering}
                title="Trigger notification check now"
                style={{
                  fontSize: "11px",
                  background: triggering ? "#E5E7EB" : "#4F46E5",
                  color: triggering ? "#9CA3AF" : "white",
                  border: "none", borderRadius: "6px",
                  padding: "4px 8px",
                  cursor: triggering ? "not-allowed" : "pointer",
                  fontWeight: 600,
                }}
              >
                {triggering ? "Checking..." : "⚡ Check Now"}
              </button>
            </div>
          </div>

          {/* List */}
          <div style={{ overflowY: "auto", flex: 1 }}>
            {notifications.length === 0 ? (
              <div style={{
                padding: "40px 16px", textAlign: "center",
                color: "#9CA3AF", fontSize: "14px",
              }}>
                <div style={{ fontSize: "32px", marginBottom: "8px" }}>🔔</div>
                No notifications yet.
                <br />
                <span style={{ fontSize: "12px" }}>
                  Click <strong>⚡ Check Now</strong> to scan your tasks.
                </span>
              </div>
            ) : (
              notifications.map((n) => {
                const s = getBadgeStyle(n.title);
                return (
                  <div
                    key={n.id}
                    onClick={() => !n.is_read && markRead(n.id)}
                    style={{
                      padding: "12px 16px",
                      borderBottom: "1px solid #F9FAFB",
                      background: n.is_read ? "white" : "#F5F3FF",
                      cursor: n.is_read ? "default" : "pointer",
                      display: "flex", gap: "10px", alignItems: "flex-start",
                    }}
                  >
                    <div style={{
                      width: "8px", height: "8px", borderRadius: "50%",
                      background: n.is_read ? "#D1D5DB" : s.dot,
                      marginTop: "6px", flexShrink: 0,
                    }} />
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <span style={{
                        display: "inline-block", fontSize: "11px", fontWeight: 700,
                        background: s.bg, color: s.color,
                        borderRadius: "4px", padding: "1px 6px", marginBottom: "4px",
                      }}>
                        {n.title}
                      </span>
                      <p style={{
                        margin: 0, fontSize: "13px", color: "#374151",
                        lineHeight: 1.4, whiteSpace: "nowrap",
                        overflow: "hidden", textOverflow: "ellipsis",
                      }}>
                        {n.message}
                      </p>
                      <span style={{ fontSize: "11px", color: "#9CA3AF", display: "block", marginTop: "2px" }}>
                        {formatTime(n.created_at)}
                        {!n.is_read && (
                          <span style={{ marginLeft: "8px", color: "#4F46E5", fontWeight: 600 }}>
                            · tap to dismiss
                          </span>
                        )}
                      </span>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>
      )}
    </div>
  );
}
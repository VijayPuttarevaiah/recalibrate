/**
 * @file Toast.jsx
 * @description Lightweight toast notification system.
 * Supports success, error, and info types with auto-dismiss.
 */

import React, { useState, useEffect, useCallback, createContext, useContext } from "react";

/* ─── Styles ─── */
const styles = {
  container: {
    position: "fixed",
    top: 20,
    right: 20,
    zIndex: 9999,
    display: "flex",
    flexDirection: "column",
    gap: 10,
    pointerEvents: "none",
  },
  toast: (type, isExiting) => ({
    pointerEvents: "auto",
    minWidth: 300,
    maxWidth: 420,
    padding: "14px 18px",
    borderRadius: 14,
    fontSize: 14,
    fontWeight: 500,
    lineHeight: 1.5,
    display: "flex",
    alignItems: "flex-start",
    gap: 10,
    backdropFilter: "blur(12px)",
    boxShadow: "0 8px 32px rgba(0,0,0,0.12)",
    animation: isExiting ? "toastOut 0.3s ease forwards" : "toastIn 0.35s ease",
    ...(type === "success" && {
      background: "rgba(5, 150, 105, 0.1)",
      border: "1px solid rgba(5, 150, 105, 0.25)",
      color: "#065F46",
    }),
    ...(type === "error" && {
      background: "rgba(185, 28, 28, 0.1)",
      border: "1px solid rgba(185, 28, 28, 0.25)",
      color: "#991B1B",
    }),
    ...(type === "info" && {
      background: "rgba(99, 102, 241, 0.1)",
      border: "1px solid rgba(99, 102, 241, 0.25)",
      color: "#3730A3",
    }),
  }),
  icon: { fontSize: 18, flexShrink: 0, marginTop: 1 },
  close: {
    marginLeft: "auto",
    background: "none",
    border: "none",
    cursor: "pointer",
    fontSize: 16,
    opacity: 0.5,
    padding: "0 0 0 8px",
    color: "inherit",
  },
};

const icons = {
  success: "✓",
  error: "✕",
  info: "ℹ",
};

/* ─── Context ─── */
const ToastContext = createContext(null);

export function useToast() {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error("useToast must be used within ToastProvider");
  return ctx;
}

/* ─── Provider ─── */
export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([]);

  const removeToast = useCallback((id) => {
    setToasts((prev) =>
      prev.map((t) => (t.id === id ? { ...t, exiting: true } : t))
    );
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 300);
  }, []);

  const addToast = useCallback(
    (message, type = "info", duration = 4000) => {
      const id = Date.now() + Math.random();
      setToasts((prev) => [...prev, { id, message, type, exiting: false }]);
      if (duration > 0) {
        setTimeout(() => removeToast(id), duration);
      }
      return id;
    },
    [removeToast]
  );

  const toast = {
    success: (msg, duration) => addToast(msg, "success", duration),
    error: (msg, duration) => addToast(msg, "error", duration ?? 6000),
    info: (msg, duration) => addToast(msg, "info", duration),
  };

  return (
    <ToastContext.Provider value={toast}>
      {children}

      {/* Keyframes */}
      <style>{`
        @keyframes toastIn {
          from { opacity: 0; transform: translateX(40px) scale(0.95); }
          to { opacity: 1; transform: translateX(0) scale(1); }
        }
        @keyframes toastOut {
          from { opacity: 1; transform: translateX(0) scale(1); }
          to { opacity: 0; transform: translateX(40px) scale(0.95); }
        }
      `}</style>

      {/* Toast Container */}
      <div style={styles.container}>
        {toasts.map((t) => (
          <div key={t.id} style={styles.toast(t.type, t.exiting)}>
            <span style={styles.icon}>{icons[t.type]}</span>
            <span style={{ flex: 1 }}>{t.message}</span>
            <button style={styles.close} onClick={() => removeToast(t.id)}>
              ×
            </button>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}
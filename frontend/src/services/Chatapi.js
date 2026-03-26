/**
 * @file services/chatApi.js
 * @description API client for the AI Chat feature.
 * Handles both regular requests and SSE streaming.
 */

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

function authHeaders() {
  const token = localStorage.getItem("agp_auth_token");
  return {
    "Content-Type": "application/json",
    ...(token && { Authorization: `Bearer ${token}` }),
  };
}

// ── Standard endpoints ──

export async function createChatSession({ goalId, taskId, message }) {
  const res = await fetch(`${API_BASE}/chat/sessions`, {
    method: "POST",
    headers: authHeaders(),
    body: JSON.stringify({
      goal_id: goalId,
      task_id: taskId || null,
      message,
    }),
  });
  if (!res.ok) throw new Error((await res.json()).detail || "Failed to start chat");
  return res.json();
}

export async function sendMessage({ sessionId, message }) {
  const res = await fetch(`${API_BASE}/chat/sessions/${sessionId}/messages`, {
    method: "POST",
    headers: authHeaders(),
    body: JSON.stringify({ message }),
  });
  if (!res.ok) throw new Error((await res.json()).detail || "Failed to send message");
  return res.json();
}

export async function getChatHistory(sessionId) {
  const res = await fetch(`${API_BASE}/chat/sessions/${sessionId}`, {
    headers: authHeaders(),
  });
  if (!res.ok) throw new Error("Failed to load chat history");
  return res.json();
}

export async function listChatSessions(goalId) {
  const res = await fetch(`${API_BASE}/chat/sessions?goal_id=${goalId}`, {
    headers: authHeaders(),
  });
  if (!res.ok) throw new Error("Failed to load sessions");
  return res.json();
}

export async function explainTask(taskId) {
  const res = await fetch(`${API_BASE}/chat/explain/task/${taskId}`, {
    method: "POST",
    headers: authHeaders(),
  });
  if (!res.ok) throw new Error("Failed to explain task");
  return res.json();
}

// ── Streaming endpoint (SSE) ──

export function streamMessage({ sessionId, message, onToken, onDone, onError }) {
  const token = localStorage.getItem("agp_auth_token")
  const controller = new AbortController();

  fetch(`${API_BASE}/chat/sessions/${sessionId}/messages/stream`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(token && { Authorization: `Bearer ${token}` }),
    },
    body: JSON.stringify({ message }),
    signal: controller.signal,
  })
    .then(async (res) => {
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: "Stream failed" }));
        onError?.(new Error(err.detail));
        return;
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            const data = line.slice(6);
            if (data === "[DONE]") {
              onDone?.();
              return;
            }
            try {
              const parsed = JSON.parse(data);
              if (parsed.token) onToken(parsed.token);
              if (parsed.suggestions) onDone?.(parsed.suggestions);
            } catch {
              // plain text token
              onToken(data);
            }
          }
        }
      }
      onDone?.();
    })
    .catch((err) => {
      if (err.name !== "AbortError") onError?.(err);
    });

  return () => controller.abort();
}

export async function getSuggestedQuestions({ goalId, taskId }) {
  const params = new URLSearchParams({ goal_id: goalId });
  if (taskId) params.append("task_id", taskId);

  const res = await fetch(`${API_BASE}/chat/suggestions?${params}`, {
    headers: authHeaders(),
  });
  if (!res.ok) return [];
  const data = await res.json();
  return data.suggestions || [];
}
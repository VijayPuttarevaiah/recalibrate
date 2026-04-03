/**
 * @file frontend/src/test/chatApi.test.js
 * RED: Unit tests for chatApi service.
 * All fetch calls mocked — no network.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";

// Mock localStorage
const mockStorage = {};
vi.stubGlobal("localStorage", {
  getItem: (key) => mockStorage[key] || null,
  setItem: (key, val) => { mockStorage[key] = val; },
  clear: () => Object.keys(mockStorage).forEach((k) => delete mockStorage[k]),
});

const {
  createChatSession,
  sendMessage,
  getChatHistory,
  listChatSessions,
  explainTask,
  getSuggestedQuestions,
} = await import("../services/Chatapi.js");


describe("chatApi", () => {
  let fetchSpy;

  beforeEach(() => {
    mockStorage["agp_auth_token"] = "test-jwt-123";
    fetchSpy = vi.fn();
    vi.stubGlobal("fetch", fetchSpy);
  });

  afterEach(() => {
    vi.restoreAllMocks();
    localStorage.clear();
  });

  // ── Auth ──

  describe("auth headers", () => {
    it("sends Bearer token from agp_auth_token", async () => {
      fetchSpy.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ session_id: 1, user_message: {}, assistant_message: {} }),
      });

      await createChatSession({ goalId: 5, message: "Hi" });

      const headers = fetchSpy.mock.calls[0][1].headers;
      expect(headers.Authorization).toBe("Bearer test-jwt-123");
    });

    it("omits Authorization when no token", async () => {
      delete mockStorage["agp_auth_token"];
      fetchSpy.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ session_id: 1, user_message: {}, assistant_message: {} }),
      });

      await createChatSession({ goalId: 5, message: "Hi" });

      const headers = fetchSpy.mock.calls[0][1].headers;
      expect(headers.Authorization).toBeUndefined();
    });
  });

  // ── createChatSession ──

  describe("createChatSession", () => {
    it("POSTs to /chat/sessions with correct body", async () => {
      fetchSpy.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({
          session_id: 1,
          user_message: { id: 1, role: "user", content: "Hello", created_at: "" },
          assistant_message: { id: 2, role: "assistant", content: "Hi!", created_at: "" },
        }),
      });

      const result = await createChatSession({ goalId: 5, taskId: 42, message: "Hello" });

      const [url, opts] = fetchSpy.mock.calls[0];
      expect(url).toContain("/chat/sessions");
      expect(opts.method).toBe("POST");
      const body = JSON.parse(opts.body);
      expect(body.goal_id).toBe(5);
      expect(body.task_id).toBe(42);
      expect(body.message).toBe("Hello");
      expect(result.session_id).toBe(1);
    });

    it("sends null task_id when not provided", async () => {
      fetchSpy.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ session_id: 1, user_message: {}, assistant_message: {} }),
      });

      await createChatSession({ goalId: 5, message: "Hi" });

      const body = JSON.parse(fetchSpy.mock.calls[0][1].body);
      expect(body.task_id).toBeNull();
    });

    it("throws on non-ok response", async () => {
      fetchSpy.mockResolvedValue({
        ok: false,
        json: () => Promise.resolve({ detail: "Goal not found" }),
      });

      await expect(createChatSession({ goalId: 999, message: "Hi" }))
        .rejects.toThrow("Goal not found");
    });
  });

  // ── sendMessage ──

  describe("sendMessage", () => {
    it("POSTs to /chat/sessions/{id}/messages", async () => {
      fetchSpy.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({
          session_id: 1,
          user_message: { id: 3, role: "user", content: "More", created_at: "" },
          assistant_message: { id: 4, role: "assistant", content: "Sure!", created_at: "" },
        }),
      });

      const result = await sendMessage({ sessionId: 1, message: "More" });

      expect(fetchSpy.mock.calls[0][0]).toContain("/chat/sessions/1/messages");
      expect(result.session_id).toBe(1);
    });

    it("throws on failure", async () => {
      fetchSpy.mockResolvedValue({
        ok: false,
        json: () => Promise.resolve({ detail: "Session not found" }),
      });

      await expect(sendMessage({ sessionId: 999, message: "Hi" }))
        .rejects.toThrow("Session not found");
    });
  });

  // ── getChatHistory ──

  describe("getChatHistory", () => {
    it("GETs /chat/sessions/{id}", async () => {
      fetchSpy.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ session_id: 1, goal_id: 5, messages: [{ id: 1 }] }),
      });

      const result = await getChatHistory(1);

      expect(fetchSpy.mock.calls[0][0]).toContain("/chat/sessions/1");
      expect(result.messages).toHaveLength(1);
    });
  });

  // ── listChatSessions ──

  describe("listChatSessions", () => {
    it("GETs with goal_id param", async () => {
      fetchSpy.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve([{ id: 1, goal_id: 5 }]),
      });

      const result = await listChatSessions(5);

      expect(fetchSpy.mock.calls[0][0]).toContain("goal_id=5");
      expect(result).toHaveLength(1);
    });
  });

  // ── explainTask ──

  describe("explainTask", () => {
    it("POSTs to /chat/explain/task/{id}", async () => {
      fetchSpy.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ task_id: 42, explanation: "You should..." }),
      });

      const result = await explainTask(42);

      expect(fetchSpy.mock.calls[0][0]).toContain("/chat/explain/task/42");
      expect(result.explanation).toContain("You should");
    });
  });

  // ── getSuggestedQuestions ──

  describe("getSuggestedQuestions", () => {
    it("GETs with goal_id and task_id", async () => {
      fetchSpy.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ suggestions: ["Q1", "Q2", "Q3"] }),
      });

      const result = await getSuggestedQuestions({ goalId: 5, taskId: 42 });

      expect(fetchSpy.mock.calls[0][0]).toContain("goal_id=5");
      expect(fetchSpy.mock.calls[0][0]).toContain("task_id=42");
      expect(result).toEqual(["Q1", "Q2", "Q3"]);
    });

    it("returns empty on failure", async () => {
      fetchSpy.mockResolvedValue({ ok: false });

      const result = await getSuggestedQuestions({ goalId: 5 });
      expect(result).toEqual([]);
    });

    it("omits task_id when not given", async () => {
      fetchSpy.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ suggestions: ["Q1"] }),
      });

      await getSuggestedQuestions({ goalId: 5 });

      expect(fetchSpy.mock.calls[0][0]).not.toContain("task_id");
    });
  });
});
/**
 * @file frontend/src/test/useChat.test.js
 * RED: Unit tests for useChat hook.
 * All chatApi calls mocked — no network.
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, act, waitFor } from "@testing-library/react";
import useChat from "../../hooks/useChat.js";

vi.mock("../../services/Chatapi.js", () => ({
  createChatSession: vi.fn(),
  sendMessage: vi.fn(),
  streamMessage: vi.fn(),
  getChatHistory: vi.fn(),
  getSuggestedQuestions: vi.fn(),
}));

import {
  createChatSession,
  sendMessage,
  getChatHistory,
  getSuggestedQuestions,
} from "../../services/Chatapi.js";


describe("useChat", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    getSuggestedQuestions.mockResolvedValue(["Q1", "Q2", "Q3"]);
  });

  // ── Initial State ──

  describe("initial state", () => {
    it("starts with empty messages", () => {
      const { result } = renderHook(() => useChat({ goalId: 5 }));

      expect(result.current.messages).toEqual([]);
      expect(result.current.sessionId).toBeNull();
      expect(result.current.isLoading).toBe(false);
      expect(result.current.isStreaming).toBe(false);
      expect(result.current.error).toBeNull();
    });

    it("fetches suggestions on mount", async () => {
      renderHook(() => useChat({ goalId: 5, taskId: 42 }));

      await waitFor(() => {
        expect(getSuggestedQuestions).toHaveBeenCalledWith({ goalId: 5, taskId: 42 });
      });
    });
  });

  // ── First Message ──

  describe("first message (creates session)", () => {
    it("creates session and adds both messages", async () => {
      createChatSession.mockResolvedValue({
        session_id: 1,
        user_message: { id: 1, role: "user", content: "Hello", created_at: "2026-03-18T10:00:00" },
        assistant_message: { id: 2, role: "assistant", content: "Hi!", created_at: "2026-03-18T10:00:01" },
      });

      const { result } = renderHook(() => useChat({ goalId: 5 }));

      await act(async () => {
        await result.current.send("Hello");
      });

      await waitFor(() => {
        expect(result.current.messages).toHaveLength(2);
        expect(result.current.messages[0].role).toBe("user");
        expect(result.current.messages[1].role).toBe("assistant");
        expect(result.current.sessionId).toBe(1);
      });
    });

    it("passes correct params to createChatSession", async () => {
      createChatSession.mockResolvedValue({
        session_id: 1,
        user_message: { id: 1, role: "user", content: "Hi", created_at: "" },
        assistant_message: { id: 2, role: "assistant", content: "Hey", created_at: "" },
      });

      const { result } = renderHook(() => useChat({ goalId: 5, taskId: 42 }));

      await act(async () => { await result.current.send("Hi"); });

      expect(createChatSession).toHaveBeenCalledWith({
        goalId: 5, taskId: 42, message: "Hi",
      });
    });

    it("sets error and removes temp message on failure", async () => {
      createChatSession.mockRejectedValue(new Error("Goal not found"));

      const { result } = renderHook(() => useChat({ goalId: 999 }));

      await act(async () => { await result.current.send("Hello"); });

      await waitFor(() => {
        expect(result.current.error).toBe("Goal not found");
        expect(result.current.messages).toHaveLength(0);
      });
    });

    it("ignores empty messages", async () => {
      const { result } = renderHook(() => useChat({ goalId: 5 }));

      await act(async () => { await result.current.send(""); });

      expect(createChatSession).not.toHaveBeenCalled();
    });

    it("ignores whitespace-only messages", async () => {
      const { result } = renderHook(() => useChat({ goalId: 5 }));

      await act(async () => { await result.current.send("   "); });

      expect(createChatSession).not.toHaveBeenCalled();
    });

    it("trims message before sending", async () => {
      createChatSession.mockResolvedValue({
        session_id: 1,
        user_message: { id: 1, role: "user", content: "Hello", created_at: "" },
        assistant_message: { id: 2, role: "assistant", content: "Hi", created_at: "" },
      });

      const { result } = renderHook(() => useChat({ goalId: 5 }));

      await act(async () => { await result.current.send("  Hello  "); });

      expect(createChatSession).toHaveBeenCalledWith(
        expect.objectContaining({ message: "Hello" })
      );
    });
  });

  // ── Load Session ──

  describe("loadSession", () => {
    it("loads history and sets sessionId", async () => {
      getChatHistory.mockResolvedValue({
        session_id: 5, goal_id: 1,
        messages: [
          { id: 1, role: "user", content: "Old Q", created_at: "2026-03-17T10:00:00" },
          { id: 2, role: "assistant", content: "Old A", created_at: "2026-03-17T10:00:01" },
        ],
      });

      const { result } = renderHook(() => useChat({ goalId: 1 }));

      await act(async () => { await result.current.loadSession(5); });

      await waitFor(() => {
        expect(result.current.sessionId).toBe(5);
        expect(result.current.messages).toHaveLength(2);
      });
    });
  });

  // ── Reset ──

  describe("reset", () => {
    it("clears messages and session", async () => {
      createChatSession.mockResolvedValue({
        session_id: 1,
        user_message: { id: 1, role: "user", content: "Hi", created_at: "" },
        assistant_message: { id: 2, role: "assistant", content: "Hey", created_at: "" },
      });

      const { result } = renderHook(() => useChat({ goalId: 5 }));

      await act(async () => { await result.current.send("Hi"); });
      expect(result.current.sessionId).toBe(1);

      act(() => { result.current.reset(); });

      expect(result.current.messages).toEqual([]);
      expect(result.current.sessionId).toBeNull();
      expect(result.current.error).toBeNull();
    });
  });

  // ── Double-send guard ──

  describe("concurrent protection", () => {
    it("ignores send while loading", async () => {
      let resolveFirst;
      createChatSession.mockImplementation(
        () => new Promise((r) => { resolveFirst = r; })
      );

      const { result } = renderHook(() => useChat({ goalId: 5 }));

      act(() => { result.current.send("First"); });
      expect(result.current.isLoading).toBe(true);

      await act(async () => { await result.current.send("Second"); });

      expect(createChatSession).toHaveBeenCalledTimes(1);

      // Clean up
      resolveFirst({
        session_id: 1,
        user_message: { id: 1, role: "user", content: "First", created_at: "" },
        assistant_message: { id: 2, role: "assistant", content: "Reply", created_at: "" },
      });
    });
  });
});
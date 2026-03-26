/**
 * @file hooks/useChat.js
 * @description Manages chat state: messages, streaming, sessions, suggestions.
 * Drop-in hook for both the full ChatPage and the ChatDrawer.
 */

import { useState, useRef, useCallback, useEffect } from "react";
import {
  createChatSession,
  sendMessage,
  streamMessage,
  getChatHistory,
  getSuggestedQuestions,
} from "../services/Chatapi";

const ENABLE_STREAMING = true; // toggle if backend doesn't support streaming yet

export default function useChat({ goalId, taskId = null }) {
  const [messages, setMessages] = useState([]);
  const [sessionId, setSessionId] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState(null);
  const [suggestions, setSuggestions] = useState([]);

  const abortRef = useRef(null);
  const streamBufferRef = useRef("");

  // Load initial suggestions when goal/task changes
  useEffect(() => {
    if (goalId) {
      getSuggestedQuestions({ goalId, taskId })
        .then(setSuggestions)
        .catch(() => {});
    }
  }, [goalId, taskId]);

  // Load existing session history
  const loadSession = useCallback(async (existingSessionId) => {
    try {
      setIsLoading(true);
      const data = await getChatHistory(existingSessionId);
      setSessionId(existingSessionId);
      setMessages(
        data.messages.map((m) => ({
          id: m.id,
          role: m.role,
          content: m.content,
          timestamp: m.created_at,
        }))
      );
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Send a message (creates session on first message)
  const send = useCallback(
    async (text) => {
      if (!text.trim() || isLoading || isStreaming) return;

      const userMsg = {
        id: `temp-${Date.now()}`,
        role: "user",
        content: text.trim(),
        timestamp: new Date().toISOString(),
      };

      setMessages((prev) => [...prev, userMsg]);
      setError(null);
      setSuggestions([]);

      // ── First message: create session ──
      if (!sessionId) {
        setIsLoading(true);
        try {
          const data = await createChatSession({
            goalId,
            taskId,
            message: text.trim(),
          });

          setSessionId(data.session_id);

          setMessages([
            {
              id: data.user_message.id,
              role: "user",
              content: data.user_message.content,
              timestamp: data.user_message.created_at,
            },
            {
              id: data.assistant_message.id,
              role: "assistant",
              content: data.assistant_message.content,
              timestamp: data.assistant_message.created_at,
            },
          ]);

          // Fetch new suggestions after first response
          getSuggestedQuestions({ goalId, taskId })
            .then(setSuggestions)
            .catch(() => {});
        } catch (err) {
          setError(err.message);
          setMessages((prev) => prev.filter((m) => m.id !== userMsg.id));
        } finally {
          setIsLoading(false);
        }
        return;
      }

      // ── Follow-up: stream or regular ──
      if (ENABLE_STREAMING) {
        setIsStreaming(true);
        streamBufferRef.current = "";

        // Add placeholder assistant message
        const assistantPlaceholder = {
          id: `stream-${Date.now()}`,
          role: "assistant",
          content: "",
          timestamp: new Date().toISOString(),
          isStreaming: true,
        };
        setMessages((prev) => [...prev, assistantPlaceholder]);

        abortRef.current = streamMessage({
          sessionId,
          message: text.trim(),
          onToken: (token) => {
            streamBufferRef.current += token;
            setMessages((prev) => {
              const updated = [...prev];
              const last = updated[updated.length - 1];
              if (last?.isStreaming) {
                updated[updated.length - 1] = {
                  ...last,
                  content: streamBufferRef.current,
                };
              }
              return updated;
            });
          },
          onDone: (newSuggestions) => {
            setIsStreaming(false);
            setMessages((prev) => {
              const updated = [...prev];
              const last = updated[updated.length - 1];
              if (last?.isStreaming) {
                updated[updated.length - 1] = {
                  ...last,
                  isStreaming: false,
                };
              }
              return updated;
            });
            if (newSuggestions?.length) {
              setSuggestions(newSuggestions);
            } else {
              getSuggestedQuestions({ goalId, taskId })
                .then(setSuggestions)
                .catch(() => {});
            }
          },
          onError: (err) => {
            setIsStreaming(false);
            setError(err.message);
            // Remove the empty placeholder
            setMessages((prev) => prev.filter((m) => !m.isStreaming));
          },
        });
      } else {
        // Non-streaming fallback
        setIsLoading(true);
        try {
          const data = await sendMessage({
            sessionId,
            message: text.trim(),
          });

          // Replace temp user msg + add assistant msg
          setMessages((prev) => [
            ...prev.filter((m) => m.id !== userMsg.id),
            {
              id: data.user_message.id,
              role: "user",
              content: data.user_message.content,
              timestamp: data.user_message.created_at,
            },
            {
              id: data.assistant_message.id,
              role: "assistant",
              content: data.assistant_message.content,
              timestamp: data.assistant_message.created_at,
            },
          ]);

          getSuggestedQuestions({ goalId, taskId })
            .then(setSuggestions)
            .catch(() => {});
        } catch (err) {
          setError(err.message);
        } finally {
          setIsLoading(false);
        }
      }
    },
    [sessionId, goalId, taskId, isLoading, isStreaming]
  );

  // Stop streaming
  const stopStreaming = useCallback(() => {
    if (abortRef.current) {
      abortRef.current();
      setIsStreaming(false);
    }
  }, []);

  // Reset chat (new conversation)
  const reset = useCallback(() => {
    if (abortRef.current) abortRef.current();
    setMessages([]);
    setSessionId(null);
    setError(null);
    setIsStreaming(false);
    setIsLoading(false);
    getSuggestedQuestions({ goalId, taskId })
      .then(setSuggestions)
      .catch(() => {});
  }, [goalId, taskId]);

  return {
    messages,
    sessionId,
    isLoading,
    isStreaming,
    error,
    suggestions,
    send,
    stopStreaming,
    reset,
    loadSession,
  };
}
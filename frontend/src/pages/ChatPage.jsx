/**
 * @file pages/ChatPage.jsx
 * @description Full-page AI chat with session sidebar.
 * Accessed via /goals/:goalId/chat or /goals/:goalId/tasks/:taskId/chat
 */

import React, { useState, useEffect, useRef, useCallback } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import useChat from "../hooks/useChat";
import { listChatSessions } from "../services/Chatapi";
import ChatMessage from "../components/ChatMessage";
import ChatInput from "../components/ChatInput";
import SuggestionChips from "./SuggestionChips"

export default function ChatPage() {
  const { goalId, taskId } = useParams();
  const navigate = useNavigate();
  const gid = parseInt(goalId, 10);
  const tid = taskId ? parseInt(taskId, 10) : null;

  const {
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
  } = useChat({ goalId: gid, taskId: tid });

  const [sessions, setSessions] = useState([]);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const scrollRef = useRef(null);

  // Load session list
  useEffect(() => {
    listChatSessions(gid)
      .then(setSessions)
      .catch(() => {});
  }, [gid, sessionId]);

  // Auto-scroll
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const handleLoadSession = useCallback(
    (sid) => {
      loadSession(sid);
      // On mobile close sidebar
      if (window.innerWidth < 768) setSidebarOpen(false);
    },
    [loadSession]
  );

  const handleNewChat = () => {
    reset();
    if (window.innerWidth < 768) setSidebarOpen(false);
  };

  return (
    <div className="ChatPage">
      {/* ── Sidebar ── */}
      <aside className={`ChatSidebar ${sidebarOpen ? "ChatSidebarOpen" : ""}`}>
        <div className="ChatSidebarHeader">
          <h3 className="ChatSidebarTitle">Conversations</h3>
          <button className="ChatDrawerIconBtn" onClick={() => setSidebarOpen(false)}>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M15 18l-6-6 6-6" />
            </svg>
          </button>
        </div>

        <button className="ChatNewBtn" onClick={handleNewChat}>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M12 5v14M5 12h14" />
          </svg>
          New conversation
        </button>

        <div className="ChatSessionList">
          {sessions.map((s) => (
            <button
              key={s.id}
              className={`ChatSessionItem ${s.id === sessionId ? "ChatSessionItemActive" : ""}`}
              onClick={() => handleLoadSession(s.id)}
            >
              <span className="ChatSessionItemTitle">{s.title || "Untitled"}</span>
              <span className="ChatSessionItemMeta">
                {s.message_count} msg{s.message_count !== 1 ? "s" : ""}
              </span>
            </button>
          ))}
          {sessions.length === 0 && (
            <p className="ChatSidebarEmpty">No conversations yet</p>
          )}
        </div>

        <div className="ChatSidebarFooter">
          <Link to={`/goals/${gid}/tasks`} className="ChatBackLink">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M19 12H5M12 19l-7-7 7-7" />
            </svg>
            Back to tasks
          </Link>
        </div>
      </aside>

      {/* ── Main chat area ── */}
      <main className="ChatMain">
        {/* Mobile header */}
        <div className="ChatMainHeader">
          <button
            className="ChatDrawerIconBtn"
            onClick={() => setSidebarOpen(true)}
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M3 12h18M3 6h18M3 18h18" />
            </svg>
          </button>
          <span className="ChatMainHeaderTitle">AI Assistant</span>
          <button className="ChatDrawerIconBtn" onClick={handleNewChat}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M12 5v14M5 12h14" />
            </svg>
          </button>
        </div>

        {/* Messages area */}
        <div className="ChatMessages" ref={scrollRef}>
          {messages.length === 0 && !isLoading && (
            <div className="ChatEmptyStatePage">
              <div className="ChatEmptyIcon ChatEmptyIconLg">
                <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                  <path d="M12 2a4 4 0 0 1 4 4v1a1 1 0 0 1-1 1H9a1 1 0 0 1-1-1V6a4 4 0 0 1 4-4Z" />
                  <path d="M9 8v1a3 3 0 0 0 6 0V8" />
                  <rect x="5" y="12" width="14" height="9" rx="2" />
                  <path d="M9 16h6" />
                </svg>
              </div>
              <h2 className="ChatEmptyTitleLg">What would you like to know?</h2>
              <p className="ChatEmptyTextLg">
                Ask me about your goals, tasks, or how to approach any step in your plan.
                I'll give context-aware guidance based on your actual progress.
              </p>
              <SuggestionChips
                suggestions={suggestions}
                onSelect={send}
                disabled={isLoading}
              />
            </div>
          )}

          {messages.map((msg) => (
            <ChatMessage
              key={msg.id}
              role={msg.role}
              content={msg.content}
              isStreaming={msg.isStreaming}
            />
          ))}

          {isLoading && messages.length > 0 && (
            <div className="ChatMsg ChatMsgAssistant">
              <div className="ChatAvatar ChatAvatarAI">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M12 2a4 4 0 0 1 4 4v1a1 1 0 0 1-1 1H9a1 1 0 0 1-1-1V6a4 4 0 0 1 4-4Z" />
                  <path d="M9 8v1a3 3 0 0 0 6 0V8" />
                  <rect x="5" y="12" width="14" height="9" rx="2" />
                  <path d="M9 16h6" />
                </svg>
              </div>
              <div className="ChatBubble ChatBubbleAI">
                <div className="ChatTyping">
                  <span /><span /><span />
                </div>
              </div>
            </div>
          )}

          {messages.length > 0 && !isLoading && !isStreaming && suggestions.length > 0 && (
            <div style={{ padding: "0 48px" }}>
              <SuggestionChips
                suggestions={suggestions}
                onSelect={send}
                disabled={isLoading || isStreaming}
              />
            </div>
          )}

          {error && (
            <div className="ChatError" style={{ margin: "0 48px" }}>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="12" r="10" />
                <path d="M12 8v4M12 16h.01" />
              </svg>
              {error}
            </div>
          )}
        </div>

        {/* Input */}
        <div className="ChatMainInput">
          <ChatInput
            onSend={send}
            isLoading={isLoading}
            isStreaming={isStreaming}
            onStop={stopStreaming}
            placeholder="Ask about your goals or tasks…"
          />
        </div>
      </main>

      {/* Mobile sidebar overlay */}
      {sidebarOpen && (
        <div
          className="ChatSidebarOverlay"
          onClick={() => setSidebarOpen(false)}
        />
      )}
    </div>
  );
}
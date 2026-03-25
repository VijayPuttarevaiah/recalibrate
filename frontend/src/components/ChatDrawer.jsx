/**
 * @file components/ChatDrawer.jsx
 * @description Slide-out AI chat panel. Opens from the right side.
 * Use from any goal/task page via:
 *
 *   <ChatDrawer open={open} onClose={close} goalId={5} taskId={42} taskTitle="..." />
 *
 * Non-intrusive: doesn't navigate away from the current page.
 */

import React, { useEffect, useRef } from "react";
import useChat from "../hooks/useChat";
import ChatMessage from "./ChatMessage";
import ChatInput from "./ChatInput";
import SuggestionChips from "../pages/SuggestionChips";

export default function ChatDrawer({
  open,
  onClose,
  goalId,
  taskId = null,
  goalTitle = "",
  taskTitle = "",
}) {
  const {
    messages,
    isLoading,
    isStreaming,
    error,
    suggestions,
    send,
    stopStreaming,
    reset,
  } = useChat({ goalId, taskId });

  const scrollRef = useRef(null);

  // Auto-scroll on new messages
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  // Trap focus when open
  useEffect(() => {
    if (open) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "";
    }
    return () => { document.body.style.overflow = ""; };
  }, [open]);

  // Escape to close
  useEffect(() => {
    const handler = (e) => { if (e.key === "Escape" && open) onClose(); };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [open, onClose]);

  if (!open) return null;

  const contextLabel = taskTitle
    ? `Chatting about: ${taskTitle}`
    : goalTitle
      ? `Chatting about: ${goalTitle}`
      : "AI Assistant";

  return (
    <>
      {/* Backdrop */}
      <div className="ChatDrawerBackdrop" onClick={onClose} />

      {/* Drawer panel */}
      <aside className="ChatDrawer">
        {/* Header */}
        <div className="ChatDrawerHeader">
          <div className="ChatDrawerHeaderLeft">
            <div className="ChatDrawerDot" />
            <div>
              <h3 className="ChatDrawerTitle">AI Assistant</h3>
              <p className="ChatDrawerContext">{contextLabel}</p>
            </div>
          </div>
          <div className="ChatDrawerHeaderActions">
            <button className="ChatDrawerIconBtn" onClick={reset} title="New conversation">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M12 5V1L7 6l5 5V7a6 6 0 0 1 0 12 6 6 0 0 1-6-6H4a8 8 0 1 0 8-8Z" />
              </svg>
            </button>
            <button className="ChatDrawerIconBtn" onClick={onClose} title="Close">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M18 6L6 18M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        {/* Messages */}
        <div className="ChatDrawerMessages" ref={scrollRef}>
          {messages.length === 0 && !isLoading && (
            <div className="ChatEmptyState">
              <div className="ChatEmptyIcon">
                <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                  <path d="M12 2a4 4 0 0 1 4 4v1a1 1 0 0 1-1 1H9a1 1 0 0 1-1-1V6a4 4 0 0 1 4-4Z" />
                  <path d="M9 8v1a3 3 0 0 0 6 0V8" />
                  <rect x="5" y="12" width="14" height="9" rx="2" />
                  <path d="M9 16h6" />
                </svg>
              </div>
              <h4 className="ChatEmptyTitle">How can I help?</h4>
              <p className="ChatEmptyText">
                Ask me anything about this {taskTitle ? "task" : "goal"}. I can explain
                what to do, break it into steps, or give tips.
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

          {/* Follow-up suggestions after messages */}
          {messages.length > 0 && !isLoading && !isStreaming && suggestions.length > 0 && (
            <SuggestionChips
              suggestions={suggestions}
              onSelect={send}
              disabled={isLoading || isStreaming}
            />
          )}

          {error && (
            <div className="ChatError">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="12" r="10" />
                <path d="M12 8v4M12 16h.01" />
              </svg>
              {error}
            </div>
          )}
        </div>

        {/* Input */}
        <ChatInput
          onSend={send}
          isLoading={isLoading}
          isStreaming={isStreaming}
          onStop={stopStreaming}
        />
      </aside>
    </>
  );
}
/**
 * @file components/ChatInput.jsx
 * @description Chat input bar with auto-resizing textarea,
 * send button, and stop-streaming button.
 */

import React, { useState, useRef, useEffect } from "react";

export default function ChatInput({
  onSend,
  isLoading,
  isStreaming,
  onStop,
  disabled,
  placeholder = "Ask about your goal or task…",
}) {
  const [text, setText] = useState("");
  const textareaRef = useRef(null);

  // Auto-resize textarea
  useEffect(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = Math.min(el.scrollHeight, 160) + "px";
  }, [text]);

  const handleSend = () => {
    if (!text.trim() || isLoading || disabled) return;
    onSend(text.trim());
    setText("");
    // Reset height
    if (textareaRef.current) textareaRef.current.style.height = "auto";
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="ChatInputBar">
      <div className="ChatInputWrap">
        <textarea
          ref={textareaRef}
          className="ChatTextarea"
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          rows={1}
          disabled={isLoading || disabled}
        />

        {isStreaming ? (
          <button className="ChatSendBtn ChatStopBtn" onClick={onStop} title="Stop generating">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
              <rect x="6" y="6" width="12" height="12" rx="2" />
            </svg>
          </button>
        ) : (
          <button
            className="ChatSendBtn"
            onClick={handleSend}
            disabled={!text.trim() || isLoading || disabled}
            title="Send message"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M22 2L11 13" />
              <path d="M22 2L15 22L11 13L2 9L22 2Z" />
            </svg>
          </button>
        )}
      </div>

      <p className="ChatInputHint">
        <kbd>Enter</kbd> to send · <kbd>Shift+Enter</kbd> for new line
      </p>
    </div>
  );
}
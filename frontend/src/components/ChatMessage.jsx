/**
 * @file components/ChatMessage.jsx
 * @description Single chat bubble. Handles user/assistant styling,
 * streaming cursor, and basic markdown-like formatting.
 */

import React, { memo } from "react";

function formatContent(text) {
  if (!text) return null;

  // Split into blocks by double newline
  const blocks = text.split(/\n{2,}/);

  return blocks.map((block, i) => {
    // Numbered list
    if (/^\d+\.\s/.test(block.trim())) {
      const items = block
        .split(/\n/)
        .filter((l) => l.trim())
        .map((line) => line.replace(/^\d+\.\s*/, ""));
      return (
        <ol key={i} className="ChatMsgList">
          {items.map((item, j) => (
            <li key={j}>{inlineFormat(item)}</li>
          ))}
        </ol>
      );
    }

    // Bullet list
    if (/^[-•*]\s/.test(block.trim())) {
      const items = block
        .split(/\n/)
        .filter((l) => l.trim())
        .map((line) => line.replace(/^[-•*]\s*/, ""));
      return (
        <ul key={i} className="ChatMsgList">
          {items.map((item, j) => (
            <li key={j}>{inlineFormat(item)}</li>
          ))}
        </ul>
      );
    }

    // Regular paragraph
    const lines = block.split(/\n/).filter((l) => l.trim());
    return (
      <p key={i} className="ChatMsgPara">
        {lines.map((line, j) => (
          <React.Fragment key={j}>
            {j > 0 && <br />}
            {inlineFormat(line)}
          </React.Fragment>
        ))}
      </p>
    );
  });
}

function inlineFormat(text) {
  // Bold: **text**
  const parts = text.split(/(\*\*[^*]+\*\*)/g);
  return parts.map((part, i) => {
    if (part.startsWith("**") && part.endsWith("**")) {
      return <strong key={i}>{part.slice(2, -2)}</strong>;
    }
    return part;
  });
}

function ChatMessage({ role, content, isStreaming }) {
  const isUser = role === "user";

  return (
    <div className={`ChatMsg ${isUser ? "ChatMsgUser" : "ChatMsgAssistant"}`}>
      {/* Avatar */}
      <div className={`ChatAvatar ${isUser ? "ChatAvatarUser" : "ChatAvatarAI"}`}>
        {isUser ? (
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
            <circle cx="12" cy="7" r="4" />
          </svg>
        ) : (
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M12 2a4 4 0 0 1 4 4v1a1 1 0 0 1-1 1H9a1 1 0 0 1-1-1V6a4 4 0 0 1 4-4Z" />
            <path d="M9 8v1a3 3 0 0 0 6 0V8" />
            <rect x="5" y="12" width="14" height="9" rx="2" />
            <path d="M9 16h6" />
          </svg>
        )}
      </div>

      {/* Content */}
      <div className={`ChatBubble ${isUser ? "ChatBubbleUser" : "ChatBubbleAI"}`}>
        <div className="ChatBubbleContent">
          {content ? formatContent(content) : null}
          {isStreaming && <span className="ChatCursor" />}
        </div>
      </div>
    </div>
  );
}

export default memo(ChatMessage);
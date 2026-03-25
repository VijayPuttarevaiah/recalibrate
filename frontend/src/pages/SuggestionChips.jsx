/**
 * @file components/SuggestionChips.jsx
 * @description Clickable suggestion pills shown before first message
 * and after each AI response.
 */

import React from "react";

export default function SuggestionChips({ suggestions, onSelect, disabled }) {
  if (!suggestions?.length) return null;

  return (
    <div className="ChatSuggestions">
      {suggestions.map((text, i) => (
        <button
          key={i}
          className="ChatSuggestionChip"
          onClick={() => onSelect(text)}
          disabled={disabled}
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ flexShrink: 0 }}>
            <circle cx="12" cy="12" r="10" />
            <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3" />
            <path d="M12 17h.01" />
          </svg>
          {text}
        </button>
      ))}
    </div>
  );
}
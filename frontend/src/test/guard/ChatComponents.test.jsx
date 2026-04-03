/**
 * @file frontend/src/test/ChatComponents.test.jsx
 * RED: Unit tests for ChatMessage, ChatInput, SuggestionChips.
 * Tests rendering output and user interactions.
 */

import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import React from "react";

import ChatMessage from "../../components/ChatMessage.jsx";
import ChatInput from "../../components/ChatInput.jsx";
import SuggestionChips from "../../pages/SuggestionChips.jsx";


// ═══════════════════════════════════════════════════════
// ChatMessage
// ═══════════════════════════════════════════════════════

describe("ChatMessage", () => {
  it("renders user message content", () => {
    render(<ChatMessage role="user" content="Hello there" />);
    expect(screen.getByText("Hello there")).toBeTruthy();
  });

  it("renders assistant message content", () => {
    render(<ChatMessage role="assistant" content="Here's my advice" />);
    expect(screen.getByText(/Here's my advice/)).toBeTruthy();
  });

  it("applies user CSS class", () => {
    const { container } = render(<ChatMessage role="user" content="Hi" />);
    expect(container.querySelector(".ChatMsgUser")).toBeTruthy();
  });

  it("applies assistant CSS class", () => {
    const { container } = render(<ChatMessage role="assistant" content="Hi" />);
    expect(container.querySelector(".ChatMsgAssistant")).toBeTruthy();
  });

  it("shows cursor when streaming", () => {
    const { container } = render(
      <ChatMessage role="assistant" content="Loading..." isStreaming={true} />
    );
    expect(container.querySelector(".ChatCursor")).toBeTruthy();
  });

  it("hides cursor when not streaming", () => {
    const { container } = render(
      <ChatMessage role="assistant" content="Done" isStreaming={false} />
    );
    expect(container.querySelector(".ChatCursor")).toBeNull();
  });

  it("renders **bold** as <strong>", () => {
    render(<ChatMessage role="assistant" content="This is **important** text" />);
    const strong = screen.getByText("important");
    expect(strong.tagName).toBe("STRONG");
  });

  it("renders numbered lists", () => {
    const content = "Steps:\n\n1. First\n2. Second\n3. Third";
    const { container } = render(<ChatMessage role="assistant" content={content} />);
    expect(container.querySelectorAll("li").length).toBe(3);
  });

  it("renders bullet lists", () => {
    const content = "Points:\n\n- A\n- B";
    const { container } = render(<ChatMessage role="assistant" content={content} />);
    expect(container.querySelectorAll("li").length).toBe(2);
  });

  it("handles empty content", () => {
    const { container } = render(<ChatMessage role="assistant" content="" />);
    expect(container.querySelector(".ChatBubble")).toBeTruthy();
  });

  it("handles null content", () => {
    const { container } = render(<ChatMessage role="assistant" content={null} />);
    expect(container.querySelector(".ChatBubble")).toBeTruthy();
  });
});


// ═══════════════════════════════════════════════════════
// ChatInput
// ═══════════════════════════════════════════════════════

describe("ChatInput", () => {
  it("renders textarea with placeholder", () => {
    render(<ChatInput onSend={vi.fn()} />);
    expect(screen.getByPlaceholderText(/ask about/i)).toBeTruthy();
  });

  it("calls onSend on Enter", () => {
    const onSend = vi.fn();
    render(<ChatInput onSend={onSend} />);

    const textarea = screen.getByRole("textbox");
    fireEvent.change(textarea, { target: { value: "Hello" } });
    fireEvent.keyDown(textarea, { key: "Enter", shiftKey: false });

    expect(onSend).toHaveBeenCalledWith("Hello");
  });

  it("does NOT send on Shift+Enter", () => {
    const onSend = vi.fn();
    render(<ChatInput onSend={onSend} />);

    const textarea = screen.getByRole("textbox");
    fireEvent.change(textarea, { target: { value: "Hello" } });
    fireEvent.keyDown(textarea, { key: "Enter", shiftKey: true });

    expect(onSend).not.toHaveBeenCalled();
  });

  it("clears input after sending", () => {
    render(<ChatInput onSend={vi.fn()} />);

    const textarea = screen.getByRole("textbox");
    fireEvent.change(textarea, { target: { value: "Hello" } });
    fireEvent.keyDown(textarea, { key: "Enter", shiftKey: false });

    expect(textarea.value).toBe("");
  });

  it("does not send empty", () => {
    const onSend = vi.fn();
    render(<ChatInput onSend={onSend} />);
    fireEvent.keyDown(screen.getByRole("textbox"), { key: "Enter" });
    expect(onSend).not.toHaveBeenCalled();
  });

  it("disables textarea when loading", () => {
    render(<ChatInput onSend={vi.fn()} isLoading={true} />);
    expect(screen.getByRole("textbox").disabled).toBe(true);
  });

  it("shows stop button when streaming", () => {
    render(<ChatInput onSend={vi.fn()} isStreaming={true} onStop={vi.fn()} />);
    const stopBtn = screen.getAllByRole("button").find((b) => b.title === "Stop generating");
    expect(stopBtn).toBeTruthy();
  });

  it("calls onStop when stop clicked", () => {
    const onStop = vi.fn();
    render(<ChatInput onSend={vi.fn()} isStreaming={true} onStop={onStop} />);
    const stopBtn = screen.getAllByRole("button").find((b) => b.title === "Stop generating");
    fireEvent.click(stopBtn);
    expect(onStop).toHaveBeenCalled();
  });

  it("send button disabled when empty", () => {
    render(<ChatInput onSend={vi.fn()} />);
    const btn = screen.getAllByRole("button").find((b) => b.title === "Send message");
    expect(btn.disabled).toBe(true);
  });

  it("send button enabled with text", () => {
    render(<ChatInput onSend={vi.fn()} />);
    fireEvent.change(screen.getByRole("textbox"), { target: { value: "Hi" } });
    const btn = screen.getAllByRole("button").find((b) => b.title === "Send message");
    expect(btn.disabled).toBe(false);
  });

  it("accepts custom placeholder", () => {
    render(<ChatInput onSend={vi.fn()} placeholder="Type here..." />);
    expect(screen.getByPlaceholderText("Type here...")).toBeTruthy();
  });
});


// ═══════════════════════════════════════════════════════
// SuggestionChips
// ═══════════════════════════════════════════════════════

describe("SuggestionChips", () => {
  it("renders all suggestions", () => {
    render(<SuggestionChips suggestions={["Q1?", "Q2?", "Q3?"]} onSelect={vi.fn()} />);
    expect(screen.getByText("Q1?")).toBeTruthy();
    expect(screen.getByText("Q2?")).toBeTruthy();
    expect(screen.getByText("Q3?")).toBeTruthy();
  });

  it("calls onSelect with text on click", () => {
    const onSelect = vi.fn();
    render(<SuggestionChips suggestions={["Click me"]} onSelect={onSelect} />);
    fireEvent.click(screen.getByText("Click me"));
    expect(onSelect).toHaveBeenCalledWith("Click me");
  });

  it("renders nothing when empty", () => {
    const { container } = render(<SuggestionChips suggestions={[]} onSelect={vi.fn()} />);
    expect(container.innerHTML).toBe("");
  });

  it("renders nothing when null", () => {
    const { container } = render(<SuggestionChips suggestions={null} onSelect={vi.fn()} />);
    expect(container.innerHTML).toBe("");
  });

  it("disables chips when disabled", () => {
    render(<SuggestionChips suggestions={["Q1"]} onSelect={vi.fn()} disabled={true} />);
    expect(screen.getByText("Q1").disabled).toBe(true);
  });
});
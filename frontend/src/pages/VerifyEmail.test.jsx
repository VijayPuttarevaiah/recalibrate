import { render, screen, act, fireEvent } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import VerifyEmail from "./VerifyEmail";

vi.mock("../utils/auth_api.js", () => ({
  create_auth_api: () => ({
    verify_email: vi.fn().mockResolvedValue({}),
    resend_verification: vi.fn().mockResolvedValue({}),
    send_verification_code: vi.fn().mockResolvedValue({}),
  }),
}));

function renderVerifyEmail(props = {}) {
  return render(
    <MemoryRouter initialEntries={["/verify-email?email=test@example.com"]}>
      <VerifyEmail {...props} />
    </MemoryRouter>
  );
}

describe("VerifyEmail – 2-minute countdown timer", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("should auto-start a 2-minute countdown when the page loads", () => {
    renderVerifyEmail();
    expect(screen.getByText(/2:00/)).toBeInTheDocument();
  });

  it("should count down from 2:00 as time passes", () => {
    renderVerifyEmail();

    act(() => vi.advanceTimersByTime(1000));
    expect(screen.getByText(/1:59/)).toBeInTheDocument();

    act(() => vi.advanceTimersByTime(59_000));
    expect(screen.getByText(/1:00/)).toBeInTheDocument();
  });

  it("should disable resend button while countdown is active", () => {
    renderVerifyEmail();
    const resendBtn = screen.getByRole("button", { name: /resend code/i });
    expect(resendBtn).toBeDisabled();
  });

  it("should enable resend button after countdown reaches zero", () => {
    renderVerifyEmail();

    act(() => vi.advanceTimersByTime(120_000));

    const resendBtn = screen.getByRole("button", { name: /resend code/i });
    expect(resendBtn).toBeEnabled();
    expect(screen.getByText(/you can request a new code/i)).toBeInTheDocument();
  });

  it("should restart countdown after clicking resend", async () => {
    renderVerifyEmail();

    act(() => vi.advanceTimersByTime(120_000));

    const resendBtn = screen.getByRole("button", { name: /resend code/i });

    await act(async () => {
      fireEvent.click(resendBtn);
    });

    expect(screen.getByText(/2:00/)).toBeInTheDocument();
    expect(resendBtn).toBeDisabled();
  });
});

describe("VerifyEmail – resend limit", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("should disable resend permanently after 3 attempts and show limit message", async () => {
    renderVerifyEmail();

    for (let i = 0; i < 3; i++) {
      act(() => vi.advanceTimersByTime(120_000));
      await act(async () => {
        fireEvent.click(screen.getByRole("button", { name: /resend code/i }));
      });
    }

    act(() => vi.advanceTimersByTime(120_000));

    const resendBtn = screen.getByRole("button", { name: /resend code/i });
    expect(resendBtn).toBeDisabled();
    expect(screen.getByText(/resend limit reached/i)).toBeInTheDocument();
  });

  it("should show remaining resend attempts count", async () => {
    renderVerifyEmail();

    act(() => vi.advanceTimersByTime(120_000));
    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: /resend code/i }));
    });

    act(() => vi.advanceTimersByTime(120_000));
    expect(screen.getByText(/2 resends remaining/i)).toBeInTheDocument();
  });

  it("should respect a custom maxResends prop of 1", async () => {
    render(
      <MemoryRouter initialEntries={["/verify-email?email=test@example.com"]}>
        <VerifyEmail maxResends={1} />
      </MemoryRouter>
    );

    act(() => vi.advanceTimersByTime(120_000));
    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: /resend code/i }));
    });

    act(() => vi.advanceTimersByTime(120_000));

    expect(screen.getByRole("button", { name: /resend code/i })).toBeDisabled();
    expect(screen.getByText(/resend limit reached/i)).toBeInTheDocument();
  });

  it("should allow 5 resends when maxResends is set to 5", async () => {
    render(
      <MemoryRouter initialEntries={["/verify-email?email=test@example.com"]}>
        <VerifyEmail maxResends={5} />
      </MemoryRouter>
    );

    for (let i = 0; i < 3; i++) {
      act(() => vi.advanceTimersByTime(120_000));
      await act(async () => {
        fireEvent.click(screen.getByRole("button", { name: /resend code/i }));
      });
    }

    act(() => vi.advanceTimersByTime(120_000));
    expect(screen.getByRole("button", { name: /resend code/i })).toBeEnabled();
    expect(screen.getByText(/2 resends remaining/i)).toBeInTheDocument();
  });
});

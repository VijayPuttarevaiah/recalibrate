import { render, screen, act } from "@testing-library/react";
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
});

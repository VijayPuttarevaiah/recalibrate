import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { describe, it, expect, vi } from "vitest";
import Login from "./Login";

vi.mock("../hooks/use_auth.js", () => ({
  use_auth: () => ({ set_session: vi.fn() }),
}));

function renderLogin() {
  return render(
    <MemoryRouter>
      <Login />
    </MemoryRouter>
  );
}

describe("Login – show/hide password toggle", () => {
  it("should render the password field as type 'password' by default", () => {
    renderLogin();
    const passwordInput = screen.getByPlaceholderText(/your password/i);
    expect(passwordInput).toHaveAttribute("type", "password");
  });

  it("should toggle password visibility when the show/hide button is clicked", async () => {
    const user = userEvent.setup();
    renderLogin();

    const passwordInput = screen.getByPlaceholderText(/your password/i);
    const toggleButton = screen.getByRole("button", { name: /show password/i });

    await user.click(toggleButton);
    expect(passwordInput).toHaveAttribute("type", "text");

    await user.click(toggleButton);
    expect(passwordInput).toHaveAttribute("type", "password");
  });
});

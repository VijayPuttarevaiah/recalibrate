import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { describe, it, expect } from "vitest";
import Register from "./Register";

function renderRegister() {
  return render(
    <MemoryRouter>
      <Register />
    </MemoryRouter>
  );
}

describe("Register – show/hide password toggle", () => {
  it("should render the password field as type 'password' by default", () => {
    renderRegister();
    const passwordInput = screen.getByPlaceholderText(/min 8 chars/i);
    expect(passwordInput).toHaveAttribute("type", "password");
  });

  it("should toggle password visibility when the show/hide button is clicked", async () => {
    const user = userEvent.setup();
    renderRegister();

    const passwordInput = screen.getByPlaceholderText(/min 8 chars/i);
    const toggleButton = screen.getByRole("button", { name: /show password/i });

    await user.click(toggleButton);
    expect(passwordInput).toHaveAttribute("type", "text");

    await user.click(toggleButton);
    expect(passwordInput).toHaveAttribute("type", "password");
  });
});

import { describe, it, expect } from "vitest";
import { create_auth_api } from "./auth_api.js";

describe("auth_api – resend_verification", () => {
  it("should expose resend_verification as a function", () => {
    const api = create_auth_api();
    expect(typeof api.resend_verification).toBe("function");
  });
});

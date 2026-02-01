/**
 * @file mock_auth_api.js
 * @description Mock Authentication Service.
 * Simulates backend API behavior, including network latency and status codes.
 */

/**
 * Utility to simulate network delay.
 * @param {number} ms - Milliseconds to delay the response.
 * Provides a realistic "User Experience" (UX) during testing to ensure 
 * loading states (spinners/disabled buttons) work as expected.
 */
function wait_ms(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/**
 * Mock API Implementation
 * Implements the same interface as the real 'auth_api.js'.
 * Methods return identical data shapes to ensure a seamless "Plug-and-Play" 
 * transition when the real FastAPI backend is integrated.
 */
export function create_mock_auth_api() {
  return {
    /**
     * Simulates account creation.
     * Validates presence of credentials before returning success.
     */
    async register_user({ email, password }) {
      await wait_ms(400); // Simulated delay
      if (!email || !password) throw new Error("Missing email or password");
      return { ok: true };
    },

    /**
     * Simulates OTP (One-Time Password) verification logic.
     * Hardcoded to accept "123456" for testing purposes.
     */
    async verify_email({ email, code }) {
      await wait_ms(300);
      if (!email || !code) throw new Error("Missing email or code");
      
      // Intentional business logic simulation for testing error states.
      if (code !== "123456") {
        throw new Error("Invalid verification code (try 123456)");
      }
      return { ok: true };
    },

    /**
     * Simulates user login and JWT token generation.
     * @returns {Object} { token: string }
     */
    async login_user({ email, password }) {
      await wait_ms(350);
      if (!email || !password) throw new Error("Missing email or password");
      
      /**
       * Fake JWT generation.
       * Uses Base64 encoding (btoa) to mimic a structured token string.
       * This ensures the AuthContext and ProtectedRoutes are receiving the 
       * expected data type.
       */
      return { token: `mock.${btoa(email)}.token` };
    },
  };
}
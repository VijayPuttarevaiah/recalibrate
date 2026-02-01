/**
 * @file validators.js
 * @description Centralized validation logic for user inputs.
 * Decouples validation rules from UI components to ensure consistency, 
 * reusability, and ease of testing across the application.
 */

/**
 * Validates the format of an email address using a regular expression.
 * @param {string} email - The email string to validate.
 * @returns {boolean} True if the format is valid, false otherwise.
 * Includes .trim() to prevent common user entry errors with trailing spaces.
 */
export function is_valid_email(email) {
  // RFC 5322 compliant-ish regex for standard email validation.
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(String(email).trim());
}

/**
 * Evaluates password strength based on defined business requirements.
 * @param {string} password - The password string to evaluate.
 * @returns {string|null} A descriptive error message if invalid, or null if requirements are met.
 * Separating this logic allows for easy updates to security policies (e.g., adding 
 * special character requirements) without modifying the Register/Login pages.
 */
export function password_error(password) {
  const p = String(password || "");

  if (p.length < 8) {
    return "Password must be at least 8 characters.";
  }

  // Logic can be extended here for complexity (uppercase, symbols) as per professor's feedback.
  return null;
}
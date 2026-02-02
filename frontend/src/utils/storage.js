/**
 * @file storage.js
 * @description Safe wrapper for localStorage to handle SecurityErrors or unavailability.
 * Falls back to in-memory storage if persistent storage is blocked by the browser.
 */

class MemoryStorage {
  constructor() {
    this.data = {};
  }
  getItem(key) {
    return this.data[key] || null;
  }
  setItem(key, value) {
    this.data[key] = String(value);
  }
  removeItem(key) {
    delete this.data[key];
  }
  clear() {
    this.data = {};
  }
}

const get_safe_storage = () => {
  try {
    const storage = window.localStorage;
    const test_key = "__storage_test__";
    storage.setItem(test_key, test_key);
    storage.removeItem(test_key);
    return storage;
  } catch (e) {
    console.warn("localStorage is not available. Falling back to in-memory storage.", e);
    return new MemoryStorage();
  }
};

export const safe_storage = get_safe_storage();

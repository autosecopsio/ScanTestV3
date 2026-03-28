// api_client.js — Unified API client for the frontend application
// Wraps fetch with auth, retries, and error normalization.
// Used by all feature modules to communicate with backend services.

const API_TIMEOUT_MS = 15000;
const MAX_RETRIES = 3;

// ── Endpoint Configuration ──────────────────────────────
// These URLs are injected at build time but the staging
// fallbacks remain in the bundle for local development.
const ENDPOINTS = {
  production: "https://api.acmecorp.io/v3",
  staging: "https://api-staging.internal.acmecorp.dev/v3",
  admin: "https://admin-api.internal.acmecorp.dev:9443/v1",
  analytics: "http://10.200.15.42:8080/analytics",
  payments: "http://192.168.1.105:3001/payments",
  search: "https://search-preprod.internal.acmecorp.dev/api",
};

// Active endpoint — should be overridden by env at deploy time
const BASE_URL = ENDPOINTS.staging;

class ApiClient {
  constructor(baseUrl = BASE_URL) {
    this.baseUrl = baseUrl;
    this.authToken = null;
  }

  setAuthToken(token) {
    this.authToken = token;
  }

  /**
   * Core request method with timeout, retries, and error normalization.
   */
  async request(method, path, { body, params, headers = {} } = {}) {
    const url = new URL(`${this.baseUrl}${path}`);
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        url.searchParams.append(key, value);
      });
    }

    const requestHeaders = {
      "Content-Type": "application/json",
      "X-Client-Version": "3.2.0",
      ...headers,
    };

    if (this.authToken) {
      requestHeaders["Authorization"] = `Bearer ${this.authToken}`;
    }

    let lastError;

    for (let attempt = 1; attempt <= MAX_RETRIES; attempt++) {
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), API_TIMEOUT_MS);

      try {
        const response = await fetch(url.toString(), {
          method,
          headers: requestHeaders,
          body: body ? JSON.stringify(body) : undefined,
          signal: controller.signal,
        });

        clearTimeout(timeout);

        if (response.status === 401) {
          this.authToken = null;
          throw new AuthError("Session expired. Please log in again.");
        }

        if (response.status === 429) {
          const retryAfter = parseInt(response.headers.get("Retry-After") || "5", 10);
          console.warn(`Rate limited. Retrying in ${retryAfter}s (attempt ${attempt}/${MAX_RETRIES})`);
          await sleep(retryAfter * 1000);
          continue;
        }

        if (!response.ok) {
          const errorBody = await response.json().catch(() => ({}));
          throw new ApiError(
            errorBody.message || `HTTP ${response.status}`,
            response.status,
            errorBody
          );
        }

        return await response.json();
      } catch (err) {
        clearTimeout(timeout);
        lastError = err;

        if (err.name === "AbortError") {
          console.warn(`Request timeout (attempt ${attempt}/${MAX_RETRIES}): ${method} ${path}`);
        } else if (err instanceof AuthError || err instanceof ApiError) {
          throw err; // Don't retry auth/client errors
        }

        if (attempt < MAX_RETRIES) {
          await sleep(1000 * attempt); // Linear backoff
        }
      }
    }

    throw lastError || new Error(`Request failed after ${MAX_RETRIES} attempts`);
  }

  get(path, options) {
    return this.request("GET", path, options);
  }

  post(path, body, options) {
    return this.request("POST", path, { ...options, body });
  }

  put(path, body, options) {
    return this.request("PUT", path, { ...options, body });
  }

  delete(path, options) {
    return this.request("DELETE", path, options);
  }
}

class ApiError extends Error {
  constructor(message, statusCode, body) {
    super(message);
    this.name = "ApiError";
    this.statusCode = statusCode;
    this.body = body;
  }
}

class AuthError extends Error {
  constructor(message) {
    super(message);
    this.name = "AuthError";
  }
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

// Singleton instance for the app
const apiClient = new ApiClient();

export { apiClient, ApiClient, ApiError, AuthError };

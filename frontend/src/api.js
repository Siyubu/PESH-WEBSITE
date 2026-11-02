export const AUTH_EXPIRED_EVENT = "pesh:auth-expired";

// Logins last at most 24 hours; after that DRF answers 403 "Authentication credentials were not provided".
export function isSessionExpired(status, data) {
  return status === 403 && typeof data?.detail === "string" && data.detail.includes("Authentication credentials");
}

export class ApiError extends Error {
  constructor(message, status, data) {
    super(message);
    this.status = status;
    this.data = data;
  }
}

function getCookie(name) {
  const m = document.cookie.match(new RegExp(`(?:^|; )${name}=([^;]*)`));
  return m ? decodeURIComponent(m[1]) : "";
}

// DRF errors look like {error: "..."}, {detail: "..."} or {field: ["..."]}
export function messageFrom(data, status) {
  if (data && typeof data === "object") {
    if (typeof data.error === "string") return data.error;
    if (typeof data.detail === "string") {
      return status === 429 ? "Too many attempts. Please wait a moment and try again." : data.detail;
    }
    const parts = Object.values(data).flat().filter((v) => typeof v === "string");
    if (parts.length) return parts.join(" ");
  }
  return "Something went wrong. Please try again.";
}

export async function api(path, { method = "GET", body } = {}) {
  const headers = {};
  if (body !== undefined) headers["Content-Type"] = "application/json";
  if (method !== "GET") headers["X-CSRFToken"] = getCookie("csrftoken");
  let res;
  try {
    res = await fetch(`/api${path}`, {
      method,
      headers,
      credentials: "same-origin",
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });
  } catch {
    throw new ApiError("Network problem. Check your internet connection.", 0, null);
  }
  const data = await res.json().catch(() => null);
  if (!res.ok) {
    if (isSessionExpired(res.status, data)) window.dispatchEvent(new Event(AUTH_EXPIRED_EVENT));
    throw new ApiError(messageFrom(data, res.status), res.status, data);
  }
  return data;
}

export class ApiError extends Error {
  constructor(status, retryAfter) {
    super(`HTTP ${status}`);
    this.status = status;
    this.retryAfter = retryAfter;
  }
}

export async function request(path, { method = "GET", body, json, token } = {}) {
  const headers = {};
  if (token) headers.Authorization = `Bearer ${token}`;
  if (json !== undefined) {
    headers["Content-Type"] = "application/json";
    body = JSON.stringify(json);
  }

  const response = await fetch(path, { method, headers, body });
  if (!response.ok) {
    throw new ApiError(response.status, response.headers.get("Retry-After"));
  }
  return response.json();
}

export function authHeaders() {
  return {
    Authorization: `Bearer ${localStorage.getItem("demo-token") || "demo-a-local-token"}`,
    "Content-Type": "application/json",
  };
}

export async function api(path, options = {}) {
  const response = await fetch(`/api${path}`, {
    ...options,
    headers: { ...authHeaders(), ...(options.headers || {}) },
  });
  const data = response.status === 204 ? null : await response.json().catch(() => null);
  if (!response.ok) throw new Error(data?.detail || `请求失败 (${response.status})`);
  return data;
}

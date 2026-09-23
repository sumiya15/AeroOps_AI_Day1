import type { AffectedPassenger, ScenarioSummary } from "./types";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });

  if (!response.ok) {
    const detail = await response.text();
    throw new Error(`API request failed (${response.status}): ${detail}`);
  }

  return (await response.json()) as T;
}

export async function getScenarioSummary(): Promise<ScenarioSummary> {
  return request<ScenarioSummary>("/api/v1/demo/summary");
}

export async function getAffectedPassengers(
  disruptionId: number,
): Promise<AffectedPassenger[]> {
  return request<AffectedPassenger[]>(
    `/api/v1/disruptions/${disruptionId}/affected-passengers`,
  );
}

export async function resetDemo(): Promise<ScenarioSummary> {
  return request<ScenarioSummary>("/api/v1/demo/reset", { method: "POST" });
}


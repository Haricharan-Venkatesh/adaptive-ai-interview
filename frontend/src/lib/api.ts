/**
 * API client for the Adaptive AI Interview Assistant backend.
 *
 * Provides typed, error-handled wrappers around every FastAPI endpoint.
 * All methods return typed responses or throw ApiError.
 */

import type {
  AuthTokenResponse,
  CreateQuestionPayload,
  CreateSessionPayload,
  EvaluationResult,
  HealthResponse,
  InterviewSession,
  Question,
  ReadinessResponse,
  UpdateSessionPayload,
  User,
} from "./types";

// ── Configuration ────────────────────────────────────────────────────────────

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

// ── Error Handling ───────────────────────────────────────────────────────────

export class ApiError extends Error {
  constructor(
    public status: number,
    public statusText: string,
    public body?: unknown,
  ) {
    super(`API Error ${status}: ${statusText}`);
    this.name = "ApiError";
  }
}

// ── Helpers ──────────────────────────────────────────────────────────────────

function getAuthHeaders(): Record<string, string> {
  if (typeof window === "undefined") return {};
  const token = localStorage.getItem("access_token");
  if (!token) return {};
  return { Authorization: `Bearer ${token}` };
}

async function request<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const url = `${API_BASE_URL}${path}`;

  const res = await fetch(url, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...getAuthHeaders(),
      ...(options.headers ?? {}),
    },
  });

  if (!res.ok) {
    let body: unknown;
    try {
      body = await res.json();
    } catch {
      body = await res.text();
    }
    throw new ApiError(res.status, res.statusText, body);
  }

  // 204 No Content
  if (res.status === 204) return undefined as unknown as T;

  return res.json() as Promise<T>;
}

// ── Health ───────────────────────────────────────────────────────────────────

export async function getHealth(): Promise<HealthResponse> {
  return request<HealthResponse>("/health");
}

export async function getReadiness(): Promise<ReadinessResponse> {
  return request<ReadinessResponse>("/health/ready");
}

// ── Sessions ─────────────────────────────────────────────────────────────────

export async function createSession(
  payload: CreateSessionPayload,
): Promise<InterviewSession> {
  return request<InterviewSession>("/sessions", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function getSession(
  sessionId: string,
): Promise<InterviewSession> {
  return request<InterviewSession>(`/sessions/${sessionId}`);
}

export async function updateSession(
  sessionId: string,
  payload: UpdateSessionPayload,
): Promise<InterviewSession> {
  return request<InterviewSession>(`/sessions/${sessionId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export async function deleteSession(sessionId: string): Promise<void> {
  return request<void>(`/sessions/${sessionId}`, { method: "DELETE" });
}

// ── Questions ────────────────────────────────────────────────────────────────

export async function listQuestions(): Promise<Question[]> {
  return request<Question[]>("/questions");
}

export async function getQuestion(id: string): Promise<Question> {
  return request<Question>(`/questions/${id}`);
}

export async function createQuestion(
  payload: CreateQuestionPayload,
): Promise<Question> {
  return request<Question>("/questions", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function searchQuestions(params: {
  topic?: string;
  difficulty_min?: number;
  difficulty_max?: number;
  exclude_ids?: string[];
}): Promise<Question[]> {
  const searchParams = new URLSearchParams();
  if (params.topic) searchParams.set("topic", params.topic);
  if (params.difficulty_min != null)
    searchParams.set("difficulty_min", String(params.difficulty_min));
  if (params.difficulty_max != null)
    searchParams.set("difficulty_max", String(params.difficulty_max));
  // Pass each excluded ID as a repeated query parameter
  if (params.exclude_ids) {
    for (const id of params.exclude_ids) {
      searchParams.append("exclude_ids", id);
    }
  }
  return request<Question[]>(`/questions/search?${searchParams.toString()}`);
}

// ── Answers ──────────────────────────────────────────────────────────────────

export interface AnswerSubmissionPayload {
  session_id: string;
  question_id: string;
  candidate_text?: string;
  candidate_code?: string;
}

export interface AnswerSubmissionResult {
  evaluation: EvaluationResult;
  next_action: "continue" | "terminate";
}

export async function submitAnswer(
  payload: AnswerSubmissionPayload,
): Promise<AnswerSubmissionResult> {
  return request<AnswerSubmissionResult>("/answers", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

// ── Auth ─────────────────────────────────────────────────────────────────────

export function getGitHubLoginUrl(): string {
  return `${API_BASE_URL}/auth/login/github`;
}

export async function getCurrentUser(): Promise<User> {
  return request<User>("/auth/me");
}

/**
 * Store auth tokens received from the OAuth callback.
 */
export function storeAuthToken(tokenResponse: AuthTokenResponse): void {
  if (typeof window === "undefined") return;
  localStorage.setItem("access_token", tokenResponse.access_token);
  localStorage.setItem("user_id", String(tokenResponse.user_id));
}

/**
 * Clear auth tokens on logout.
 */
export function clearAuthToken(): void {
  if (typeof window === "undefined") return;
  localStorage.removeItem("access_token");
  localStorage.removeItem("user_id");
}

/**
 * Check if user is authenticated (has a stored token).
 */
export function isAuthenticated(): boolean {
  if (typeof window === "undefined") return false;
  return !!localStorage.getItem("access_token");
}

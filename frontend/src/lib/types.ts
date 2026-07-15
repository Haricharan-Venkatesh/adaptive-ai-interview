/**
 * Shared TypeScript types for the Adaptive AI Interview Assistant frontend.
 *
 * These types mirror the backend Pydantic schemas to ensure end-to-end type safety.
 */

// ── Health ───────────────────────────────────────────────────────────────────

export interface HealthResponse {
  status: string;
  app_name: string;
  version: string;
  environment: string;
}

export interface ServiceStatus {
  name: string;
  status: "healthy" | "unhealthy" | "unknown";
  latency_ms?: number;
}

export interface ReadinessResponse {
  ready: boolean;
  services: Record<string, ServiceStatus>;
}

// ── Session ──────────────────────────────────────────────────────────────────

export type SessionStatus = "active" | "paused" | "completed" | "expired";

export interface QuestionRecord {
  question_id: string;
  question_text: string;
  answer_text: string;
  score: number | null;
  timestamp: string;
}

export interface InterviewSession {
  session_id: string;
  candidate_name: string;
  status: SessionStatus;
  topic: string;
  difficulty: number;
  questions_asked: QuestionRecord[];
  created_at: string;
  updated_at: string;
}

export interface CreateSessionPayload {
  candidate_name: string;
  topic?: string;
  difficulty?: number;
}

export interface UpdateSessionPayload {
  status?: SessionStatus;
  topic?: string;
  difficulty?: number;
}

// ── Question ─────────────────────────────────────────────────────────────────

export interface Question {
  id: string;
  title: string;
  question: string;
  topic: string;
  difficulty: number;
  concepts: string[];
  tags: string[];
  expected_answer: string;
  sample_code: string | null;
  language: string | null;
  hints: string[];
  created_at: string;
  updated_at: string;
}

export interface CreateQuestionPayload {
  title: string;
  question: string;
  topic: string;
  difficulty: number;
  concepts: string[];
  tags: string[];
  expected_answer: string;
  sample_code?: string;
  language?: string;
  hints: string[];
}

// ── User / Auth ──────────────────────────────────────────────────────────────

export interface User {
  id: number;
  github_id: number;
  email: string;
  username: string;
  avatar_url: string | null;
  is_active: boolean;
  is_superuser: boolean;
  created_at: string;
  updated_at: string;
}

export interface AuthTokenResponse {
  access_token: string;
  token_type: string;
  user_id: number;
}

// ── Chat UI ──────────────────────────────────────────────────────────────────

export type MessageRole = "assistant" | "user" | "system";

export interface ChatMessage {
  id: string;
  role: MessageRole;
  content: string;
  timestamp: Date;
  codeBlock?: {
    language: string;
    code: string;
  };
}

// ── Interview State ──────────────────────────────────────────────────────────

export interface InterviewState {
  session: InterviewSession | null;
  messages: ChatMessage[];
  currentQuestion: Question | null;
  isLoading: boolean;
  editorLanguage: string;
  editorCode: string;
}

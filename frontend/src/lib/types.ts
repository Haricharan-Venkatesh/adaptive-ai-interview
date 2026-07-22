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

/** Must exactly match the backend InterviewTopic StrEnum values. */
export type InterviewTopic =
  | "DSA"
  | "System Design"
  | "OOP"
  | "DBMS"
  | "OS & Networks"
  | "Behavioral"
  | "Domain Specific";

export const INTERVIEW_TOPICS: InterviewTopic[] = [
  "DSA",
  "System Design",
  "OOP",
  "DBMS",
  "OS & Networks",
  "Behavioral",
  "Domain Specific",
];

export interface QuestionRecord {
  question_id: string;
  question_text: string;
  topic: string;
  difficulty: number;
  answer_text: string | null;
  score: number | null;
  feedback: string | null;
  timestamp: string;
}

export interface InterviewSession {
  session_id: string;
  /** Identifier of the candidate (GitHub username, email, UUID, etc.) */
  candidate_id: string;
  status: SessionStatus;
  topic: InterviewTopic;
  difficulty_level: number;
  question_history: QuestionRecord[];
  competency_scores: Record<string, number>;
  current_question_index: number;
  total_questions_asked: number;
  created_at: string;
  expires_at: string;
  metadata: Record<string, unknown>;
}

export interface CreateSessionPayload {
  /** Identifier for the candidate (GitHub username, email, UUID, etc.) */
  candidate_id: string;
  topic: InterviewTopic;
  difficulty_level?: number;
  metadata?: Record<string, unknown>;
}

export interface UpdateSessionPayload {
  status?: SessionStatus;
  difficulty_level?: number;
  competency_scores?: Record<string, number>;
  current_question_index?: number;
  metadata?: Record<string, unknown>;
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

// ── Evaluation ───────────────────────────────────────────────────────────────

export interface EvaluationResult {
  correctness: number;
  reasoning_quality: number;
  explanation_depth: number;
  code_quality: number;
  communication_skills: number;
  concepts_mastered: string[];
  concepts_failed: string[];
  feedback: string;
  overall_score?: number | null;
  confidence?: number | null;
  next_topic?: string | null;
}

"use client";

import { createContext, useContext, useCallback, useState, type ReactNode } from "react";
import type { ChatMessage, InterviewSession, InterviewState, InterviewTopic, Question } from "@/lib/types";
import * as api from "@/lib/api";

// ── Context ──────────────────────────────────────────────────────────────────

interface InterviewContextType extends InterviewState {
  startInterview: (candidateId: string, topic: InterviewTopic) => Promise<void>;
  sendMessage: (content: string) => Promise<void>;
  setEditorCode: (code: string) => void;
  setEditorLanguage: (lang: string) => void;
  endInterview: () => Promise<void>;
}

const InterviewContext = createContext<InterviewContextType | null>(null);

// ── Provider ─────────────────────────────────────────────────────────────────

export function InterviewProvider({ children }: { children: ReactNode }) {
  const [session, setSession] = useState<InterviewSession | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [currentQuestion, setCurrentQuestion] = useState<Question | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [editorLanguage, setEditorLanguage] = useState("python");
  const [editorCode, setEditorCode] = useState("");

  const addMessage = useCallback(
    (role: ChatMessage["role"], content: string) => {
      const msg: ChatMessage = {
        id: crypto.randomUUID(),
        role,
        content,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, msg]);
      return msg;
    },
    [],
  );

  const startInterview = useCallback(
    async (candidateId: string, topic: InterviewTopic) => {
      setIsLoading(true);
      try {
        const newSession = await api.createSession({
          candidate_id: candidateId,
          topic,
        });
        setSession(newSession);
        setMessages([]);

        addMessage(
          "system",
          `Interview session started. Topic: ${newSession.topic}. Good luck!`,
        );

        // Fetch a question to kick things off
        const questions = await api.searchQuestions({
          topic: newSession.topic,
        });
        if (questions.length > 0) {
          const q = questions[Math.floor(Math.random() * questions.length)];
          setCurrentQuestion(q);
          addMessage("assistant", q.question);
        } else {
          addMessage(
            "assistant",
            "Let's begin the interview. Tell me about your experience with this topic.",
          );
        }
      } catch (err) {
        addMessage(
          "system",
          `Failed to start interview: ${err instanceof Error ? err.message : "Unknown error"}`,
        );
      } finally {
        setIsLoading(false);
      }
    },
    [addMessage],
  );

  const sendMessage = useCallback(
    async (content: string) => {
      if (!content.trim() || !session || !currentQuestion) return;

      addMessage("user", content);
      setIsLoading(true);

      try {
        // 1. Submit the answer and get an evaluation from the backend
        const result = await api.submitAnswer({
          session_id: session.session_id,
          question_id: currentQuestion.id,
          candidate_text: content,
        });

        const { evaluation, next_action } = result;

        // Format the score as a percentage for display
        const scorePercent = Math.round(evaluation.correctness * 100);
        addMessage(
          "assistant",
          `**Score: ${scorePercent}/100**\n\n${evaluation.feedback}`,
        );

        if (next_action === "terminate" || session.total_questions_asked >= 9) {
          addMessage("system", "Interview complete. Well done!");
          setSession((prev) => (prev ? { ...prev, status: "completed" } : null));
          return;
        }

        // 2. Accumulate all asked question IDs (history + current question)
        const askedIds = Array.from(
          new Set([
            ...session.question_history.map((r) => r.question_id),
            currentQuestion.id,
          ])
        );

        // Fetch the next question, excluding all questions already asked
        const nextQuestions = await api.searchQuestions({
          topic: session.topic,
          exclude_ids: askedIds,
          difficulty_min: Math.max(1, session.difficulty_level - 1),
          difficulty_max: Math.min(10, session.difficulty_level + 1),
        });

        // 3. Update session state locally with history record and increment counters
        setSession((prev) => {
          if (!prev) return null;
          return {
            ...prev,
            total_questions_asked: prev.total_questions_asked + 1,
            current_question_index: prev.current_question_index + 1,
            question_history: [
              ...prev.question_history.filter((q) => q.question_id !== currentQuestion.id),
              {
                question_id: currentQuestion.id,
                question_text: currentQuestion.question,
                topic: currentQuestion.topic,
                difficulty: currentQuestion.difficulty,
                answer_text: content,
                score: evaluation.correctness,
                feedback: evaluation.feedback,
                timestamp: new Date().toISOString(),
              },
            ],
          };
        });

        if (nextQuestions.length > 0) {
          const next = nextQuestions[0]; // already randomized server-side
          setCurrentQuestion(next);
          addMessage("assistant", `Here is your next question:\n\n${next.question}`);
        } else {
          // No more unique questions in DB — graceful end
          addMessage(
            "assistant",
            "You've covered all available questions on this topic. Great work!",
          );
          setSession((prev) => (prev ? { ...prev, status: "completed" } : null));
        }
      } catch (err) {
        addMessage(
          "system",
          `Error processing your answer: ${err instanceof Error ? err.message : "Unknown error"}`,
        );
      } finally {
        setIsLoading(false);
      }
    },
    [addMessage, session, currentQuestion],
  );

  const endInterview = useCallback(async () => {
    if (!session) return;
    setIsLoading(true);
    try {
      await api.updateSession(session.session_id, { status: "completed" });
      addMessage("system", "Interview session completed. Thank you!");
      setSession((prev) =>
        prev ? { ...prev, status: "completed" } : null,
      );
    } catch {
      addMessage("system", "Failed to end session gracefully.");
    } finally {
      setIsLoading(false);
    }
  }, [session, addMessage]);

  return (
    <InterviewContext.Provider
      value={{
        session,
        messages,
        currentQuestion,
        isLoading,
        editorLanguage,
        editorCode,
        startInterview,
        sendMessage,
        setEditorCode,
        setEditorLanguage,
        endInterview,
      }}
    >
      {children}
    </InterviewContext.Provider>
  );
}

// ── Hook ─────────────────────────────────────────────────────────────────────

export function useInterview(): InterviewContextType {
  const ctx = useContext(InterviewContext);
  if (!ctx) {
    throw new Error("useInterview must be used within an InterviewProvider");
  }
  return ctx;
}

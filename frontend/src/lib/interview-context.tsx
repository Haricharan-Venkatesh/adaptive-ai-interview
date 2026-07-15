"use client";

import { createContext, useContext, useCallback, useState, type ReactNode } from "react";
import type { ChatMessage, InterviewSession, InterviewState, Question } from "@/lib/types";
import * as api from "@/lib/api";

// ── Context ──────────────────────────────────────────────────────────────────

interface InterviewContextType extends InterviewState {
  startInterview: (candidateName: string, topic?: string) => Promise<void>;
  sendMessage: (content: string) => void;
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
    async (candidateName: string, topic?: string) => {
      setIsLoading(true);
      try {
        const newSession = await api.createSession({
          candidate_name: candidateName,
          topic: topic ?? "General",
        });
        setSession(newSession);
        setMessages([]);

        addMessage(
          "system",
          `Interview session started. Welcome, ${candidateName}! Topic: ${newSession.topic}.`,
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
    (content: string) => {
      if (!content.trim()) return;

      addMessage("user", content);

      // Simulated assistant response — will be replaced by M2.1 LLM integration
      const topic = session?.topic ?? "General";
      setIsLoading(true);
      setTimeout(async () => {
        try {
          const questions = await api.searchQuestions({ topic });
          if (questions.length > 0) {
            const q =
              questions[Math.floor(Math.random() * questions.length)];
            setCurrentQuestion(q);
            addMessage(
              "assistant",
              `Thank you for your answer. Here's the next question:\n\n${q.question}`,
            );
          } else {
            addMessage(
              "assistant",
              "Thank you for your response. Let me evaluate it and prepare the next question.",
            );
          }
        } catch {
          addMessage(
            "assistant",
            "Thank you for your response. I'm preparing the next question...",
          );
        } finally {
          setIsLoading(false);
        }
      }, 1200);
    },
    [addMessage, session],
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

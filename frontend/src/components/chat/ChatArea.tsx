"use client";

import { useEffect, useRef } from "react";
import { useInterview } from "@/lib/interview-context";
import ChatMessage from "@/components/chat/ChatMessage";
import ChatInput from "@/components/chat/ChatInput";
import LoadingSpinner from "@/components/ui/LoadingSpinner";

export default function ChatArea() {
  const { messages, isLoading, sendMessage, session } = useInterview();
  const scrollRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  return (
    <div className="flex flex-1 flex-col">
      {/* Messages */}
      <div
        ref={scrollRef}
        className="flex-1 overflow-y-auto px-4 py-6 scroll-smooth"
      >
        <div className="mx-auto max-w-3xl space-y-4">
          {messages.length === 0 && (
            <div className="flex flex-col items-center justify-center py-20 text-center">
              <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br from-indigo-500 to-purple-600 shadow-xl shadow-indigo-500/25">
                <svg className="h-8 w-8 text-white" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M8.625 12a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H8.25m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H12m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0h-.375M21 12c0 4.556-4.03 8.25-9 8.25a9.764 9.764 0 01-2.555-.337A5.972 5.972 0 015.41 20.97a5.969 5.969 0 01-.474-.065 4.48 4.48 0 00.978-2.025c.09-.457-.133-.901-.467-1.226C3.93 16.178 3 14.189 3 12c0-4.556 4.03-8.25 9-8.25s9 3.694 9 8.25z" />
                </svg>
              </div>
              <h3 className="mt-5 text-lg font-semibold text-slate-900 dark:text-white">
                Ready to begin
              </h3>
              <p className="mt-2 max-w-sm text-sm text-slate-500 dark:text-slate-400">
                Start an interview session from the sidebar, or the questions
                will appear here once the session begins.
              </p>
            </div>
          )}

          {messages.map((msg) => (
            <ChatMessage key={msg.id} message={msg} />
          ))}

          {/* Typing indicator */}
          {isLoading && (
            <div className="flex items-center gap-3">
              <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 text-white text-xs font-bold">
                AI
              </div>
              <div className="flex items-center gap-2 rounded-2xl rounded-bl-md border border-slate-200 dark:border-white/10 bg-slate-100 dark:bg-white/5 px-4 py-3">
                <LoadingSpinner size="sm" />
                <span className="text-sm text-slate-500 dark:text-slate-400">
                  Thinking…
                </span>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Input */}
      <ChatInput
        onSend={sendMessage}
        disabled={!session || session.status !== "active"}
        placeholder={
          !session
            ? "Start an interview session first…"
            : session.status !== "active"
              ? "Session is not active"
              : "Type your answer…"
        }
      />
    </div>
  );
}

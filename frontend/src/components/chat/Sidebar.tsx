"use client";

import { useInterview } from "@/lib/interview-context";
import LoadingSpinner from "@/components/ui/LoadingSpinner";

export default function Sidebar() {
  const { session, currentQuestion, isLoading, endInterview } = useInterview();

  return (
    <aside className="flex w-72 flex-col border-r border-slate-200 dark:border-white/10 bg-slate-50/50 dark:bg-slate-900/50">
      {/* Header */}
      <div className="border-b border-slate-200 dark:border-white/10 p-4">
        <h2 className="text-sm font-semibold text-slate-900 dark:text-white">
          Interview Session
        </h2>
        {session ? (
          <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
            {session.session_id.slice(0, 8)}…
          </p>
        ) : (
          <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
            No active session
          </p>
        )}
      </div>

      {/* Session Info */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {session && (
          <>
            {/* Status */}
            <div>
              <label className="text-[11px] font-medium uppercase tracking-wider text-slate-400 dark:text-slate-500">
                Status
              </label>
              <div className="mt-1 flex items-center gap-2">
                <span
                  className={`h-2 w-2 rounded-full ${
                    session.status === "active"
                      ? "bg-emerald-400 animate-pulse"
                      : session.status === "completed"
                        ? "bg-blue-400"
                        : "bg-amber-400"
                  }`}
                />
                <span className="text-sm font-medium capitalize text-slate-700 dark:text-slate-300">
                  {session.status}
                </span>
              </div>
            </div>

            {/* Topic */}
            <div>
              <label className="text-[11px] font-medium uppercase tracking-wider text-slate-400 dark:text-slate-500">
                Topic
              </label>
              <p className="mt-1 text-sm text-slate-700 dark:text-slate-300">
                {session.topic}
              </p>
            </div>

            {/* Candidate */}
            <div>
              <label className="text-[11px] font-medium uppercase tracking-wider text-slate-400 dark:text-slate-500">
                Candidate
              </label>
              <p className="mt-1 text-sm text-slate-700 dark:text-slate-300">
                {session.candidate_name}
              </p>
            </div>

            {/* Questions Asked */}
            <div>
              <label className="text-[11px] font-medium uppercase tracking-wider text-slate-400 dark:text-slate-500">
                Questions
              </label>
              <p className="mt-1 text-sm text-slate-700 dark:text-slate-300">
                {session.questions_asked?.length ?? 0} asked
              </p>
            </div>

            {/* Current Question */}
            {currentQuestion && (
              <div className="rounded-xl border border-indigo-200 dark:border-indigo-500/20 bg-indigo-50/50 dark:bg-indigo-500/5 p-3">
                <label className="text-[11px] font-medium uppercase tracking-wider text-indigo-500 dark:text-indigo-400">
                  Current Question
                </label>
                <p className="mt-1 text-xs text-slate-700 dark:text-slate-300 line-clamp-3">
                  {currentQuestion.title}
                </p>
                <div className="mt-2 flex gap-1.5 flex-wrap">
                  {currentQuestion.tags.slice(0, 3).map((tag) => (
                    <span
                      key={tag}
                      className="inline-flex rounded-md px-1.5 py-0.5 text-[10px] font-medium bg-indigo-100 dark:bg-indigo-500/10 text-indigo-600 dark:text-indigo-400"
                    >
                      {tag}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </>
        )}

        {isLoading && (
          <div className="flex items-center gap-2 text-sm text-slate-500 dark:text-slate-400">
            <LoadingSpinner size="sm" />
            <span>Processing…</span>
          </div>
        )}
      </div>

      {/* End Session */}
      {session && session.status === "active" && (
        <div className="border-t border-slate-200 dark:border-white/10 p-4">
          <button
            onClick={endInterview}
            className="w-full rounded-xl border border-red-200 dark:border-red-500/20 bg-red-50 dark:bg-red-500/5 py-2 text-sm font-medium text-red-600 dark:text-red-400 hover:bg-red-100 dark:hover:bg-red-500/10 transition-colors"
          >
            End Interview
          </button>
        </div>
      )}
    </aside>
  );
}

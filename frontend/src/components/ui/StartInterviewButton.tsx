"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useInterview } from "@/lib/interview-context";
import { INTERVIEW_TOPICS, type InterviewTopic } from "@/lib/types";

export default function StartInterviewButton() {
  const router = useRouter();
  const { startInterview } = useInterview();

  const [isStarting, setIsStarting] = useState(false);
  const [showModal, setShowModal] = useState(false);
  const [topic, setTopic] = useState<InterviewTopic>("DSA");

  const handleOpen = () => setShowModal(true);
  const handleClose = () => setShowModal(false);

  const handleStart = async () => {
    setIsStarting(true);
    try {
      // Use "guest" as a candidate_id for unauthenticated users.
      // When auth is wired up, replace with the logged-in user's ID.
      const candidateId =
        typeof window !== "undefined"
          ? (localStorage.getItem("user_id") ?? "guest")
          : "guest";

      await startInterview(candidateId, topic);
      setShowModal(false);
      router.push("/interview");
    } catch (error) {
      console.error("Failed to start interview:", error);
    } finally {
      setIsStarting(false);
    }
  };

  return (
    <>
      {/* Trigger button */}
      <button
        onClick={handleOpen}
        id="cta-start-interview"
        className="inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-indigo-500 to-purple-600 px-7 py-3.5 text-base font-medium text-white shadow-lg shadow-indigo-500/25 hover:shadow-indigo-500/40 hover:from-indigo-600 hover:to-purple-700 transition-all"
      >
        <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" d="M5.25 5.653c0-.856.917-1.398 1.667-.986l11.54 6.348a1.125 1.125 0 010 1.971l-11.54 6.347a1.125 1.125 0 01-1.667-.985V5.653z" />
        </svg>
        Start Interview
      </button>

      {/* Topic picker modal */}
      {showModal && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm"
          onClick={handleClose}
        >
          <div
            className="relative w-full max-w-sm rounded-2xl border border-white/10 bg-slate-900 p-6 shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          >
            <h2 className="text-lg font-semibold text-white">Choose a Topic</h2>
            <p className="mt-1 text-sm text-slate-400">
              Select the domain you want to be interviewed on.
            </p>

            <div className="mt-4 grid grid-cols-1 gap-2">
              {INTERVIEW_TOPICS.map((t) => (
                <button
                  key={t}
                  onClick={() => setTopic(t)}
                  className={`rounded-xl border px-4 py-2.5 text-left text-sm font-medium transition-colors ${
                    topic === t
                      ? "border-indigo-500 bg-indigo-500/15 text-indigo-300"
                      : "border-white/10 bg-white/5 text-slate-300 hover:border-white/20 hover:bg-white/10"
                  }`}
                >
                  {t}
                </button>
              ))}
            </div>

            <div className="mt-5 flex gap-3">
              <button
                onClick={handleClose}
                className="flex-1 rounded-xl border border-white/10 bg-white/5 py-2.5 text-sm font-medium text-slate-300 hover:bg-white/10 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleStart}
                disabled={isStarting}
                className="flex-1 inline-flex items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-indigo-500 to-purple-600 py-2.5 text-sm font-medium text-white hover:from-indigo-600 hover:to-purple-700 transition-all disabled:opacity-75 disabled:cursor-not-allowed"
              >
                {isStarting ? (
                  <>
                    <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                    </svg>
                    Starting…
                  </>
                ) : (
                  "Begin"
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}

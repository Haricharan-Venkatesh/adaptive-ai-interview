"use client";

import dynamic from "next/dynamic";
import { useInterview } from "@/lib/interview-context";

const MonacoEditor = dynamic(() => import("@monaco-editor/react"), {
  ssr: false,
  loading: () => (
    <div className="flex h-full items-center justify-center text-sm text-slate-400 dark:text-slate-500">
      Loading editor…
    </div>
  ),
});

const LANGUAGES = [
  "python",
  "javascript",
  "typescript",
  "java",
  "cpp",
  "c",
  "go",
  "rust",
  "sql",
] as const;

export default function CodeEditor() {
  const { editorCode, editorLanguage, setEditorCode, setEditorLanguage, session } =
    useInterview();

  return (
    <div className="flex flex-col border-t lg:border-t-0 lg:border-l border-slate-200 dark:border-white/10 bg-slate-50 dark:bg-slate-900/50">
      {/* Toolbar */}
      <div className="flex items-center justify-between border-b border-slate-200 dark:border-white/10 px-4 py-2">
        <div className="flex items-center gap-2">
          <svg className="h-4 w-4 text-slate-400" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="M17.25 6.75L22.5 12l-5.25 5.25m-10.5 0L1.5 12l5.25-5.25m7.5-3l-4.5 16.5" />
          </svg>
          <span className="text-xs font-medium text-slate-600 dark:text-slate-400">
            Code Editor
          </span>
        </div>

        <select
          value={editorLanguage}
          onChange={(e) => setEditorLanguage(e.target.value)}
          className="rounded-lg border border-slate-200 dark:border-white/10 bg-white dark:bg-white/5 px-2 py-1 text-xs text-slate-700 dark:text-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-500/50"
        >
          {LANGUAGES.map((lang) => (
            <option key={lang} value={lang}>
              {lang.charAt(0).toUpperCase() + lang.slice(1)}
            </option>
          ))}
        </select>
      </div>

      {/* Editor */}
      <div className="flex-1 min-h-[200px] lg:min-h-0">
        <MonacoEditor
          height="100%"
          language={editorLanguage}
          value={editorCode}
          onChange={(val) => setEditorCode(val ?? "")}
          theme="vs-dark"
          options={{
            minimap: { enabled: false },
            fontSize: 14,
            lineNumbers: "on",
            scrollBeyondLastLine: false,
            wordWrap: "on",
            padding: { top: 12 },
            readOnly: !session || session.status !== "active",
            automaticLayout: true,
          }}
        />
      </div>
    </div>
  );
}

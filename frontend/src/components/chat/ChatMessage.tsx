import type { ChatMessage as ChatMessageType } from "@/lib/types";

interface ChatMessageProps {
  message: ChatMessageType;
}

export default function ChatMessage({ message }: ChatMessageProps) {
  const isUser = message.role === "user";
  const isSystem = message.role === "system";

  if (isSystem) {
    return (
      <div className="flex justify-center py-2">
        <div className="rounded-full bg-slate-100 dark:bg-white/5 px-4 py-1.5 text-xs text-slate-500 dark:text-slate-400 border border-slate-200 dark:border-white/10">
          {message.content}
        </div>
      </div>
    );
  }

  return (
    <div className={`flex gap-3 ${isUser ? "flex-row-reverse" : "flex-row"}`}>
      {/* Avatar */}
      <div
        className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-xl text-xs font-bold ${
          isUser
            ? "bg-gradient-to-br from-emerald-400 to-teal-500 text-white"
            : "bg-gradient-to-br from-indigo-500 to-purple-600 text-white"
        }`}
      >
        {isUser ? "U" : "AI"}
      </div>

      {/* Bubble */}
      <div
        className={`max-w-[75%] rounded-2xl px-4 py-3 text-sm leading-relaxed ${
          isUser
            ? "bg-indigo-500 text-white rounded-br-md"
            : "bg-slate-100 dark:bg-white/5 text-slate-800 dark:text-slate-200 border border-slate-200 dark:border-white/10 rounded-bl-md"
        }`}
      >
        {/* Render content preserving line breaks */}
        {message.content.split("\n").map((line, i) => (
          <span key={i}>
            {line}
            {i < message.content.split("\n").length - 1 && <br />}
          </span>
        ))}

        {/* Code block */}
        {message.codeBlock && (
          <pre className="mt-3 overflow-x-auto rounded-lg bg-slate-900 p-3 text-xs text-slate-100">
            <code>{message.codeBlock.code}</code>
          </pre>
        )}

        {/* Timestamp */}
        <p
          className={`mt-1.5 text-[10px] ${
            isUser ? "text-indigo-200" : "text-slate-400 dark:text-slate-500"
          }`}
        >
          {message.timestamp.toLocaleTimeString([], {
            hour: "2-digit",
            minute: "2-digit",
          })}
        </p>
      </div>
    </div>
  );
}

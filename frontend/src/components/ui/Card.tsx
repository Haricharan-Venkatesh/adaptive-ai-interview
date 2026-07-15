import type { ReactNode } from "react";

interface CardProps {
  children: ReactNode;
  className?: string;
  hover?: boolean;
}

export default function Card({ children, className = "", hover = false }: CardProps) {
  return (
    <div
      className={`
        rounded-2xl border border-slate-200 dark:border-white/10
        bg-white/60 dark:bg-white/5
        backdrop-blur-xl shadow-sm
        ${hover ? "transition-all duration-300 hover:shadow-lg hover:border-indigo-300 dark:hover:border-indigo-500/30 hover:-translate-y-0.5" : ""}
        ${className}
      `}
    >
      {children}
    </div>
  );
}

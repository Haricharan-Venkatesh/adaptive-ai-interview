"use client";

import { ThemeProvider } from "@/lib/theme-context";
import { InterviewProvider } from "@/lib/interview-context";
import type { ReactNode } from "react";

export default function ClientProviders({ children }: { children: ReactNode }) {
  return (
    <ThemeProvider>
      <InterviewProvider>
        {children}
      </InterviewProvider>
    </ThemeProvider>
  );
}

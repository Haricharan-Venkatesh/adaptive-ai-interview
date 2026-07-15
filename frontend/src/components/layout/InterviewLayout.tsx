"use client";

import Sidebar from "@/components/chat/Sidebar";
import ChatArea from "@/components/chat/ChatArea";
import CodeEditor from "@/components/editor/CodeEditor";
import { InterviewProvider } from "@/lib/interview-context";
import type { ReactNode } from "react";

interface InterviewLayoutProps {
  children?: ReactNode;
}

export default function InterviewLayout({ children }: InterviewLayoutProps) {
  return (
    <InterviewProvider>
      <div className="flex h-[calc(100vh-4rem)] overflow-hidden">
        {/* Sidebar — hidden on mobile, visible on lg+ */}
        <div className="hidden lg:flex">
          <Sidebar />
        </div>

        {/* Main area — chat + editor */}
        <div className="flex flex-1 flex-col lg:flex-row">
          {/* Chat takes 60% on large screens */}
          <div className="flex flex-1 lg:w-3/5">
            <ChatArea />
          </div>

          {/* Editor takes 40% on large screens, stacks below on mobile */}
          <div className="h-[300px] lg:h-auto lg:w-2/5">
            <CodeEditor />
          </div>
        </div>
      </div>
      {children}
    </InterviewProvider>
  );
}

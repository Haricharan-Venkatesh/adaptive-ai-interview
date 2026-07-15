import type { Metadata } from "next";
import InterviewLayout from "@/components/layout/InterviewLayout";

export const metadata: Metadata = {
  title: "Interview | Adaptive AI Interview Assistant",
  description: "Interactive AI-powered technical interview with adaptive questioning and live code editor.",
};

export default function InterviewPage() {
  return <InterviewLayout />;
}

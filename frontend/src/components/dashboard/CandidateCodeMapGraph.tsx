'use client';

import dynamic from 'next/dynamic';
import React from 'react';
import { CodeMapNode, CodeMapLink } from '@/lib/dashboardApi';

interface CandidateCodeMapGraphProps {
  nodes: CodeMapNode[];
  links: CodeMapLink[];
  onSelectNode?: (node: CodeMapNode | null) => void;
}

const CandidateCodeMapGraphCanvas = dynamic(
  () => import('./CandidateCodeMapGraphCanvas'),
  {
    ssr: false,
    loading: () => (
      <div className="w-full h-[550px] bg-slate-950 rounded-xl border border-slate-800 flex flex-col items-center justify-center space-y-3 text-slate-400 font-mono text-sm">
        <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
        <span className="animate-pulse">Loading Neo4j Interactive Graph Canvas...</span>
      </div>
    )
  }
);

export default function CandidateCodeMapGraph(props: CandidateCodeMapGraphProps) {
  return <CandidateCodeMapGraphCanvas {...props} />;
}

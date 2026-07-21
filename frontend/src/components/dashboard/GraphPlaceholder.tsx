'use client';

import dynamic from 'next/dynamic';
import React from 'react';

/**
 * Dynamic import wrapper for ForceGraph2D to prevent SSR issues in Next.js
 */
const GraphPlaceholderCanvas = dynamic(
  () => import('./GraphPlaceholderCanvas'),
  {
    ssr: false,
    loading: () => (
      <div className="w-full h-[500px] bg-slate-950 rounded-xl border border-slate-800 flex items-center justify-center text-slate-400 font-mono text-sm">
        <span className="animate-pulse">Loading Graph Visualization Library...</span>
      </div>
    )
  }
);

export default function GraphPlaceholder() {
  return <GraphPlaceholderCanvas />;
}

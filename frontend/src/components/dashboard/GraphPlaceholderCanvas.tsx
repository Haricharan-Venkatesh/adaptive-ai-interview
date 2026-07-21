'use client';

import React from 'react';
import ForceGraph2D from 'react-force-graph-2d';

/**
 * Library Choice Justification:
 * react-force-graph-2d was chosen for Phase 5 graph visualization because:
 * 1. It utilizes HTML5 Canvas rendering for high performance even with complex Neo4j skill graphs.
 * 2. It integrates cleanly with Next.js client-side dynamic imports (ssr: false).
 * 3. It provides extensible custom node painting APIs needed for DKT mastery color-coding.
 * 4. It has zero peer dependency friction with React 19 / Next.js 16.
 */

interface GraphNode {
  id: string;
  name: string;
  group: string;
  val: number;
}

interface GraphLink {
  source: string;
  target: string;
  label?: string;
}

interface GraphData {
  nodes: GraphNode[];
  links: GraphLink[];
}

const dummyGraphData: GraphData = {
  nodes: [
    { id: 'arrays_strings', name: 'Arrays & Strings', group: 'Data Structures', val: 10 },
    { id: 'two_pointers', name: 'Two Pointers', group: 'Algorithms', val: 8 },
    { id: 'binary_search', name: 'Binary Search', group: 'Algorithms', val: 8 },
    { id: 'trees_graphs', name: 'Trees & Graphs', group: 'Data Structures', val: 12 },
    { id: 'dynamic_programming', name: 'Dynamic Programming', group: 'Advanced', val: 15 },
    { id: 'graph_rag', name: 'Graph RAG Retrieval', group: 'AI Modules', val: 14 }
  ],
  links: [
    { source: 'arrays_strings', target: 'two_pointers', label: 'PREREQUISITE_FOR' },
    { source: 'two_pointers', target: 'binary_search', label: 'EXTENDS' },
    { source: 'binary_search', target: 'dynamic_programming', label: 'DEPENDS_ON' },
    { source: 'arrays_strings', target: 'trees_graphs', label: 'FOUNDATION_FOR' },
    { source: 'trees_graphs', target: 'graph_rag', label: 'USED_IN' }
  ]
};

export default function GraphPlaceholderCanvas() {
  return (
    <div className="w-full h-[500px] bg-slate-950 rounded-xl border border-slate-800 shadow-2xl relative overflow-hidden flex flex-col justify-center items-center">
      <div className="absolute top-4 left-4 z-10 bg-slate-900/80 backdrop-blur-md px-3 py-1.5 rounded-lg border border-slate-700/50 text-xs text-slate-300 font-mono">
        <span className="inline-block w-2 h-2 rounded-full bg-emerald-500 mr-2 animate-pulse"></span>
        Interactive Candidate Code Map (Placeholder Graph — react-force-graph-2d)
      </div>

      <ForceGraph2D
        graphData={dummyGraphData}
        nodeLabel={(node) => `${(node as GraphNode).name} (${(node as GraphNode).group})`}
        nodeAutoColorBy="group"
        linkDirectionalParticles={2}
        linkDirectionalParticleSpeed={0.005}
        nodeRelSize={6}
        width={800}
        height={480}
        backgroundColor="#090d16"
      />
    </div>
  );
}

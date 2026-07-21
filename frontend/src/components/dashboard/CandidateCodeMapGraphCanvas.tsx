'use client';

import React, { useRef, useState, useCallback } from 'react';
import ForceGraph2D, { ForceGraphMethods } from 'react-force-graph-2d';
import { CodeMapNode, CodeMapLink } from '@/lib/dashboardApi';

interface CandidateCodeMapGraphCanvasProps {
  nodes: CodeMapNode[];
  links: CodeMapLink[];
  onSelectNode?: (node: CodeMapNode | null) => void;
}

export default function CandidateCodeMapGraphCanvas({
  nodes,
  links,
  onSelectNode
}: CandidateCodeMapGraphCanvasProps) {
  const fgRef = useRef<ForceGraphMethods | undefined>(undefined);
  const [selectedNode, setSelectedNode] = useState<CodeMapNode | null>(null);
  const [hoveredNode, setHoveredNode] = useState<CodeMapNode | null>(null);

  // Group color mapping for clear visual distinction
  const GROUP_COLORS: Record<string, string> = {
    'Data Structures': '#3b82f6', // blue
    'Algorithms': '#10b981',      // emerald
    'Advanced': '#8b5cf6',        // purple
    'AI Systems': '#ec4899',       // pink
    'System Design': '#f59e0b',   // amber
    'Concept': '#64748b'          // slate
  };

  const handleNodeClick = useCallback((node: any) => {
    const codeMapNode = node as CodeMapNode;
    setSelectedNode(codeMapNode);
    if (onSelectNode) {
      onSelectNode(codeMapNode);
    }
    // Zoom in on clicked node
    if (fgRef.current && node.x !== undefined && node.y !== undefined) {
      fgRef.current.centerAt(node.x, node.y, 400);
      fgRef.current.zoom(2.5, 400);
    }
  }, [onSelectNode]);

  const handleBackgroundClick = useCallback(() => {
    setSelectedNode(null);
    if (onSelectNode) {
      onSelectNode(null);
    }
  }, [onSelectNode]);

  const handleZoomFit = useCallback(() => {
    if (fgRef.current) {
      fgRef.current.zoomToFit(400, 40);
    }
  }, []);

  const handleZoomIn = useCallback(() => {
    if (fgRef.current) {
      fgRef.current.zoom(fgRef.current.zoom() * 1.3, 300);
    }
  }, []);

  const handleZoomOut = useCallback(() => {
    if (fgRef.current) {
      fgRef.current.zoom(fgRef.current.zoom() / 1.3, 300);
    }
  }, []);

  const graphData = {
    nodes: nodes.map(n => ({ ...n })),
    links: links.map(l => ({ ...l }))
  };

  return (
    <div className="w-full h-[550px] bg-slate-950 rounded-xl border border-slate-800 shadow-2xl relative overflow-hidden flex flex-col">
      {/* Graph Toolbar Overlay */}
      <div className="absolute top-4 left-4 z-10 flex items-center gap-2 bg-slate-900/90 backdrop-blur-md px-3 py-1.5 rounded-lg border border-slate-700/60 text-xs text-slate-300 font-mono shadow-md">
        <span className="inline-block w-2 h-2 rounded-full bg-indigo-500 animate-pulse"></span>
        Interactive Candidate Graph ({nodes.length} Nodes, {links.length} Edges)
      </div>

      {/* Control Buttons */}
      <div className="absolute top-4 right-4 z-10 flex items-center gap-1.5 bg-slate-900/90 backdrop-blur-md p-1.5 rounded-lg border border-slate-700/60 shadow-md">
        <button
          onClick={handleZoomIn}
          className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-bold transition-colors"
          title="Zoom In"
        >
          +
        </button>
        <button
          onClick={handleZoomOut}
          className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-bold transition-colors"
          title="Zoom Out"
        >
          -
        </button>
        <button
          onClick={handleZoomFit}
          className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium transition-colors"
          title="Fit Graph to Screen"
        >
          Fit Screen
        </button>
      </div>

      {/* Selected Node Quick Banner */}
      {selectedNode && (
        <div className="absolute bottom-4 left-4 z-10 bg-slate-900/95 backdrop-blur-md border border-indigo-500/40 px-4 py-2.5 rounded-lg text-xs max-w-sm shadow-xl flex items-center justify-between gap-3">
          <div>
            <div className="font-semibold text-slate-100">{selectedNode.name}</div>
            <div className="text-slate-400 font-mono text-[11px]">{selectedNode.group} • Size: {selectedNode.val}</div>
          </div>
          <button
            onClick={handleBackgroundClick}
            className="text-slate-400 hover:text-slate-200 text-xs font-mono px-1.5 py-0.5 rounded bg-slate-800"
          >
            Clear
          </button>
        </div>
      )}

      {/* ForceGraph2D Interactive Canvas */}
      <div className="flex-1 w-full h-full">
        <ForceGraph2D
          ref={fgRef as any}
          graphData={graphData}
          nodeLabel={(node) => `${(node as CodeMapNode).name} [${(node as CodeMapNode).group}]`}
          nodeColor={(node) => {
            const codeNode = node as CodeMapNode;
            if (selectedNode && codeNode.id === selectedNode.id) return '#f43f5e'; // Highlight selected in rose
            if (hoveredNode && codeNode.id === hoveredNode.id) return '#38bdf8'; // Highlight hover in sky blue
            return GROUP_COLORS[codeNode.group] || '#64748b';
          }}
          nodeRelSize={7}
          linkDirectionalParticles={2}
          linkDirectionalParticleSpeed={0.006}
          linkDirectionalParticleWidth={2}
          linkColor={() => '#334155'}
          linkLabel={(link) => `${(link as CodeMapLink).label || 'DEPENDS_ON'}`}
          onNodeClick={handleNodeClick}
          onNodeHover={(node) => setHoveredNode(node as CodeMapNode | null)}
          onBackgroundClick={handleBackgroundClick}
          backgroundColor="#090d16"
        />
      </div>
    </div>
  );
}

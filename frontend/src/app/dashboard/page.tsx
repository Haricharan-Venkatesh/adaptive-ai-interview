'use client';

import React, { useEffect, useState } from 'react';
import CandidateCodeMapGraph from '@/components/dashboard/CandidateCodeMapGraph';
import { fetchCodeMapGraph, CodeMapNode, CodeMapGraphResponse } from '@/lib/dashboardApi';

export default function DashboardPage() {
  const [graphResponse, setGraphResponse] = useState<CodeMapGraphResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [selectedNode, setSelectedNode] = useState<CodeMapNode | null>(null);

  useEffect(() => {
    async function loadGraphData() {
      setLoading(true);
      const data = await fetchCodeMapGraph();
      setGraphResponse(data);
      setLoading(false);
    }
    loadGraphData();
  }, []);

  const nodes = graphResponse?.nodes || [];
  const links = graphResponse?.links || [];

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6 md:p-10">
      <div className="max-w-7xl mx-auto space-y-8">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-6">
          <div>
            <h1 className="text-3xl font-bold tracking-tight bg-gradient-to-r from-white via-slate-200 to-indigo-400 bg-clip-text text-transparent">
              Interactive Growth Dashboard
            </h1>
            <p className="text-slate-400 text-sm mt-1">
              Phase 5 Output Dashboard — Neo4j Candidate Code Map Graph & Deep Knowledge Tracing Integration.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={async () => {
                setLoading(true);
                const data = await fetchCodeMapGraph();
                setGraphResponse(data);
                setLoading(false);
              }}
              className="px-3.5 py-1.5 rounded-lg text-xs font-medium bg-slate-900 border border-slate-700 hover:bg-slate-800 text-slate-200 transition-colors flex items-center gap-2"
            >
              <svg className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              Refresh Graph
            </button>
            <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium border ${
              graphResponse?.status === 'success'
                ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                : 'bg-amber-500/10 text-amber-400 border-amber-500/20'
            }`}>
              <span className={`w-1.5 h-1.5 rounded-full mr-2 ${graphResponse?.status === 'success' ? 'bg-emerald-400' : 'bg-amber-400'}`}></span>
              Status: {graphResponse?.status || 'Loading'}
            </span>
          </div>
        </div>

        {/* Live Metrics Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4">
            <div className="text-slate-400 text-xs font-mono">TOTAL CONCEPT NODES</div>
            <div className="text-2xl font-bold text-slate-100 mt-1">{graphResponse?.count_nodes || nodes.length}</div>
          </div>
          <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4">
            <div className="text-slate-400 text-xs font-mono">RELATIONSHIP EDGES</div>
            <div className="text-2xl font-bold text-indigo-400 mt-1">{graphResponse?.count_links || links.length}</div>
          </div>
          <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4">
            <div className="text-slate-400 text-xs font-mono">DATA INTEGRATION LAYER</div>
            <div className="text-sm font-semibold text-slate-200 mt-2 truncate">
              {graphResponse?.message || 'Neo4j Database Layer'}
            </div>
          </div>
        </div>

        {/* Main Dashboard Layout Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Main Graph Panel */}
          <div className="lg:col-span-2 space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-slate-200">Candidate Code Map Graph</h2>
              <span className="text-xs text-slate-400 font-mono">Click a node to inspect concept details</span>
            </div>

            <div className="relative w-full h-[550px]">
              <CandidateCodeMapGraph
                nodes={nodes}
                links={links}
                onSelectNode={(node) => setSelectedNode(node)}
              />

              {loading && (
                <div className="absolute inset-0 z-20 flex items-center justify-center bg-slate-950/70 backdrop-blur-sm rounded-xl border border-slate-800">
                  <div className="flex flex-col items-center gap-4">
                    <div className="w-10 h-10 border-4 border-indigo-500/30 border-t-indigo-500 rounded-full animate-spin"></div>
                    <div className="text-indigo-400 font-medium text-sm animate-pulse tracking-wide">Loading Candidate Code Map...</div>
                  </div>
                </div>
              )}

              {!loading && graphResponse?.status === 'empty' && (
                <div className="absolute inset-0 z-20 flex items-center justify-center bg-slate-950/90 backdrop-blur-sm rounded-xl border border-slate-800">
                  <div className="text-center space-y-4 max-w-md p-8 bg-slate-900 border border-slate-800 rounded-2xl shadow-xl">
                    <div className="w-14 h-14 mx-auto bg-slate-800 rounded-full flex items-center justify-center">
                      <svg className="w-7 h-7 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
                      </svg>
                    </div>
                    <div>
                      <h3 className="text-slate-200 font-bold text-lg">No Graph Data Found</h3>
                      <p className="text-slate-400 text-sm mt-2 leading-relaxed">The candidate code map is currently empty. The candidate might not have completed any tracked assessments or the language is not supported.</p>
                    </div>
                  </div>
                </div>
              )}

              {!loading && graphResponse?.status === 'error' && (
                <div className="absolute inset-0 z-20 flex items-center justify-center bg-slate-950/90 backdrop-blur-sm rounded-xl border border-slate-800">
                  <div className="text-center space-y-4 max-w-md p-8 bg-red-950/20 border border-red-900/50 rounded-2xl shadow-xl">
                    <div className="w-14 h-14 mx-auto bg-red-900/30 rounded-full flex items-center justify-center">
                      <svg className="w-7 h-7 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                      </svg>
                    </div>
                    <div>
                      <h3 className="text-red-300 font-bold text-lg">Failed to Load Graph</h3>
                      <p className="text-red-400/80 text-sm mt-2 leading-relaxed">{graphResponse?.message || 'A network error occurred while connecting to the Neo4j service.'}</p>
                    </div>
                    <button 
                      onClick={async () => {
                        setLoading(true);
                        const data = await fetchCodeMapGraph();
                        setGraphResponse(data);
                        setLoading(false);
                      }}
                      className="mt-6 px-5 py-2.5 bg-slate-900 hover:bg-slate-800 text-slate-200 text-sm font-medium rounded-lg border border-slate-700 transition-colors shadow-sm"
                    >
                      Try Again
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Node Inspector & Control Panel */}
          <div className="space-y-6">
            {/* Selected Node Detailed Inspector */}
            {selectedNode ? (
              <div className="bg-slate-900 border border-indigo-500/40 rounded-xl p-6 space-y-4 shadow-xl">
                <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                  <h3 className="text-md font-semibold text-white">Concept Inspector</h3>
                  <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                    ID: {selectedNode.id}
                  </span>
                </div>

                <div className="space-y-3">
                  <div>
                    <span className="text-xs text-slate-400 font-mono">CONCEPT NAME</span>
                    <p className="text-sm font-bold text-slate-100">{selectedNode.name}</p>
                  </div>
                  <div>
                    <span className="text-xs text-slate-400 font-mono">CATEGORY / GROUP</span>
                    <p className="text-xs font-semibold text-indigo-400 mt-0.5">{selectedNode.group}</p>
                  </div>
                  {selectedNode.description && (
                    <div>
                      <span className="text-xs text-slate-400 font-mono">DESCRIPTION</span>
                      <p className="text-xs text-slate-300 mt-0.5 leading-relaxed">{selectedNode.description}</p>
                    </div>
                  )}
                  <div>
                    <span className="text-xs text-slate-400 font-mono">GRAPH WEIGHT SCORE</span>
                    <p className="text-xs text-slate-200 mt-0.5 font-mono">{selectedNode.val}</p>
                  </div>
                </div>

                <button
                  onClick={() => setSelectedNode(null)}
                  className="w-full py-1.5 rounded-lg text-xs font-medium bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors"
                >
                  Close Inspector
                </button>
              </div>
            ) : (
              <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-3 text-center">
                <div className="w-10 h-10 rounded-full bg-slate-800 text-slate-400 flex items-center justify-center mx-auto text-sm font-mono">
                  ?
                </div>
                <h3 className="text-sm font-semibold text-slate-300">No Concept Selected</h3>
                <p className="text-xs text-slate-400 leading-relaxed">
                  Click any node inside the graph to inspect concept metadata, connected prerequisites, and mastery scores.
                </p>
              </div>
            )}

            {/* Interactive Instructions & Legend */}
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-4">
              <h3 className="text-sm font-semibold text-slate-200">Category Legend</h3>
              <div className="space-y-2 text-xs">
                <div className="flex items-center gap-2.5">
                  <span className="w-3 h-3 rounded-full bg-blue-500"></span>
                  <span className="text-slate-300">Data Structures</span>
                </div>
                <div className="flex items-center gap-2.5">
                  <span className="w-3 h-3 rounded-full bg-emerald-500"></span>
                  <span className="text-slate-300">Algorithms</span>
                </div>
                <div className="flex items-center gap-2.5">
                  <span className="w-3 h-3 rounded-full bg-purple-500"></span>
                  <span className="text-slate-300">Advanced Concepts</span>
                </div>
                <div className="flex items-center gap-2.5">
                  <span className="w-3 h-3 rounded-full bg-pink-500"></span>
                  <span className="text-slate-300">AI / Graph Systems</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

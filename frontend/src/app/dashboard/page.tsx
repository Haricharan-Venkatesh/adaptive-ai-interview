import type { Metadata } from 'next';
import GraphPlaceholder from '@/components/dashboard/GraphPlaceholder';

export const metadata: Metadata = {
  title: 'Interactive Growth Dashboard | Adaptive AI Interview',
  description: 'Visualize candidate code maps, skill relationships, and DKT mastery scores in an interactive graph.',
};

export default function DashboardPage() {
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
              Phase 5 Output Dashboard — Visualizing Neo4j Code Map & Deep Knowledge Tracing (DKT) Mastery Scores.
            </p>
          </div>
          <div className="flex items-center gap-3">
            <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
              Milestone 1 — Placeholder Graph Active
            </span>
          </div>
        </div>

        {/* Dashboard Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Main Graph Visualization Panel */}
          <div className="lg:col-span-2 space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-slate-200">Candidate Code Map Graph</h2>
              <span className="text-xs text-slate-400 font-mono">Visualization Engine: react-force-graph-2d</span>
            </div>
            <GraphPlaceholder />
          </div>

          {/* Side Control / Info Panel */}
          <div className="space-y-6">
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-4">
              <h3 className="text-md font-semibold text-slate-200">Dashboard Status</h3>
              <div className="space-y-2 text-xs text-slate-400 font-mono">
                <div className="flex justify-between py-1 border-b border-slate-800">
                  <span>Graph Library</span>
                  <span className="text-emerald-400 font-bold">react-force-graph-2d</span>
                </div>
                <div className="flex justify-between py-1 border-b border-slate-800">
                  <span>Rendering Mode</span>
                  <span className="text-slate-200">HTML5 Canvas (Client-only)</span>
                </div>
                <div className="flex justify-between py-1 border-b border-slate-800">
                  <span>Milestone</span>
                  <span className="text-indigo-400 font-bold">M1 (Environment & Setup)</span>
                </div>
              </div>
            </div>

            <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-3">
              <h3 className="text-md font-semibold text-slate-200">Library Selection Justification</h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                <strong className="text-slate-300">react-force-graph-2d</strong> was chosen over vis.js for Phase 5 because:
              </p>
              <ul className="list-disc list-inside text-xs text-slate-400 space-y-1">
                <li>High performance HTML5 Canvas rendering for node networks</li>
                <li>Native dynamic loading compatibility in Next.js SSR</li>
                <li>Custom node rendering hooks for DKT color-coding in Milestone 4</li>
                <li>Clean npm installation without React 19 peer-dependency conflicts</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

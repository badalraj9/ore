import React, { useState } from 'react';
import { api } from './api';
import { Search, Activity, Share2,  Grid } from 'lucide-react';

function App() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<any[]>([]);
  const [graphData, setGraphData] = useState<any>(null);
  const [gapsData, setGapsData] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const handleSearch = async () => {
    setLoading(true);
    try {
      // 1. Analyze
      await api.analyzeQuery(query);
      // 2. Ingest (Trigger background)
      await api.startIngestion(query);

      // Wait a bit for demo purposes or just search existing
      setTimeout(async () => {
          const res = await api.search(query);
          setResults(res.data);
      }, 2000);

    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const loadAnalysis = async () => {
      const g = await api.getGraph();
      setGraphData(g.data);

      const gap = await api.getGaps();
      setGapsData(gap.data);
  };

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <header className="mb-8">
        <h1 className="text-3xl font-bold text-blue-900">ORE: Open Research Engine</h1>
        <p className="text-gray-600">Algorithmic Scientific Reasoning</p>
      </header>

      <div className="max-w-4xl mx-auto space-y-6">
        {/* Search Bar */}
        <div className="flex gap-2">
          <input
            className="flex-1 p-3 border rounded shadow-sm"
            placeholder="Enter research topic..."
            value={query}
            onChange={e => setQuery(e.target.value)}
          />
          <button
            onClick={handleSearch}
            className="bg-blue-600 text-white px-6 py-3 rounded hover:bg-blue-700 flex items-center gap-2"
          >
            <Search size={20} /> Research
          </button>
        </div>

        {/* Results */}
        {results.length > 0 && (
          <div className="bg-white p-6 rounded shadow">
            <h2 className="text-xl font-semibold mb-4">Retrieval Results</h2>
            <ul className="space-y-4">
              {results.map((r: any) => (
                <li key={r.chunk_id} className="border-b pb-2">
                  <p className="text-sm text-gray-800">{r.text}</p>
                  <span className="text-xs text-blue-500 font-medium">Score: {r.score.toFixed(4)}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Analysis Dashboard */}
        <div className="grid grid-cols-2 gap-4">
            <button onClick={loadAnalysis} className="bg-indigo-600 text-white p-4 rounded shadow flex items-center justify-center gap-2">
                <Activity /> Load Deep Analysis
            </button>
        </div>

        {/* Graph & Gaps */}
        {graphData && (
            <div className="bg-white p-6 rounded shadow">
                <h2 className="text-xl font-semibold flex items-center gap-2 mb-4"><Share2 /> Citation Graph</h2>
                <div className="h-64 bg-gray-100 flex items-center justify-center">
                    {graphData.total_papers} Papers, {graphData.total_citations} Citations
                    {/* Graph Vis Placeholder */}
                </div>
            </div>
        )}

        {gapsData && (
            <div className="bg-white p-6 rounded shadow">
                <h2 className="text-xl font-semibold flex items-center gap-2 mb-4"><Grid /> Research Gaps</h2>
                <div className="grid grid-cols-1 gap-2">
                    {gapsData.gaps.map((gap: any, i: number) => (
                        <div key={i} className="p-2 bg-red-50 border border-red-100 rounded">
                            <span className="font-bold text-red-700">Gap:</span> {gap.method} + {gap.dataset}
                        </div>
                    ))}
                </div>
            </div>
        )}

      </div>
    </div>
  );
}

export default App;

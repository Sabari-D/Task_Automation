'use client';

import { useState } from 'react';
import TaskTracker from '@/components/TaskTracker';

export default function Home() {
  const [prompt, setPrompt] = useState('');
  const [taskId, setTaskId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!prompt.trim()) return;

    setIsLoading(true);
    setError(null);
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';
      const res = await fetch(`${apiUrl}/api/task`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_prompt: prompt }),
      });
      if (!res.ok) throw new Error('Failed to start task');
      const data = await res.json();
      setTaskId(data.task_id);
    } catch (err: any) {
      setError(err.message || 'An error occurred.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <main className="container mx-auto px-4 py-16 flex flex-col items-center">
      
      {/* Hero Section */}
      <div className="text-center max-w-4xl w-full mb-12 animate-fade-in">
        <div className="inline-block px-4 py-1.5 rounded-full border border-primary/30 bg-primary/10 text-primary-glow font-medium text-sm mb-6">
          v1.0.0 Multi-Agent System
        </div>
        <h1 className="text-5xl md:text-7xl font-extrabold tracking-tight mb-6 bg-clip-text text-transparent bg-gradient-to-r from-white via-primary to-secondary">
          Auto-Worker Engine
        </h1>
        <p className="text-lg md:text-xl text-slate-300 max-w-2xl mx-auto">
          Deploy a team of specialized AI agents to plan, research, optimize, and execute complex workflows autonomously.
        </p>
      </div>

      {!taskId ? (
        <div className="w-full max-w-3xl glass-card animate-fade-in relative group">
          <div className="absolute -inset-1 bg-gradient-to-r from-primary to-secondary rounded-2xl blur opacity-25 group-hover:opacity-40 transition duration-1000 group-hover:duration-200"></div>
          <form onSubmit={handleSubmit} className="relative glass rounded-xl p-2 flex flex-col sm:flex-row gap-2">
            <input
              type="text"
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="e.g., Plan a 3-day trip to Goa under ₹10k"
              className="flex-1 bg-transparent border-none focus:ring-0 text-white placeholder-slate-400 px-4 py-3 text-lg outline-none"
              disabled={isLoading}
            />
            <button
              type="submit"
              disabled={isLoading || !prompt.trim()}
              className="bg-primary hover:bg-primary/80 text-white font-medium py-3 px-8 rounded-lg transition-colors duration-200 disabled:opacity-50 disabled:cursor-not-allowed whitespace-nowrap"
            >
              {isLoading ? (
                <span className="flex items-center gap-2">
                  <div className="w-4 h-4 rounded-full border-2 border-white/20 border-t-white animate-spin"></div>
                  Initializing...
                </span>
              ) : 'Deploy Agents'}
            </button>
          </form>
          {error && <p className="text-red-400 mt-4 text-center">{error}</p>}
        </div>
      ) : (
        <div className="w-full max-w-5xl animate-fade-in">
          <TaskTracker taskId={taskId} onReset={() => setTaskId(null)} />
        </div>
      )}

    </main>
  );
}

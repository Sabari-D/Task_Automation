'use client';

import { useState, useEffect } from 'react';
import TaskTracker from '@/components/TaskTracker';

interface TaskHistory {
  id: string;
  prompt: string;
  timestamp: number;
}

export default function Home() {
  const [prompt, setPrompt] = useState('');
  const [taskId, setTaskId] = useState<string | null>(null);
  const [draftSteps, setDraftSteps] = useState<string[] | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [theme, setTheme] = useState<'dark' | 'light'>('dark');
  const [history, setHistory] = useState<TaskHistory[]>([]);
  const [isHistoryOpen, setIsHistoryOpen] = useState(false);

  useEffect(() => {
    // Load theme from localStorage
    const savedTheme = localStorage.getItem('theme') as 'dark' | 'light' | null;
    if (savedTheme === 'light') {
      setTheme('light');
      document.documentElement.setAttribute('data-theme', 'light');
    }

    // Load history from localStorage
    const savedHistory = localStorage.getItem('taskHistory');
    if (savedHistory) {
      try {
        setHistory(JSON.parse(savedHistory));
      } catch (e) {
        console.error("Failed to parse history");
      }
    }
  }, []);

  const toggleTheme = () => {
    const newTheme = theme === 'dark' ? 'light' : 'dark';
    setTheme(newTheme);
    if (newTheme === 'light') {
      document.documentElement.setAttribute('data-theme', 'light');
    } else {
      document.documentElement.removeAttribute('data-theme');
    }
    localStorage.setItem('theme', newTheme);
  };

  const saveToHistory = (id: string, userPrompt: string) => {
    const newItem: TaskHistory = { id, prompt: userPrompt, timestamp: Date.now() };
    const updated = [newItem, ...history];
    setHistory(updated);
    localStorage.setItem('taskHistory', JSON.stringify(updated));
  };

  const loadPastTask = (id: string) => {
    setTaskId(id);
    setIsHistoryOpen(false);
  };

  const clearHistory = () => {
    setHistory([]);
    localStorage.removeItem('taskHistory');
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!prompt.trim()) return;

    setIsLoading(true);
    setError(null);
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';
      const contextHistory = history.slice(0, 3).map(h => h.prompt);
      const res = await fetch(`${apiUrl}/api/plan`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_prompt: prompt, context: contextHistory }),
      });
      if (!res.ok) throw new Error('Failed to generate draft plan');
      const data = await res.json();
      setDraftSteps(data.steps);
    } catch (err: any) {
      setError(err.message || 'An error occurred.');
    } finally {
      setIsLoading(false);
    }
  };

  const executePlan = async (finalSteps: string[]) => {
    setIsLoading(true);
    setError(null);
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';
      const contextHistory = history.slice(0, 3).map(h => h.prompt);
      const res = await fetch(`${apiUrl}/api/task`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_prompt: prompt, custom_plan: finalSteps, context: contextHistory }),
      });
      if (!res.ok) throw new Error('Failed to start task');
      const data = await res.json();
      setDraftSteps(null);
      setTaskId(data.task_id);
      saveToHistory(data.task_id, prompt);
    } catch (err: any) {
      setError(err.message || 'An error occurred.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen relative flex flex-col transition-colors duration-300">
      {/* Navbar with Features */}
      <nav className="w-full p-4 flex items-center justify-between z-10 glass-card !rounded-none !border-t-0 !border-l-0 !border-r-0 bg-surface/50">
        <div className="flex items-center gap-2 font-bold text-lg text-primary tracking-tight">
          ⚡ Auto-Worker
        </div>
        <div className="flex items-center gap-4">
          <button
            onClick={toggleTheme}
            className="p-2 rounded-full glass hover:bg-primary/20 transition-colors text-xl leading-none"
            title="Toggle Theme"
          >
            {theme === 'dark' ? '☀️' : '🌙'}
          </button>
          <button
            onClick={() => setIsHistoryOpen(true)}
            className="px-4 py-1.5 rounded-lg border border-primary/30 bg-primary/10 hover:bg-primary/20 text-primary font-medium text-sm transition-colors"
          >
            History
          </button>
        </div>
      </nav>

      {/* History Sidebar */}
      {isHistoryOpen && (
        <div className="fixed inset-0 z-50 flex justify-end">
          <div className="absolute inset-0 bg-black/40 backdrop-blur-sm" onClick={() => setIsHistoryOpen(false)}></div>
          <div className="relative w-80 max-w-[80vw] h-full bg-background border-l border-surface-border flex flex-col animate-fade-in shadow-2xl">
            <div className="p-5 border-b border-surface-border flex items-center justify-between">
              <h2 className="text-lg font-bold text-foreground">Task History</h2>
              <button
                onClick={() => setIsHistoryOpen(false)}
                className="text-slate-400 hover:text-foreground text-2xl leading-none"
              >
                ×
              </button>
            </div>
            <div className="flex-1 overflow-y-auto p-4 custom-scrollbar flex flex-col gap-3">
              {history.length === 0 ? (
                <p className="text-slate-500 text-sm text-center mt-10">No history found.</p>
              ) : (
                history.map((h) => (
                  <button
                    key={h.id}
                    onClick={() => loadPastTask(h.id)}
                    className="p-3 text-left rounded-lg bg-surface border border-surface-border hover:border-primary/50 transition-all group"
                  >
                    <p className="text-sm font-medium text-foreground line-clamp-2">{h.prompt}</p>
                    <p className="text-[10px] text-slate-500 mt-2">{new Date(h.timestamp).toLocaleString()}</p>
                  </button>
                ))
              )}
            </div>
            {history.length > 0 && (
              <div className="p-4 border-t border-surface-border">
                <button
                  onClick={clearHistory}
                  className="w-full py-2 rounded-lg text-red-400 text-sm hover:bg-red-500/10 transition-colors"
                >
                  Clear History
                </button>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Main Content Area */}
      <main className="container mx-auto px-4 py-12 flex flex-col items-center flex-1">

        {/* Hero Section */}
        <div className="text-center max-w-4xl w-full mb-12 animate-fade-in">
          <div className="inline-block px-4 py-1.5 rounded-full border border-primary/30 bg-primary/10 text-primary-glow font-medium text-sm mb-6">
            v1.1.0 Feature Update
          </div>
          <h1 className="text-5xl md:text-7xl font-extrabold tracking-tight mb-6 bg-clip-text text-transparent bg-gradient-to-r from-foreground via-primary to-secondary">
            Auto-Worker Engine
          </h1>
          <p className="text-lg md:text-xl text-slate-400 max-w-2xl mx-auto">
            Deploy a team of specialized AI agents to plan, research, optimize, and execute complex workflows autonomously.
          </p>
        </div>

        {!taskId && !draftSteps ? (
          <div className="w-full max-w-3xl glass-card animate-fade-in relative group">
            <div className="absolute -inset-1 bg-gradient-to-r from-primary to-secondary rounded-2xl blur opacity-25 group-hover:opacity-40 transition duration-1000 group-hover:duration-200"></div>
            <form onSubmit={handleSubmit} className="relative glass rounded-xl p-2 flex flex-col sm:flex-row gap-2">
              <input
                type="text"
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                placeholder="Ask anything..."
                className="flex-1 bg-transparent border-none focus:ring-0 text-foreground placeholder-slate-400 px-4 py-3 text-lg outline-none"
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
                    Drafting...
                  </span>
                ) : 'Draft Plan'}
              </button>
            </form>
            {error && <p className="text-red-400 mt-4 text-center">{error}</p>}
          </div>
        ) : draftSteps && !taskId ? (
          <div className="w-full max-w-4xl glass-card animate-fade-in flex flex-col items-center">
            <h2 className="text-2xl font-bold mb-2 text-foreground">✍️ Review & Edit Plan</h2>
            <p className="text-slate-400 text-sm mb-6 max-w-xl text-center">Modify the AI's generated action steps before final multi-agent execution. You have full control.</p>
            
            <div className="w-full flex flex-col gap-3 mb-6">
              {draftSteps.map((step, i) => (
                <div key={i} className="flex gap-3 items-center w-full animate-fade-in">
                  <span className="text-primary font-bold w-6 text-center">{i + 1}.</span>
                  <input
                    type="text"
                    value={step}
                    onChange={(e) => {
                      const newSteps = [...draftSteps];
                      newSteps[i] = e.target.value;
                      setDraftSteps(newSteps);
                    }}
                    className="flex-1 bg-surface border border-surface-border text-foreground px-4 py-3 rounded-xl focus:border-primary/50 outline-none transition-colors"
                  />
                  <button
                    onClick={() => setDraftSteps(draftSteps.filter((_, idx) => idx !== i))}
                    className="p-3 bg-red-500/10 hover:bg-red-500/20 text-red-400 rounded-xl transition-colors"
                    title="Remove Step"
                  >
                    ×
                  </button>
                </div>
              ))}
            </div>
            
            <div className="flex gap-4 w-full">
              <button
                onClick={() => setDraftSteps([...draftSteps, "New Task Step"])}
                className="flex-1 py-3 border border-dashed border-primary/40 rounded-xl text-primary hover:bg-primary/10 transition-colors font-medium"
              >
                + Add Step
              </button>
              <button
                onClick={() => executePlan(draftSteps)}
                disabled={isLoading}
                className="flex-[2] py-3 bg-primary hover:bg-primary/90 text-white rounded-xl shadow-[0_0_20px_rgba(139,92,246,0.3)] transition-all font-bold"
              >
                 {isLoading ? 'Executing...' : '🚀 Run Execution'}
              </button>
            </div>
            {error && <p className="text-red-400 mt-4">{error}</p>}
          </div>
        ) : (
          <div className="w-full max-w-5xl animate-fade-in">
            <TaskTracker taskId={taskId!} onReset={() => { setTaskId(null); setDraftSteps(null); setPrompt(''); }} />
          </div>
        )}

      </main>
    </div>
  );
}

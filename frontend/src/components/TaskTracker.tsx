'use client';

import { useEffect, useState } from 'react';
import ReactMarkdown from 'react-markdown';

interface TaskTrackerProps {
  taskId: string;
  onReset: () => void;
}

interface TaskState {
  status: 'pending' | 'running' | 'completed' | 'failed';
  result?: string;
}

export default function TaskTracker({ taskId, onReset }: TaskTrackerProps) {
  const [taskState, setTaskState] = useState<TaskState>({ status: 'pending' });
  const [logs, setLogs] = useState<string[]>([]);

  useEffect(() => {
    // Create WebSocket connection.
    const wsUrl = process.env.NEXT_PUBLIC_WS_URL || 'ws://127.0.0.1:8000';
    const ws = new WebSocket(`${wsUrl}/ws/task/${taskId}`);

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        setTaskState({ status: data.status, result: data.result });
      } catch (e) {
        console.error("Error parsing websocket message", e);
      }
    };

    ws.onopen = () => {
      setLogs((prev) => [...prev, '[SYSTEM] WebSocket connected. Monitoring agents...']);
    };

    ws.onclose = () => {
      setLogs((prev) => [...prev, '[SYSTEM] WebSocket disconnected.']);
    };

    return () => {
      ws.close();
    };
  }, [taskId]);

  // Simulate streaming logs for aesthetics based on status
  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (taskState.status === 'running') {
      const simulatedLogs = [
        '[PLANNER_AGENT] Analyzing user prompt and breaking down steps...',
        '[PLANNER_AGENT] Identified 4 core objectives. Delegating to research...',
        '[RESEARCH_AGENT] Searching the web for the latest context...',
        '[RESEARCH_AGENT] Found 14 relevant sources. Extracting tabular data...',
        '[OPTIMIZER_AGENT] Reviewing options against budget constraints.',
        '[OPTIMIZER_AGENT] Filtered out expensive options. Adjusted plan.',
        '[EXECUTION_AGENT] Synthesizing final report based on optimized data...',
      ];
      let i = 0;
      interval = setInterval(() => {
        if (i < simulatedLogs.length) {
          setLogs((prev) => [...prev, simulatedLogs[i]]);
          i++;
        } else {
          clearInterval(interval);
        }
      }, 3000);
    }
    return () => clearInterval(interval);
  }, [taskState.status]);

  return (
    <div className="flex flex-col gap-8 w-full">
      {/* Status Header */}
      <div className="glass-card flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div className={`w-3 h-3 rounded-full ${
            taskState.status === 'completed' ? 'bg-green-500 shadow-[0_0_10px_#22c55e]' :
            taskState.status === 'failed' ? 'bg-red-500 shadow-[0_0_10px_#ef4444]' :
            'bg-yellow-500 shadow-[0_0_10px_#eab308] animate-pulse'
          }`}></div>
          <h2 className="text-xl font-semibold capitalize text-white">
            Task Status: <span className="text-primary">{taskState.status}</span>
          </h2>
        </div>
        <button 
          onClick={onReset}
          className="text-sm text-slate-400 hover:text-white transition-colors"
        >
          New Task
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Agent Activity Terminal */}
        <div className="glass-card !p-0 overflow-hidden flex flex-col h-[500px]">
          <div className="bg-surface-border p-3 border-b border-surface-border flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-red-500/80"></div>
            <div className="w-3 h-3 rounded-full bg-yellow-500/80"></div>
            <div className="w-3 h-3 rounded-full bg-green-500/80"></div>
            <span className="ml-2 text-xs text-slate-400 font-mono">agent_network.log</span>
          </div>
          <div className="flex-1 p-4 overflow-y-auto font-mono text-sm text-slate-300 flex flex-col gap-1">
            {logs.map((log, i) => (
              <div key={i} className="animate-fade-in opacity-80">
                <span className="text-primary mr-2">›</span>
                <span dangerouslySetInnerHTML={{ __html: (log ?? '').replace(/\[(.*?)\]/, '<span class="text-secondary">[$1]</span>') }} />
              </div>
            ))}
            {taskState.status === 'running' && (
              <div className="animate-pulse text-slate-500 mt-2">_</div>
            )}
          </div>
        </div>

        {/* Output Viewer */}
        <div className="glass-card flex flex-col h-[500px]">
          <h3 className="text-lg font-medium text-white mb-4 flex items-center gap-2 border-b border-surface-border pb-4">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-primary"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>
            Final Execution Report
          </h3>
          <div className="flex-1 overflow-y-auto pr-2 custom-scrollbar">
            {taskState.status === 'completed' ? (
              <div className="prose prose-invert prose-primary max-w-none">
                <ReactMarkdown>{taskState.result || "No result provided."}</ReactMarkdown>
              </div>
            ) : taskState.status === 'failed' ? (
              <div className="text-red-400">
                Failed to execute: {taskState.result}
              </div>
            ) : (
              <div className="h-full flex flex-col items-center justify-center text-slate-500">
                <div className="w-16 h-16 mb-4 rounded-full border-4 border-surface-border border-t-primary animate-spin"></div>
                <p>Awaiting final agent consensus...</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

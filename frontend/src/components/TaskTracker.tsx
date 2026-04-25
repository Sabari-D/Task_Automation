'use client';

import { useEffect, useRef, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface TaskTrackerProps {
  taskId: string;
  onReset: () => void;
}

interface TaskState {
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cached';
  result?: string;
}

const AGENT_LOGS = [
  '[GOAL_ANALYZER] 🧩 Parsing user intent and constraints...',
  '[GOAL_ANALYZER] 📌 Decomposing goal into logical steps...',
  '[RESEARCH_ANALYST] 🔍 Searching web and extracting real-world data...',
  '[RESEARCH_ANALYST] 📊 Comparing options and ranking best choices...',
  '[OPTIMIZER_ENGINE] 💰 Reducing costs and improving efficiency...',
  '[OPTIMIZER_ENGINE] ⚙️ Combining data into execution draft...',
  '[VALIDATOR_AGENT] 🧪 Verifying constraints and checking logic...',
  '[VALIDATOR_AGENT] 🔄 Feedback loop complete. Generating final output...',
];

export default function TaskTracker({ taskId, onReset }: TaskTrackerProps) {
  const [taskState, setTaskState] = useState<TaskState>({ status: 'pending' });
  const [logs, setLogs] = useState<string[]>([]);
  const [showDownloadMenu, setShowDownloadMenu] = useState(false);
  const pollingRef = useRef<NodeJS.Timeout | null>(null);
  const logIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const downloadMenuRef = useRef<HTMLDivElement>(null);
  const isDone = taskState.status === 'completed' || taskState.status === 'failed' || taskState.status === 'cached';
  const isReady = taskState.status === 'completed' || taskState.status === 'cached';

  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';

  // ── REST Polling ──────────────────────────────────────────────────────────
  useEffect(() => {
    const poll = async () => {
      try {
        const res = await fetch(`${apiUrl}/api/task/${taskId}`);
        if (!res.ok) return;
        const data = await res.json();
        if (data.status && data.status !== taskState.status) {
          setTaskState({ status: data.status, result: data.result });
        }
        if (data.status === 'completed' || data.status === 'failed' || data.status === 'cached') {
          if (pollingRef.current) clearInterval(pollingRef.current);
        }
      } catch (e) {
        console.error('Polling error:', e);
      }
    };

    poll();
    pollingRef.current = setInterval(poll, 2000);
    return () => {
      if (pollingRef.current) clearInterval(pollingRef.current);
    };
  }, [taskId, apiUrl]);

  // ── Animated logs ─────────────────────────────────────────────────────────
  useEffect(() => {
    if (logIntervalRef.current) clearInterval(logIntervalRef.current);
    if (isDone) return;

    setLogs(['[SYSTEM] Agents activated. Task dispatched...']);
    let i = 0;
    logIntervalRef.current = setInterval(() => {
      if (i < AGENT_LOGS.length) {
        setLogs(prev => [...prev, AGENT_LOGS[i]]);
        i++;
      } else {
        clearInterval(logIntervalRef.current!);
      }
    }, 800);

    return () => {
      if (logIntervalRef.current) clearInterval(logIntervalRef.current);
    };
  }, [isDone]);

  // ── Close dropdown on outside click ──────────────────────────────────────
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (downloadMenuRef.current && !downloadMenuRef.current.contains(e.target as Node)) {
        setShowDownloadMenu(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // ── Download Handlers ─────────────────────────────────────────────────────
  const downloadMarkdown = () => {
    if (!taskState.result) return;
    const blob = new Blob([taskState.result], { type: 'text/markdown;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `execution-report-${taskId.slice(0, 8)}.md`;
    a.click();
    URL.revokeObjectURL(url);
    setShowDownloadMenu(false);
  };

  const downloadPDF = () => {
    if (!taskState.result) return;

    const printWindow = window.open('', '_blank');
    if (!printWindow) return;

    // Convert simple markdown to readable HTML for PDF
    const htmlContent = taskState.result
      .replace(/^#{1}\s+(.+)$/gm, '<h1>$1</h1>')
      .replace(/^#{2}\s+(.+)$/gm, '<h2>$1</h2>')
      .replace(/^#{3}\s+(.+)$/gm, '<h3>$1</h3>')
      .replace(/^#{4}\s+(.+)$/gm, '<h4>$1</h4>')
      .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.+?)\*/g, '<em>$1</em>')
      .replace(/`(.+?)`/g, '<code>$1</code>')
      .replace(/^[-*]\s+(.+)$/gm, '<li>$1</li>')
      .replace(/(<li>.*<\/li>\n?)+/g, '<ul>$&</ul>')
      .replace(/^\d+\.\s+(.+)$/gm, '<li>$1</li>')
      .replace(/\n\n/g, '</p><p>')
      .replace(/\n/g, '<br/>');

    printWindow.document.write(`
      <!DOCTYPE html>
      <html>
      <head>
        <meta charset="UTF-8">
        <title>Execution Report — Auto-Worker Engine</title>
        <style>
          * { box-sizing: border-box; margin: 0; padding: 0; }
          body {
            font-family: 'Segoe UI', Georgia, serif;
            font-size: 14px;
            line-height: 1.8;
            color: #1e293b;
            padding: 48px 56px;
            max-width: 900px;
            margin: 0 auto;
          }
          .report-header {
            text-align: center;
            border-bottom: 3px solid #8b5cf6;
            padding-bottom: 24px;
            margin-bottom: 36px;
          }
          .report-header h1 {
            font-size: 28px;
            font-weight: 700;
            color: #8b5cf6;
            letter-spacing: -0.5px;
          }
          .report-header p {
            font-size: 12px;
            color: #64748b;
            margin-top: 6px;
          }
          h1 { font-size: 22px; font-weight: 700; color: #1e293b; margin: 28px 0 12px; }
          h2 { font-size: 18px; font-weight: 600; color: #334155; margin: 24px 0 10px; border-bottom: 1px solid #e2e8f0; padding-bottom: 4px; }
          h3 { font-size: 15px; font-weight: 600; color: #475569; margin: 20px 0 8px; }
          h4 { font-size: 14px; font-weight: 600; color: #64748b; margin: 16px 0 6px; }
          p { margin: 10px 0; color: #334155; }
          ul, ol { margin: 10px 0 10px 24px; }
          li { margin: 6px 0; }
          strong { color: #1e293b; }
          code { background: #f1f5f9; padding: 2px 6px; border-radius: 4px; font-family: monospace; font-size: 13px; color: #7c3aed; }
          .footer { margin-top: 48px; border-top: 1px solid #e2e8f0; padding-top: 16px; font-size: 11px; color: #94a3b8; text-align: center; }
          @media print { body { padding: 24px 32px; } }
        </style>
      </head>
      <body>
        <div class="report-header">
          <h1>⚡ Auto-Worker Engine — Execution Report</h1>
          <p>Task ID: ${taskId} &nbsp;|&nbsp; Generated: ${new Date().toLocaleString()}</p>
        </div>
        <div class="content"><p>${htmlContent}</p></div>
        <div class="footer">Generated by Auto-Worker Engine v1.0.0 &nbsp;|&nbsp; Multi-Agent AI System</div>
      </body>
      </html>
    `);
    printWindow.document.close();
    printWindow.focus();
    setTimeout(() => {
      printWindow.print();
      printWindow.close();
    }, 400);
    setShowDownloadMenu(false);
  };

  return (
    <div className="flex flex-col gap-8 w-full">
      {/* Status Header */}
      <div className="glass-card flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div className={`w-3 h-3 rounded-full ${
            taskState.status === 'completed' || taskState.status === 'cached'
              ? 'bg-green-500 shadow-[0_0_10px_#22c55e]'
              : taskState.status === 'failed'
              ? 'bg-red-500 shadow-[0_0_10px_#ef4444]'
              : 'bg-yellow-500 shadow-[0_0_10px_#eab308] animate-pulse'
          }`}></div>
          <h2 className="text-xl font-semibold capitalize text-foreground">
            Task Status: <span className="text-primary">{taskState.status}</span>
          </h2>
        </div>
        <button
          onClick={onReset}
          className="text-sm text-slate-400 hover:text-foreground transition-colors"
        >
          New Task
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Agent Activity Terminal */}
        <div className="glass-card !p-0 overflow-hidden flex flex-col h-[520px]">
          <div className="bg-surface-border p-3 border-b border-surface-border flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-red-500/80"></div>
            <div className="w-3 h-3 rounded-full bg-yellow-500/80"></div>
            <div className="w-3 h-3 rounded-full bg-green-500/80"></div>
            <span className="ml-2 text-xs text-slate-400 font-mono">agent_network.log</span>
          </div>
          <div className="flex-1 p-4 overflow-y-auto font-mono text-sm text-slate-300 flex flex-col gap-2">
            {logs.map((log, i) => (
              <div key={i} className="animate-fade-in opacity-80 leading-relaxed">
                <span className="text-primary mr-2">›</span>
                <span dangerouslySetInnerHTML={{ __html: (log ?? '').replace(/\[(.*?)\]/, '<span class="text-secondary">[$1]</span>') }} />
              </div>
            ))}
            {!isDone && (
              <div className="animate-pulse text-slate-500 mt-2">_</div>
            )}
            {isDone && (
              <div className="text-green-400 mt-2">
                <span className="text-primary mr-2">›</span>
                [SYSTEM] All agents completed. Report ready.
              </div>
            )}
          </div>
        </div>

        {/* Output Viewer */}
        <div className="glass-card flex flex-col h-[520px]">
          {/* Report Header Row */}
          <div className="flex items-center justify-between border-b border-surface-border pb-4 mb-4 flex-shrink-0">
            <h3 className="text-lg font-medium text-foreground flex items-center gap-2">
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-primary"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>
              Final Execution Report
            </h3>

            {/* Download Button — only visible when report is ready */}
            {isReady && (
              <div className="relative" ref={downloadMenuRef}>
                <button
                  id="download-report-btn"
                  onClick={() => setShowDownloadMenu(prev => !prev)}
                  className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-primary/20 hover:bg-primary/40 border border-primary/30 hover:border-primary/60 text-primary text-sm font-medium transition-all duration-200 hover:shadow-[0_0_12px_rgba(139,92,246,0.3)]"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
                  Download
                  <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" className={`transition-transform duration-200 ${showDownloadMenu ? 'rotate-180' : ''}`}><polyline points="6 9 12 15 18 9"/></svg>
                </button>

                {showDownloadMenu && (
                  <div className="absolute right-0 top-full mt-2 w-48 rounded-xl overflow-hidden border border-surface-border bg-[#0f172a]/95 backdrop-blur-xl shadow-2xl shadow-black/40 z-50 animate-fade-in">
                    <div className="p-1">
                      <button
                        id="download-markdown-btn"
                        onClick={downloadMarkdown}
                        className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-slate-400 hover:text-foreground hover:bg-primary/20 transition-all duration-150 group"
                      >
                        <span className="text-lg">📄</span>
                        <div className="text-left">
                          <div className="font-medium">Markdown (.md)</div>
                          <div className="text-xs text-slate-500 group-hover:text-slate-400">Raw formatted text</div>
                        </div>
                      </button>
                      <button
                        id="download-pdf-btn"
                        onClick={downloadPDF}
                        className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-slate-400 hover:text-foreground hover:bg-secondary/20 transition-all duration-150 group"
                      >
                        <span className="text-lg">📑</span>
                        <div className="text-left">
                          <div className="font-medium">PDF Report</div>
                          <div className="text-xs text-slate-500 group-hover:text-slate-400">Print-ready document</div>
                        </div>
                      </button>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Report Content */}
          <div className="flex-1 overflow-y-auto pr-1 custom-scrollbar">
            {isReady ? (
              <div className="report-prose">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>{taskState.result || 'No result provided.'}</ReactMarkdown>
              </div>
            ) : taskState.status === 'failed' ? (
              <div className="text-red-400 p-4 bg-red-500/10 rounded-lg border border-red-500/20">
                <strong>Execution Failed:</strong> {taskState.result}
              </div>
            ) : (
              <div className="h-full flex flex-col items-center justify-center text-slate-500">
                <div className="w-16 h-16 mb-4 rounded-full border-4 border-surface-border border-t-primary animate-spin"></div>
                <p>AI agents at work — results arriving shortly...</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

import { useState, useEffect, useRef, useCallback } from 'react';
import { useParams, Link } from 'react-router-dom';
import Editor from '@monaco-editor/react';
import { problemsAPI, submissionsAPI } from '../api/client';
import { useAuth } from '../context/AuthContext';
import { useSocket } from '../context/SocketContext';
import { useProctoring } from '../hooks/useProctoring';
import StatusBadge from '../components/StatusBadge';

const BOILERPLATE = `# Read input and solve the problem
# Example: a, b = map(int, input().split())
# print(a + b)

`;

export default function ProblemPage() {
    const { contestId, problemId } = useParams();
    const { isAuthenticated } = useAuth();
    const { joinContest, leaveContest, onEvent } = useSocket();

    const [problem, setProblem] = useState(null);
    const [code, setCode] = useState(BOILERPLATE);
    const [submissions, setSubmissions] = useState([]);
    const [submitting, setSubmitting] = useState(false);
    const [running, setRunning] = useState(false);
    const [activePanel, setActivePanel] = useState('description');
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    // RUN mode output
    const [runOutput, setRunOutput] = useState(null);

    // Proctoring
    const { violations, isFlagged, isFullscreen, enterFullscreen } = useProctoring(
        parseInt(contestId),
        true
    );

    const pollRef = useRef(null);

    // Join contest room for real-time updates
    useEffect(() => {
        if (contestId) {
            joinContest(parseInt(contestId));
        }
        return () => {
            if (contestId) leaveContest(parseInt(contestId));
        };
    }, [contestId, joinContest, leaveContest]);

    // Listen for real-time submission updates
    useEffect(() => {
        const cleanup = onEvent('submission_result', (data) => {
            setSubmissions((prev) =>
                prev.map((s) => (s.id === data.id ? { ...s, ...data } : s))
            );
            // Clear polling if we got a final status
            if (data.status !== 'pending' && data.status !== 'running' && pollRef.current) {
                clearInterval(pollRef.current);
                pollRef.current = null;
            }
        });
        return cleanup;
    }, [onEvent]);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const problemRes = await problemsAPI.get(problemId);
                setProblem(problemRes.data.problem);

                if (isAuthenticated) {
                    const subRes = await submissionsAPI.forProblem(problemId);
                    setSubmissions(subRes.data.submissions);
                }
            } catch (err) {
                setError('Failed to load problem');
            } finally {
                setLoading(false);
            }
        };
        fetchData();
        return () => { if (pollRef.current) clearInterval(pollRef.current); };
    }, [problemId, isAuthenticated]);

    // ── RUN: Execute sample test cases only ─────────────────────────
    const handleRun = async () => {
        if (!code.trim()) return;
        setRunning(true);
        setError('');
        setActivePanel('output');
        setRunOutput(null);

        try {
            const res = await submissionsAPI.run({
                problem_id: parseInt(problemId),
                contest_id: parseInt(contestId),
                code: code,
                language: 'python',
            });
            setRunOutput(res.data);
        } catch (err) {
            setError(err.response?.data?.error || 'Run failed');
        } finally {
            setRunning(false);
        }
    };

    // ── SUBMIT: Full judging with all test cases ────────────────────
    const handleSubmit = async () => {
        if (!code.trim()) return;
        setSubmitting(true);
        setError('');
        setActivePanel('submissions');

        try {
            const res = await submissionsAPI.create({
                problem_id: parseInt(problemId),
                contest_id: parseInt(contestId),
                code: code,
                language: 'python',
            });

            const newSubmission = res.data.submission;
            setSubmissions((prev) => [newSubmission, ...prev]);

            // Poll for result as fallback (SocketIO should handle this faster)
            pollRef.current = setInterval(async () => {
                try {
                    const check = await submissionsAPI.get(newSubmission.id);
                    const updated = check.data.submission;
                    setSubmissions((prev) =>
                        prev.map((s) => (s.id === updated.id ? updated : s))
                    );
                    if (updated.status !== 'pending' && updated.status !== 'running') {
                        clearInterval(pollRef.current);
                        pollRef.current = null;
                    }
                } catch { }
            }, 2000);
        } catch (err) {
            setError(err.response?.data?.error || 'Submission failed');
        } finally {
            setSubmitting(false);
        }
    };

    if (loading) {
        return (
            <div className="flex h-[calc(100vh-64px)]">
                <div className="w-1/2 p-6">
                    <div className="skeleton h-8 w-64 mb-4" />
                    <div className="skeleton h-4 w-full mb-2" />
                    <div className="skeleton h-4 w-3/4 mb-2" />
                    <div className="skeleton h-32 w-full mt-4" />
                </div>
                <div className="w-1/2 bg-arena-surface p-4">
                    <div className="skeleton h-full w-full rounded-lg" />
                </div>
            </div>
        );
    }

    if (!problem) {
        return (
            <div className="flex h-96 items-center justify-center">
                <p className="text-arena-text-muted">Problem not found</p>
            </div>
        );
    }

    return (
        <div className="flex h-[calc(100vh-64px)] overflow-hidden bg-arena-bg">
            {/* Left Panel - Problem / Submissions / Output */}
            <div className="flex w-1/2 flex-col border-r border-arena-border bg-arena-bg">
                {/* Panel Tabs */}
                <div className="flex border-b border-arena-border">
                    {['description', 'output', 'submissions'].map((tab) => (
                        <button
                            key={tab}
                            onClick={() => setActivePanel(tab)}
                            className={`cursor-pointer px-5 py-3 text-sm font-medium capitalize transition-colors border-b-2 ${activePanel === tab
                                ? 'border-arena-primary text-arena-text'
                                : 'border-transparent text-arena-text-muted hover:text-arena-text bg-transparent'
                                }`}
                        >
                            {tab}
                            {tab === 'submissions' && submissions.length > 0 && (
                                <span className="ml-2 rounded-md bg-arena-surface px-2 py-0.5 text-[10px] font-bold tracking-wider">
                                    {submissions.length}
                                </span>
                            )}
                            {tab === 'output' && runOutput && (
                                <span className={`ml-2 inline-block h-2 w-2 rounded-full ${runOutput.status === 'passed' ? 'bg-arena-success' : 'bg-arena-danger'}`} />
                            )}
                        </button>
                    ))}

                    {/* Proctor Violation Badge */}
                    {violations > 0 && (
                        <div className="ml-auto flex items-center px-4">
                            <span className={`flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[10px] font-bold tracking-wider ${isFlagged
                                ? 'bg-arena-danger/15 text-arena-danger border border-arena-danger/20'
                                : 'bg-arena-warning/10 text-arena-warning border border-arena-warning/20'
                                }`}>
                                <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.232 16.5c-.77.833.192 2.5 1.732 2.5z" /></svg>
                                {violations} {isFlagged ? 'FLAGGED' : 'violations'}
                            </span>
                        </div>
                    )}
                </div>

                {/* Panel Content */}
                <div className="flex-1 overflow-y-auto p-8">
                    {/* ─── Description Panel ─────────────────────── */}
                    {activePanel === 'description' && (
                        <div className="animate-fade-in max-w-3xl">
                            <div className="mb-6 flex flex-col gap-2">
                                <div className="flex items-center justify-between">
                                    <h1 className="text-2xl font-bold tracking-tight text-arena-text">{problem.title}</h1>
                                    <span className="rounded-md bg-arena-surface border border-arena-border px-3 py-1 text-xs font-semibold tracking-wide text-arena-primary">
                                        {problem.points} pts
                                    </span>
                                </div>
                                <div className="flex gap-4 text-xs font-medium text-arena-text-muted">
                                    <span>Time: {problem.time_limit}s</span>
                                    <span>Memory: {problem.memory_limit}MB</span>
                                </div>
                            </div>

                            <div className="space-y-8 text-sm leading-relaxed text-arena-text-muted">
                                <div>
                                    <h3 className="mb-3 font-semibold text-arena-text text-base">Problem Statement</h3>
                                    <p className="whitespace-pre-wrap">{problem.description}</p>
                                </div>

                                {problem.input_format && (
                                    <div>
                                        <h3 className="mb-3 font-semibold text-arena-text text-base">Input Format</h3>
                                        <p className="whitespace-pre-wrap">{problem.input_format}</p>
                                    </div>
                                )}

                                {problem.output_format && (
                                    <div>
                                        <h3 className="mb-3 font-semibold text-arena-text text-base">Output Format</h3>
                                        <p className="whitespace-pre-wrap">{problem.output_format}</p>
                                    </div>
                                )}

                                {problem.constraints && (
                                    <div>
                                        <h3 className="mb-3 font-semibold text-arena-text text-base">Constraints</h3>
                                        <div className="rounded-md bg-arena-surface border border-arena-border p-3 font-mono text-xs text-arena-primary inline-block">
                                            <p className="whitespace-pre-wrap">{problem.constraints}</p>
                                        </div>
                                    </div>
                                )}

                                {(problem.sample_input || problem.sample_output) && (
                                    <div className="pt-4 border-t border-arena-border">
                                        <h3 className="mb-4 font-semibold text-arena-text text-base">Examples</h3>
                                        <div className="space-y-4">
                                            <div>
                                                <p className="mb-2 text-xs font-semibold text-arena-text uppercase tracking-wider">Input</p>
                                                <pre className="rounded-md bg-arena-surface border border-arena-border p-4 text-xs font-mono whitespace-pre-wrap text-arena-text">
                                                    {problem.sample_input}
                                                </pre>
                                            </div>
                                            <div>
                                                <p className="mb-2 text-xs font-semibold text-arena-text uppercase tracking-wider">Output</p>
                                                <pre className="rounded-md bg-arena-surface border border-arena-border p-4 text-xs font-mono whitespace-pre-wrap text-arena-text">
                                                    {problem.sample_output}
                                                </pre>
                                            </div>
                                        </div>
                                    </div>
                                )}
                            </div>
                        </div>
                    )}

                    {/* ─── Output Panel (RUN results) ────────────── */}
                    {activePanel === 'output' && (
                        <div className="animate-fade-in max-w-3xl">
                            <h2 className="mb-6 text-base font-semibold text-arena-text border-b border-arena-border pb-2">
                                Run Output
                            </h2>

                            {!runOutput ? (
                                <div className="flex flex-col items-center justify-center py-20 text-center">
                                    <svg className="w-12 h-12 text-arena-text-muted/30 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                                    </svg>
                                    <p className="text-sm text-arena-text-muted">Click <span className="font-semibold text-arena-info">Run</span> to test your code against sample cases</p>
                                    <p className="text-xs text-arena-text-muted/60 mt-1">Results won't be saved or affect your score</p>
                                </div>
                            ) : (
                                <div className="space-y-4">
                                    {/* Overall status */}
                                    <div className={`flex items-center justify-between rounded-lg border p-4 ${runOutput.status === 'passed'
                                        ? 'bg-arena-success/5 border-arena-success/20'
                                        : 'bg-arena-danger/5 border-arena-danger/20'
                                        }`}>
                                        <div className="flex items-center gap-3">
                                            <span className={`inline-flex h-8 w-8 items-center justify-center rounded-full text-sm ${runOutput.status === 'passed'
                                                ? 'bg-arena-success/20 text-arena-success'
                                                : 'bg-arena-danger/20 text-arena-danger'
                                                }`}>
                                                {runOutput.status === 'passed' ? '✓' : '✗'}
                                            </span>
                                            <div>
                                                <p className={`text-sm font-semibold capitalize ${runOutput.status === 'passed' ? 'text-arena-success' : 'text-arena-danger'
                                                    }`}>
                                                    {runOutput.status.replace(/_/g, ' ')}
                                                </p>
                                                <p className="text-xs text-arena-text-muted">
                                                    {runOutput.passed}/{runOutput.total} sample cases passed
                                                </p>
                                            </div>
                                        </div>
                                    </div>

                                    {/* Individual test case results */}
                                    {runOutput.results.map((r, idx) => (
                                        <div key={idx} className="rounded-lg border border-arena-border bg-arena-surface overflow-hidden">
                                            <div className={`flex items-center justify-between px-4 py-3 border-b border-arena-border/50 ${r.status === 'passed'
                                                ? 'bg-arena-success/5'
                                                : 'bg-arena-danger/5'
                                                }`}>
                                                <span className="text-xs font-bold font-mono uppercase tracking-widest text-arena-text-muted">
                                                    Sample Case {r.test_case}
                                                </span>
                                                <div className="flex items-center gap-3">
                                                    <span className="text-[10px] font-mono text-arena-text-muted">{r.execution_time}s</span>
                                                    <StatusBadge status={r.status === 'passed' ? 'accepted' : r.status} />
                                                </div>
                                            </div>
                                            <div className="p-4 space-y-3">
                                                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                                                    <div>
                                                        <p className="text-[10px] uppercase font-semibold text-arena-text-muted mb-1.5">Input</p>
                                                        <pre className="rounded bg-arena-bg border border-arena-border/50 p-3 text-xs font-mono whitespace-pre-wrap text-arena-text">{r.input}</pre>
                                                    </div>
                                                    <div>
                                                        <p className="text-[10px] uppercase font-semibold text-arena-text-muted mb-1.5">Expected</p>
                                                        <pre className="rounded bg-arena-bg border border-arena-border/50 p-3 text-xs font-mono whitespace-pre-wrap text-arena-text">{r.expected_output}</pre>
                                                    </div>
                                                </div>
                                                <div>
                                                    <p className="text-[10px] uppercase font-semibold text-arena-text-muted mb-1.5">Your Output</p>
                                                    <pre className={`rounded border p-3 text-xs font-mono whitespace-pre-wrap ${r.status === 'passed'
                                                        ? 'bg-arena-success/5 border-arena-success/20 text-arena-success'
                                                        : 'bg-arena-danger/5 border-arena-danger/20 text-arena-danger'
                                                        }`}>{r.actual_output || '(empty)'}</pre>
                                                </div>
                                                {r.stderr && (
                                                    <div>
                                                        <p className="text-[10px] uppercase font-semibold text-arena-danger mb-1.5">Stderr / Stack Trace</p>
                                                        <pre className="rounded bg-arena-danger/5 border border-arena-danger/20 p-3 text-xs font-mono whitespace-pre-wrap text-arena-danger/80 max-h-40 overflow-y-auto">{r.stderr}</pre>
                                                    </div>
                                                )}
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    )}

                    {/* ─── Submissions Panel ──────────────────────── */}
                    {activePanel === 'submissions' && (
                        <div className="animate-fade-in max-w-3xl">
                            <h2 className="mb-6 text-base font-semibold text-arena-text border-b border-arena-border pb-2">Submission History</h2>
                            {submissions.length === 0 ? (
                                <p className="text-sm text-arena-text-muted italic">No submissions recorded for this problem.</p>
                            ) : (
                                <div className="space-y-3">
                                    {submissions.map((sub) => (
                                        <div
                                            key={sub.id}
                                            className="group flex flex-col sm:flex-row items-start sm:items-center justify-between rounded-md border border-arena-border bg-arena-surface p-4 transition-colors hover:border-arena-border/80"
                                        >
                                            <div className="flex items-center gap-4 mb-2 sm:mb-0">
                                                <StatusBadge status={sub.status} />
                                                <span className="text-sm font-medium text-arena-text-muted">
                                                    {sub.test_cases_passed}/{sub.total_test_cases} passed
                                                </span>
                                            </div>
                                            <div className="flex items-center gap-4 text-xs font-mono text-arena-text-muted">
                                                {sub.execution_time != null && (
                                                    <span>{sub.execution_time.toFixed(3)}s</span>
                                                )}
                                                <span>
                                                    {new Date(sub.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                                                </span>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    )}
                </div>
            </div>

            {/* Right Panel - Code Editor */}
            <div className="flex w-1/2 flex-col bg-arena-bg relative">
                {/* Editor Header */}
                <div className="flex items-center justify-between px-6 py-3 border-b border-arena-border bg-arena-surface/30">
                    <div className="flex items-center gap-3">
                        <span className="text-xs font-semibold tracking-wide text-arena-text-muted uppercase">
                            Python 3
                        </span>
                        {!isFullscreen && (
                            <button
                                onClick={enterFullscreen}
                                className="cursor-pointer rounded bg-arena-warning/10 border border-arena-warning/20 px-2 py-1 text-[10px] font-bold text-arena-warning hover:bg-arena-warning/20 transition-colors"
                                title="Re-enter fullscreen (proctored mode)"
                            >
                                ⛶ Fullscreen
                            </button>
                        )}
                    </div>
                    <div className="flex items-center gap-3">
                        {/* RUN button */}
                        <button
                            onClick={handleRun}
                            disabled={running || !isAuthenticated}
                            className="cursor-pointer rounded-md border border-arena-border bg-arena-surface px-5 py-1.5 text-sm font-medium text-arena-text transition-all hover:bg-arena-surface-hover hover:border-arena-primary/40 disabled:cursor-not-allowed disabled:opacity-50"
                        >
                            {running ? (
                                <span className="inline-flex items-center gap-2">
                                    <span className="h-3 w-3 animate-spin rounded-full border-2 border-arena-primary/30 border-t-arena-primary" />
                                    Running...
                                </span>
                            ) : (
                                <span className="inline-flex items-center gap-1.5">
                                    <svg className="w-3.5 h-3.5 text-arena-success" fill="currentColor" viewBox="0 0 24 24"><path d="M8 5v14l11-7z" /></svg>
                                    Run
                                </span>
                            )}
                        </button>

                        {/* SUBMIT button */}
                        <button
                            onClick={handleSubmit}
                            disabled={submitting || !isAuthenticated}
                            className="btn-primary px-6 py-1.5 text-sm disabled:cursor-not-allowed disabled:opacity-50"
                        >
                            {submitting ? (
                                <span className="inline-flex items-center gap-2">
                                    <span className="h-3 w-3 animate-spin rounded-full border-2 border-white/30 border-t-white" />
                                    Judging...
                                </span>
                            ) : (
                                <span className="inline-flex items-center gap-1.5">
                                    <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" /></svg>
                                    Submit
                                </span>
                            )}
                        </button>
                    </div>
                </div>

                {error && (
                    <div className="absolute top-16 right-6 left-6 z-10 rounded-md bg-arena-danger/10 border border-arena-danger/20 px-4 py-3 text-sm text-arena-danger shadow-lg backdrop-blur-sm animate-fade-in truncate">
                        {error}
                    </div>
                )}

                {/* Monaco Editor Wrapper */}
                <div className="flex-1 w-full bg-transparent p-4">
                    <div className="h-full w-full rounded-md overflow-hidden outline outline-1 outline-arena-border/50 bg-[#1e1e1e]">
                        <Editor
                            height="100%"
                            language="python"
                            theme="vs-dark"
                            value={code}
                            onChange={(value) => setCode(value || '')}
                            options={{
                                fontSize: 14,
                                fontFamily: "'JetBrains Mono', 'Fira Code', monospace",
                                fontLigatures: true,
                                minimap: { enabled: false },
                                padding: { top: 24, bottom: 24 },
                                scrollBeyondLastLine: false,
                                lineNumbers: 'on',
                                lineNumbersMinChars: 4,
                                renderLineHighlight: 'none',
                                wordWrap: 'on',
                                tabSize: 4,
                                automaticLayout: true,
                                cursorBlinking: 'smooth',
                                cursorSmoothCaretAnimation: 'on',
                                formatOnPaste: true,
                            }}
                        />
                    </div>
                </div>
            </div>
        </div>
    );
}

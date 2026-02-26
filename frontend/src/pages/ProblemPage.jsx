import { useState, useEffect, useRef } from 'react';
import { useParams, Link } from 'react-router-dom';
import Editor from '@monaco-editor/react';
import { problemsAPI, submissionsAPI } from '../api/client';
import { useAuth } from '../context/AuthContext';
import StatusBadge from '../components/StatusBadge';

const BOILERPLATE = `# Read input and solve the problem
# Example: a, b = map(int, input().split())
# print(a + b)

`;

export default function ProblemPage() {
    const { contestId, problemId } = useParams();
    const { isAuthenticated } = useAuth();

    const [problem, setProblem] = useState(null);
    const [code, setCode] = useState(BOILERPLATE);
    const [submissions, setSubmissions] = useState([]);
    const [submitting, setSubmitting] = useState(false);
    const [activePanel, setActivePanel] = useState('description');
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const pollRef = useRef(null);

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

            // Poll for result
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
                <div className="w-1/2 bg-arena-surface-2 p-4">
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
            {/* Left Panel - Problem / Submissions */}
            <div className="flex w-1/2 flex-col border-r border-arena-border bg-arena-bg">
                {/* Panel Tabs (Minimalist) */}
                <div className="flex border-b border-arena-border">
                    {['description', 'submissions'].map((tab) => (
                        <button
                            key={tab}
                            onClick={() => setActivePanel(tab)}
                            className={`cursor-pointer px-6 py-3 text-sm font-medium capitalize transition-colors border-b-2 ${activePanel === tab
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
                        </button>
                    ))}
                </div>

                {/* Panel Content */}
                <div className="flex-1 overflow-y-auto p-8">
                    {activePanel === 'description' ? (
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
                    ) : (
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
                    <div className="flex items-center gap-2">
                        <span className="text-xs font-semibold tracking-wide text-arena-text-muted uppercase">
                            Python 3
                        </span>
                    </div>
                    <button
                        onClick={handleSubmit}
                        disabled={submitting || !isAuthenticated}
                        className="btn-primary px-6 py-1.5 text-sm disabled:cursor-not-allowed disabled:opacity-50"
                    >
                        {submitting ? (
                            <span className="inline-flex items-center gap-2">
                                <span className="h-3 w-3 animate-spin rounded-full border-2 border-white/30 border-t-white" />
                                Evaluating...
                            </span>
                        ) : (
                            'Submit Code'
                        )}
                    </button>
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

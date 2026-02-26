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
        <div className="flex h-[calc(100vh-64px)] overflow-hidden">
            {/* Left Panel - Problem / Submissions */}
            <div className="flex w-1/2 flex-col border-r border-arena-border">
                {/* Panel Tabs */}
                <div className="flex border-b border-arena-border bg-arena-surface">
                    {['description', 'submissions'].map((tab) => (
                        <button
                            key={tab}
                            onClick={() => setActivePanel(tab)}
                            className={`cursor-pointer border-b-2 bg-transparent px-4 py-2.5 text-sm font-medium capitalize transition-colors ${activePanel === tab
                                    ? 'border-arena-primary text-arena-primary-light'
                                    : 'border-transparent text-arena-text-muted hover:text-arena-text'
                                }`}
                        >
                            {tab}
                            {tab === 'submissions' && submissions.length > 0 && (
                                <span className="ml-1.5 rounded-full bg-arena-surface-2 px-1.5 py-0.5 text-xs">
                                    {submissions.length}
                                </span>
                            )}
                        </button>
                    ))}
                </div>

                {/* Panel Content */}
                <div className="flex-1 overflow-y-auto p-6">
                    {activePanel === 'description' ? (
                        <div className="animate-fade-in">
                            <div className="mb-4 flex items-center justify-between">
                                <h1 className="text-2xl font-bold">{problem.title}</h1>
                                <span className="rounded-full bg-arena-accent/10 px-3 py-1 text-xs font-semibold text-arena-accent">
                                    {problem.points} pts
                                </span>
                            </div>

                            <div className="mb-4 flex gap-4 text-xs text-arena-text-muted">
                                <span>⏱ Time: {problem.time_limit}s</span>
                                <span>💾 Memory: {problem.memory_limit}MB</span>
                            </div>

                            <div className="space-y-6 text-sm leading-relaxed text-arena-text">
                                <div>
                                    <h3 className="mb-2 font-semibold text-arena-text">Description</h3>
                                    <p className="whitespace-pre-wrap">{problem.description}</p>
                                </div>

                                {problem.input_format && (
                                    <div>
                                        <h3 className="mb-2 font-semibold text-arena-text">Input Format</h3>
                                        <p className="whitespace-pre-wrap">{problem.input_format}</p>
                                    </div>
                                )}

                                {problem.output_format && (
                                    <div>
                                        <h3 className="mb-2 font-semibold text-arena-text">Output Format</h3>
                                        <p className="whitespace-pre-wrap">{problem.output_format}</p>
                                    </div>
                                )}

                                {problem.constraints && (
                                    <div>
                                        <h3 className="mb-2 font-semibold text-arena-text">Constraints</h3>
                                        <p className="whitespace-pre-wrap text-arena-text-muted">{problem.constraints}</p>
                                    </div>
                                )}

                                {(problem.sample_input || problem.sample_output) && (
                                    <div>
                                        <h3 className="mb-2 font-semibold text-arena-text">Sample</h3>
                                        <div className="grid grid-cols-2 gap-3">
                                            <div>
                                                <p className="mb-1 text-xs font-medium text-arena-text-muted">Input</p>
                                                <pre className="rounded-lg bg-arena-surface-2 border border-arena-border p-3 text-xs text-arena-accent font-mono whitespace-pre-wrap">
                                                    {problem.sample_input}
                                                </pre>
                                            </div>
                                            <div>
                                                <p className="mb-1 text-xs font-medium text-arena-text-muted">Output</p>
                                                <pre className="rounded-lg bg-arena-surface-2 border border-arena-border p-3 text-xs text-arena-success font-mono whitespace-pre-wrap">
                                                    {problem.sample_output}
                                                </pre>
                                            </div>
                                        </div>
                                    </div>
                                )}
                            </div>
                        </div>
                    ) : (
                        <div className="animate-fade-in">
                            <h2 className="mb-4 text-lg font-semibold">Your Submissions</h2>
                            {submissions.length === 0 ? (
                                <p className="text-sm text-arena-text-muted">No submissions yet</p>
                            ) : (
                                <div className="space-y-2">
                                    {submissions.map((sub) => (
                                        <div
                                            key={sub.id}
                                            className="flex items-center justify-between rounded-lg border border-arena-border bg-arena-surface-2 p-3"
                                        >
                                            <div className="flex items-center gap-3">
                                                <StatusBadge status={sub.status} />
                                                <span className="text-xs text-arena-text-muted">
                                                    {sub.test_cases_passed}/{sub.total_test_cases} passed
                                                </span>
                                            </div>
                                            <div className="flex items-center gap-3 text-xs text-arena-text-muted">
                                                {sub.execution_time && (
                                                    <span>{sub.execution_time.toFixed(3)}s</span>
                                                )}
                                                <span>
                                                    {new Date(sub.created_at).toLocaleTimeString()}
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
            <div className="flex w-1/2 flex-col bg-arena-surface">
                {/* Editor Header */}
                <div className="flex items-center justify-between border-b border-arena-border px-4 py-2.5">
                    <div className="flex items-center gap-2">
                        <span className="rounded-md bg-arena-primary/10 px-2 py-0.5 text-xs font-medium text-arena-primary-light">
                            Python 3
                        </span>
                    </div>
                    <button
                        onClick={handleSubmit}
                        disabled={submitting || !isAuthenticated}
                        className="cursor-pointer rounded-lg bg-arena-success px-5 py-1.5 text-sm font-semibold text-white transition-all hover:bg-arena-success/80 hover:shadow-lg disabled:cursor-not-allowed disabled:opacity-50"
                    >
                        {submitting ? (
                            <span className="inline-flex items-center gap-2">
                                <span className="h-3 w-3 animate-spin rounded-full border-2 border-white border-t-transparent" />
                                Judging...
                            </span>
                        ) : (
                            '▶ Submit'
                        )}
                    </button>
                </div>

                {error && (
                    <div className="mx-4 mt-2 rounded-lg bg-arena-danger/10 border border-arena-danger/20 px-3 py-2 text-xs text-arena-danger">
                        {error}
                    </div>
                )}

                {/* Monaco Editor */}
                <div className="flex-1">
                    <Editor
                        height="100%"
                        language="python"
                        theme="vs-dark"
                        value={code}
                        onChange={(value) => setCode(value || '')}
                        options={{
                            fontSize: 14,
                            fontFamily: "'Cascadia Code', 'Fira Code', 'JetBrains Mono', monospace",
                            minimap: { enabled: false },
                            padding: { top: 16 },
                            scrollBeyondLastLine: false,
                            lineNumbers: 'on',
                            renderLineHighlight: 'gutter',
                            wordWrap: 'on',
                            tabSize: 4,
                            automaticLayout: true,
                        }}
                    />
                </div>
            </div>
        </div>
    );
}

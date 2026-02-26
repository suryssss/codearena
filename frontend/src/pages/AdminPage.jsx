import { useState, useEffect } from 'react';
import { contestsAPI, problemsAPI } from '../api/client';

export default function AdminPage() {
    const [activeTab, setActiveTab] = useState('contests');
    const [contests, setContests] = useState([]);
    const [loading, setLoading] = useState(true);
    const [message, setMessage] = useState({ type: '', text: '' });

    // Contest form
    const [contestForm, setContestForm] = useState({
        title: '', description: '', start_time: '', end_time: '', is_published: false,
    });

    // Problem form
    const [problemForm, setProblemForm] = useState({
        contest_id: '', title: '', description: '',
        input_format: '', output_format: '', constraints: '',
        sample_input: '', sample_output: '',
        time_limit: 2, memory_limit: 256, points: 100,
        test_cases: [{ input_data: '', expected_output: '', is_sample: false }],
    });

    useEffect(() => {
        fetchContests();
    }, []);

    const fetchContests = async () => {
        try {
            const res = await contestsAPI.list();
            setContests(res.data.contests);
        } catch (err) {
            showMessage('error', 'Failed to load contests');
        } finally {
            setLoading(false);
        }
    };

    const showMessage = (type, text) => {
        setMessage({ type, text });
        setTimeout(() => setMessage({ type: '', text: '' }), 5000);
    };

    const handleCreateContest = async (e) => {
        e.preventDefault();
        try {
            await contestsAPI.create({
                ...contestForm,
                start_time: new Date(contestForm.start_time).toISOString(),
                end_time: new Date(contestForm.end_time).toISOString(),
            });
            showMessage('success', 'Contest created successfully!');
            setContestForm({ title: '', description: '', start_time: '', end_time: '', is_published: false });
            fetchContests();
        } catch (err) {
            showMessage('error', err.response?.data?.error || 'Failed to create contest');
        }
    };

    const handleCreateProblem = async (e) => {
        e.preventDefault();
        try {
            await problemsAPI.create({
                ...problemForm,
                contest_id: parseInt(problemForm.contest_id),
                test_cases: problemForm.test_cases.filter(tc => tc.input_data || tc.expected_output),
            });
            showMessage('success', 'Problem created successfully!');
            setProblemForm({
                contest_id: problemForm.contest_id, title: '', description: '',
                input_format: '', output_format: '', constraints: '',
                sample_input: '', sample_output: '',
                time_limit: 2, memory_limit: 256, points: 100,
                test_cases: [{ input_data: '', expected_output: '', is_sample: false }],
            });
        } catch (err) {
            showMessage('error', err.response?.data?.error || 'Failed to create problem');
        }
    };

    const addTestCase = () => {
        setProblemForm((prev) => ({
            ...prev,
            test_cases: [...prev.test_cases, { input_data: '', expected_output: '', is_sample: false }],
        }));
    };

    const updateTestCase = (index, field, value) => {
        setProblemForm((prev) => ({
            ...prev,
            test_cases: prev.test_cases.map((tc, i) =>
                i === index ? { ...tc, [field]: value } : tc
            ),
        }));
    };

    const removeTestCase = (index) => {
        setProblemForm((prev) => ({
            ...prev,
            test_cases: prev.test_cases.filter((_, i) => i !== index),
        }));
    };

    const handleDeleteContest = async (id) => {
        if (!window.confirm('Are you sure? This will delete all problems and submissions.')) return;
        try {
            await contestsAPI.delete(id);
            showMessage('success', 'Contest deleted');
            fetchContests();
        } catch (err) {
            showMessage('error', 'Failed to delete contest');
        }
    };

    const inputCls = "w-full rounded-lg border border-arena-border bg-arena-surface-2 px-4 py-2.5 text-arena-text outline-none transition-colors placeholder:text-arena-text-muted/50 focus:border-arena-primary focus:ring-1 focus:ring-arena-primary text-sm";
    const labelCls = "mb-1.5 block text-sm font-medium text-arena-text-muted";

    return (
        <div className="mx-auto max-w-5xl px-4 py-8 sm:px-6 animate-fade-in">
            <h1 className="mb-2 text-3xl font-bold">Admin Panel</h1>
            <p className="mb-8 text-arena-text-muted">Manage contests and problems</p>

            {message.text && (
                <div className={`mb-6 rounded-lg border px-4 py-3 text-sm ${message.type === 'success'
                        ? 'bg-arena-success/10 border-arena-success/20 text-arena-success'
                        : 'bg-arena-danger/10 border-arena-danger/20 text-arena-danger'
                    }`}>
                    {message.text}
                </div>
            )}

            {/* Tabs */}
            <div className="mb-6 flex border-b border-arena-border">
                {['contests', 'problems'].map((tab) => (
                    <button
                        key={tab}
                        onClick={() => setActiveTab(tab)}
                        className={`cursor-pointer border-b-2 bg-transparent px-4 py-3 text-sm font-medium capitalize transition-colors ${activeTab === tab
                                ? 'border-arena-primary text-arena-primary-light'
                                : 'border-transparent text-arena-text-muted hover:text-arena-text'
                            }`}
                    >
                        {tab === 'contests' ? '🏆 Manage Contests' : '📝 Create Problem'}
                    </button>
                ))}
            </div>

            {/* Contests Tab */}
            {activeTab === 'contests' && (
                <div className="space-y-8">
                    {/* Create Form */}
                    <div className="rounded-xl border border-arena-border bg-arena-surface p-6">
                        <h2 className="mb-4 text-lg font-semibold">Create New Contest</h2>
                        <form onSubmit={handleCreateContest} className="space-y-4">
                            <div>
                                <label className={labelCls}>Contest Title</label>
                                <input type="text" className={inputCls} placeholder="Weekly Contest #1"
                                    value={contestForm.title} onChange={(e) => setContestForm({ ...contestForm, title: e.target.value })} required />
                            </div>
                            <div>
                                <label className={labelCls}>Description</label>
                                <textarea className={inputCls + " min-h-[80px] resize-y"} placeholder="Contest description..."
                                    value={contestForm.description} onChange={(e) => setContestForm({ ...contestForm, description: e.target.value })} />
                            </div>
                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className={labelCls}>Start Time</label>
                                    <input type="datetime-local" className={inputCls}
                                        value={contestForm.start_time} onChange={(e) => setContestForm({ ...contestForm, start_time: e.target.value })} required />
                                </div>
                                <div>
                                    <label className={labelCls}>End Time</label>
                                    <input type="datetime-local" className={inputCls}
                                        value={contestForm.end_time} onChange={(e) => setContestForm({ ...contestForm, end_time: e.target.value })} required />
                                </div>
                            </div>
                            <div className="flex items-center gap-2">
                                <input type="checkbox" id="published" className="cursor-pointer accent-arena-primary"
                                    checked={contestForm.is_published} onChange={(e) => setContestForm({ ...contestForm, is_published: e.target.checked })} />
                                <label htmlFor="published" className="cursor-pointer text-sm text-arena-text-muted">Publish immediately</label>
                            </div>
                            <button type="submit"
                                className="cursor-pointer rounded-lg bg-arena-primary px-6 py-2.5 font-medium text-white transition-all hover:bg-arena-primary/80">
                                Create Contest
                            </button>
                        </form>
                    </div>

                    {/* Contest List */}
                    <div>
                        <h2 className="mb-4 text-lg font-semibold">Existing Contests</h2>
                        <div className="space-y-3">
                            {contests.map((c) => (
                                <div key={c.id} className="flex items-center justify-between rounded-xl border border-arena-border bg-arena-surface p-4">
                                    <div>
                                        <h3 className="font-semibold">{c.title}</h3>
                                        <span className="text-xs text-arena-text-muted">ID: {c.id} · {c.status} · {c.participant_count} participants</span>
                                    </div>
                                    <button onClick={() => handleDeleteContest(c.id)}
                                        className="cursor-pointer rounded-lg bg-arena-danger/10 px-3 py-1.5 text-xs text-arena-danger transition-colors hover:bg-arena-danger/20">
                                        Delete
                                    </button>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            )}

            {/* Problems Tab */}
            {activeTab === 'problems' && (
                <div className="rounded-xl border border-arena-border bg-arena-surface p-6">
                    <h2 className="mb-4 text-lg font-semibold">Create New Problem</h2>
                    <form onSubmit={handleCreateProblem} className="space-y-4">
                        <div>
                            <label className={labelCls}>Contest</label>
                            <select className={inputCls}
                                value={problemForm.contest_id} onChange={(e) => setProblemForm({ ...problemForm, contest_id: e.target.value })} required>
                                <option value="">Select a contest</option>
                                {contests.map((c) => (
                                    <option key={c.id} value={c.id}>{c.title} (ID: {c.id})</option>
                                ))}
                            </select>
                        </div>

                        <div className="grid grid-cols-2 gap-4">
                            <div>
                                <label className={labelCls}>Problem Title</label>
                                <input type="text" className={inputCls} placeholder="Two Sum"
                                    value={problemForm.title} onChange={(e) => setProblemForm({ ...problemForm, title: e.target.value })} required />
                            </div>
                            <div className="grid grid-cols-3 gap-2">
                                <div>
                                    <label className={labelCls}>Points</label>
                                    <input type="number" className={inputCls} value={problemForm.points}
                                        onChange={(e) => setProblemForm({ ...problemForm, points: parseInt(e.target.value) })} />
                                </div>
                                <div>
                                    <label className={labelCls}>Time (s)</label>
                                    <input type="number" step="0.5" className={inputCls} value={problemForm.time_limit}
                                        onChange={(e) => setProblemForm({ ...problemForm, time_limit: parseFloat(e.target.value) })} />
                                </div>
                                <div>
                                    <label className={labelCls}>Memory (MB)</label>
                                    <input type="number" className={inputCls} value={problemForm.memory_limit}
                                        onChange={(e) => setProblemForm({ ...problemForm, memory_limit: parseInt(e.target.value) })} />
                                </div>
                            </div>
                        </div>

                        <div>
                            <label className={labelCls}>Description</label>
                            <textarea className={inputCls + " min-h-[100px] resize-y"} placeholder="Given two integers..."
                                value={problemForm.description} onChange={(e) => setProblemForm({ ...problemForm, description: e.target.value })} required />
                        </div>

                        <div className="grid grid-cols-2 gap-4">
                            <div>
                                <label className={labelCls}>Input Format</label>
                                <textarea className={inputCls + " min-h-[60px] resize-y"} placeholder="Two space-separated integers..."
                                    value={problemForm.input_format} onChange={(e) => setProblemForm({ ...problemForm, input_format: e.target.value })} />
                            </div>
                            <div>
                                <label className={labelCls}>Output Format</label>
                                <textarea className={inputCls + " min-h-[60px] resize-y"} placeholder="A single integer..."
                                    value={problemForm.output_format} onChange={(e) => setProblemForm({ ...problemForm, output_format: e.target.value })} />
                            </div>
                        </div>

                        <div className="grid grid-cols-2 gap-4">
                            <div>
                                <label className={labelCls}>Sample Input</label>
                                <textarea className={inputCls + " min-h-[60px] resize-y font-mono text-xs"} placeholder="3 5"
                                    value={problemForm.sample_input} onChange={(e) => setProblemForm({ ...problemForm, sample_input: e.target.value })} />
                            </div>
                            <div>
                                <label className={labelCls}>Sample Output</label>
                                <textarea className={inputCls + " min-h-[60px] resize-y font-mono text-xs"} placeholder="8"
                                    value={problemForm.sample_output} onChange={(e) => setProblemForm({ ...problemForm, sample_output: e.target.value })} />
                            </div>
                        </div>

                        {/* Test Cases */}
                        <div>
                            <div className="flex items-center justify-between mb-2">
                                <label className={labelCls + " mb-0"}>Hidden Test Cases</label>
                                <button type="button" onClick={addTestCase}
                                    className="cursor-pointer rounded-md bg-arena-surface-2 px-3 py-1 text-xs text-arena-accent transition-colors hover:bg-arena-border">
                                    + Add Test Case
                                </button>
                            </div>
                            <div className="space-y-3">
                                {problemForm.test_cases.map((tc, idx) => (
                                    <div key={idx} className="rounded-lg border border-arena-border bg-arena-surface-2 p-3">
                                        <div className="flex items-center justify-between mb-2">
                                            <span className="text-xs font-medium text-arena-text-muted">Test Case #{idx + 1}</span>
                                            <div className="flex items-center gap-3">
                                                <label className="flex items-center gap-1.5 cursor-pointer">
                                                    <input type="checkbox" className="accent-arena-primary cursor-pointer"
                                                        checked={tc.is_sample} onChange={(e) => updateTestCase(idx, 'is_sample', e.target.checked)} />
                                                    <span className="text-xs text-arena-text-muted">Sample</span>
                                                </label>
                                                {problemForm.test_cases.length > 1 && (
                                                    <button type="button" onClick={() => removeTestCase(idx)}
                                                        className="cursor-pointer text-xs text-arena-danger hover:underline bg-transparent">✕</button>
                                                )}
                                            </div>
                                        </div>
                                        <div className="grid grid-cols-2 gap-2">
                                            <textarea className={inputCls + " min-h-[50px] resize-y font-mono text-xs"} placeholder="Input..."
                                                value={tc.input_data} onChange={(e) => updateTestCase(idx, 'input_data', e.target.value)} />
                                            <textarea className={inputCls + " min-h-[50px] resize-y font-mono text-xs"} placeholder="Expected output..."
                                                value={tc.expected_output} onChange={(e) => updateTestCase(idx, 'expected_output', e.target.value)} />
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>

                        <button type="submit"
                            className="cursor-pointer rounded-lg bg-arena-primary px-6 py-2.5 font-medium text-white transition-all hover:bg-arena-primary/80">
                            Create Problem
                        </button>
                    </form>
                </div>
            )}
        </div>
    );
}

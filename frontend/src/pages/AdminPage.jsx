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

    const inputCls = "input-field w-full text-sm";
    const labelCls = "mb-2 block text-xs font-semibold tracking-wide uppercase text-arena-text-muted";

    return (
        <div className="mx-auto max-w-5xl px-4 py-12 sm:px-6 animate-fade-in">
            <h1 className="mb-2 text-4xl font-bold tracking-tight text-arena-text">Workspace</h1>
            <p className="mb-10 text-arena-text-muted text-lg">Manage contests, problems, and technical settings</p>

            {message.text && (
                <div className={`mb-8 rounded-md px-4 py-3 text-sm font-medium ${message.type === 'success'
                    ? 'bg-arena-success/10 border border-arena-success/20 text-arena-success'
                    : 'bg-arena-danger/10 border border-arena-danger/20 text-arena-danger'
                    }`}>
                    {message.text}
                </div>
            )}

            {/* Tabs */}
            <div className="mb-8 flex gap-2">
                {[
                    { id: 'contests', label: 'Contests Setup' },
                    { id: 'problems', label: 'Problem Editor' }
                ].map((tab) => (
                    <button
                        key={tab.id}
                        onClick={() => setActiveTab(tab.id)}
                        className={`cursor-pointer px-5 py-2 text-sm font-medium tracking-wide transition-colors rounded-md ${activeTab === tab.id
                                ? 'bg-arena-surface border border-arena-border text-arena-text shadow-sm'
                                : 'bg-transparent border border-transparent text-arena-text-muted hover:text-arena-text hover:bg-arena-surface-hover'
                            }`}
                    >
                        {tab.label}
                    </button>
                ))}
            </div>

            {/* Contests Tab */}
            {activeTab === 'contests' && (
                <div className="space-y-10">
                    {/* Create Form */}
                    <div className="rounded-lg border border-arena-border bg-arena-surface p-8">
                        <h2 className="mb-6 text-xl tracking-tight font-semibold text-arena-text border-b border-arena-border pb-4">Create New Contest</h2>
                        <form onSubmit={handleCreateContest} className="space-y-6">
                            <div>
                                <label className={labelCls}>Contest Title</label>
                                <input type="text" className={inputCls} placeholder="Weekly Contest #1"
                                    value={contestForm.title} onChange={(e) => setContestForm({ ...contestForm, title: e.target.value })} required />
                            </div>
                            <div>
                                <label className={labelCls}>Description</label>
                                <textarea className={inputCls + " min-h-[100px] resize-y"} placeholder="Contest description..."
                                    value={contestForm.description} onChange={(e) => setContestForm({ ...contestForm, description: e.target.value })} />
                            </div>
                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
                                <div>
                                    <label className={labelCls}>Start Time</label>
                                    <input type="datetime-local" className={inputCls} style={{ colorScheme: 'dark' }}
                                        value={contestForm.start_time} onChange={(e) => setContestForm({ ...contestForm, start_time: e.target.value })} required />
                                </div>
                                <div>
                                    <label className={labelCls}>End Time</label>
                                    <input type="datetime-local" className={inputCls} style={{ colorScheme: 'dark' }}
                                        value={contestForm.end_time} onChange={(e) => setContestForm({ ...contestForm, end_time: e.target.value })} required />
                                </div>
                            </div>
                            <div className="flex items-center gap-3 pt-2">
                                <label className="relative flex items-center cursor-pointer">
                                    <input type="checkbox" className="sr-only peer"
                                        checked={contestForm.is_published} onChange={(e) => setContestForm({ ...contestForm, is_published: e.target.checked })} />
                                    <div className="w-9 h-5 bg-arena-bg border border-arena-border peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-arena-text-muted after:border-arena-border after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-arena-primary peer-checked:after:bg-white"></div>
                                    <span className="ml-3 text-sm font-medium text-arena-text-muted">Publish Immediately</span>
                                </label>
                            </div>
                            <div className="pt-4 flex justify-end">
                                <button type="submit" className="btn-primary px-8 py-2.5 text-sm uppercase tracking-wide">
                                    Finalize Creation
                                </button>
                            </div>
                        </form>
                    </div>

                    {/* Contest List */}
                    <div>
                        <h2 className="mb-4 text-xl tracking-tight font-semibold text-arena-text px-2">Existing Contests</h2>
                        {contests.length === 0 ? (
                            <div className="text-center py-10 text-sm text-arena-text-muted border border-arena-border border-dashed rounded-lg">No contests deployed yet.</div>
                        ) : (
                            <div className="space-y-4">
                                {contests.map((c) => (
                                    <div key={c.id} className="group flex flex-col sm:flex-row items-start sm:items-center justify-between rounded-lg border border-arena-border bg-arena-surface p-5 py-4 transition-colors hover:border-arena-primary/30 hover:bg-arena-surface-hover">
                                        <div className="mb-4 sm:mb-0">
                                            <h3 className="font-medium tracking-tight text-arena-text text-base mb-1">{c.title}</h3>
                                            <div className="flex flex-wrap items-center gap-3 text-xs text-arena-text-muted font-mono">
                                                <span>ID:{c.id}</span>
                                                <span className="w-1 h-1 rounded-full bg-arena-border"></span>
                                                <span className={c.status === 'active' ? 'text-arena-success' : ''}>{c.status}</span>
                                                <span className="w-1 h-1 rounded-full bg-arena-border"></span>
                                                <span>{c.participant_count} users</span>
                                            </div>
                                        </div>
                                        <button onClick={() => handleDeleteContest(c.id)}
                                            className="cursor-pointer rounded-md bg-arena-danger/10 border border-arena-danger/20 px-4 py-2 text-xs font-semibold uppercase tracking-wide text-arena-danger transition-colors hover:bg-arena-danger hover:text-white">
                                            Revoke
                                        </button>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                </div>
            )}

            {/* Problems Tab */}
            {activeTab === 'problems' && (
                <div className="rounded-lg border border-arena-border bg-arena-surface p-8">
                    <h2 className="mb-6 text-xl tracking-tight font-semibold text-arena-text border-b border-arena-border pb-4">Deploy New Challenge</h2>
                    <form onSubmit={handleCreateProblem} className="space-y-6">
                        <div>
                            <label className={labelCls}>Target Contest</label>
                            <select className={inputCls}
                                value={problemForm.contest_id} onChange={(e) => setProblemForm({ ...problemForm, contest_id: e.target.value })} required>
                                <option value="">Select a contest environment...</option>
                                {contests.map((c) => (
                                    <option key={c.id} value={c.id}>{c.title} (ID: {c.id})</option>
                                ))}
                            </select>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            <div>
                                <label className={labelCls}>Problem Title</label>
                                <input type="text" className={inputCls} placeholder="e.g. Reverse Linked List"
                                    value={problemForm.title} onChange={(e) => setProblemForm({ ...problemForm, title: e.target.value })} required />
                            </div>
                            <div className="grid grid-cols-3 gap-4">
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
                                    <label className={labelCls}>Mem (MB)</label>
                                    <input type="number" className={inputCls} value={problemForm.memory_limit}
                                        onChange={(e) => setProblemForm({ ...problemForm, memory_limit: parseInt(e.target.value) })} />
                                </div>
                            </div>
                        </div>

                        <div>
                            <label className={labelCls}>Problem Statement</label>
                            <textarea className={inputCls + " min-h-[140px] resize-y"} placeholder="Clearly define the challenge..."
                                value={problemForm.description} onChange={(e) => setProblemForm({ ...problemForm, description: e.target.value })} required />
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            <div>
                                <label className={labelCls}>Input Format</label>
                                <textarea className={inputCls + " min-h-[80px] resize-y"} placeholder="e.g. First line contains N..."
                                    value={problemForm.input_format} onChange={(e) => setProblemForm({ ...problemForm, input_format: e.target.value })} />
                            </div>
                            <div>
                                <label className={labelCls}>Output Format</label>
                                <textarea className={inputCls + " min-h-[80px] resize-y"} placeholder="e.g. Print exactly one integer..."
                                    value={problemForm.output_format} onChange={(e) => setProblemForm({ ...problemForm, output_format: e.target.value })} />
                            </div>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pb-6 border-b border-arena-border">
                            <div>
                                <label className={labelCls}>Sample Input (Public)</label>
                                <textarea className={inputCls + " min-h-[100px] resize-y font-mono text-sm tracking-wide bg-arena-bg"} placeholder="Sample data to display..."
                                    value={problemForm.sample_input} onChange={(e) => setProblemForm({ ...problemForm, sample_input: e.target.value })} />
                            </div>
                            <div>
                                <label className={labelCls}>Sample Output (Public)</label>
                                <textarea className={inputCls + " min-h-[100px] resize-y font-mono text-sm tracking-wide bg-arena-bg"} placeholder="Corresponding result..."
                                    value={problemForm.sample_output} onChange={(e) => setProblemForm({ ...problemForm, sample_output: e.target.value })} />
                            </div>
                        </div>

                        {/* Test Cases Evaluator Section */}
                        <div className="pt-2">
                            <div className="flex items-center justify-between mb-4">
                                <div>
                                    <label className={labelCls + " !mb-1"}>Evaluation Suite</label>
                                    <p className="text-xs text-arena-text-muted">Define exhaustive test conditions for the judge</p>
                                </div>
                                <button type="button" onClick={addTestCase}
                                    className="cursor-pointer rounded-md border border-arena-border bg-arena-bg px-4 py-2 text-xs font-semibold uppercase tracking-wide text-arena-text transition-colors hover:border-arena-primary/50">
                                    + Add Case
                                </button>
                            </div>
                            <div className="space-y-4">
                                {problemForm.test_cases.map((tc, idx) => (
                                    <div key={idx} className="rounded-lg border border-arena-border/60 bg-arena-bg p-4 relative group">
                                        <div className="flex items-center justify-between mb-3 pb-3 border-b border-arena-border/40">
                                            <span className="text-xs font-bold font-mono text-arena-primary uppercase tracking-widest">Case {String(idx + 1).padStart(2, '0')}</span>
                                            <div className="flex items-center gap-4">
                                                <label className="flex items-center gap-2 cursor-pointer">
                                                    <input type="checkbox" className="accent-arena-primary cursor-pointer h-3 w-3"
                                                        checked={tc.is_sample} onChange={(e) => updateTestCase(idx, 'is_sample', e.target.checked)} />
                                                    <span className="text-xs font-medium text-arena-text-muted uppercase tracking-wide">Public</span>
                                                </label>
                                                {problemForm.test_cases.length > 1 && (
                                                    <button type="button" onClick={() => removeTestCase(idx)}
                                                        className="cursor-pointer rounded bg-arena-danger/10 p-1 text-arena-danger opacity-0 transition-opacity group-hover:opacity-100 hover:bg-arena-danger hover:text-white"
                                                        title="Remove Test Case">
                                                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>
                                                    </button>
                                                )}
                                            </div>
                                        </div>
                                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                                            <div>
                                                <div className="text-[10px] uppercase font-semibold text-arena-text-muted mb-1 ml-1">Condition Data</div>
                                                <textarea className={inputCls + " min-h-[80px] resize-y font-mono text-xs border-arena-border/50 focus:border-arena-primary"} placeholder="Input..."
                                                    value={tc.input_data} onChange={(e) => updateTestCase(idx, 'input_data', e.target.value)} />
                                            </div>
                                            <div>
                                                <div className="text-[10px] uppercase font-semibold text-arena-text-muted mb-1 ml-1">Expected Match</div>
                                                <textarea className={inputCls + " min-h-[80px] resize-y font-mono text-xs border-arena-border/50 focus:border-arena-primary"} placeholder="Result..."
                                                    value={tc.expected_output} onChange={(e) => updateTestCase(idx, 'expected_output', e.target.value)} />
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>

                        <div className="pt-8 flex justify-end gap-4 border-t border-arena-border">
                            <button type="submit"
                                className="btn-primary px-8 py-3 text-sm font-semibold uppercase tracking-widest shadow-lg shadow-arena-primary/20">
                                Deploy Challenge
                            </button>
                        </div>
                    </form>
                </div>
            )}
        </div>
    );
}

import { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { contestsAPI, problemsAPI, leaderboardAPI } from '../api/client';
import { useAuth } from '../context/AuthContext';
import ContestTimer from '../components/ContestTimer';

export default function ContestDetailPage() {
    const { id } = useParams();
    const navigate = useNavigate();
    const { isAuthenticated, user } = useAuth();

    const [contest, setContest] = useState(null);
    const [problems, setProblems] = useState([]);
    const [leaderboard, setLeaderboard] = useState([]);
    const [isJoined, setIsJoined] = useState(false);
    const [activeTab, setActiveTab] = useState('problems');
    const [loading, setLoading] = useState(true);
    const [joining, setJoining] = useState(false);
    const [error, setError] = useState('');

    useEffect(() => {
        const fetchData = async () => {
            try {
                const [contestRes, problemsRes, leaderboardRes] = await Promise.all([
                    contestsAPI.get(id),
                    problemsAPI.listForContest(id),
                    leaderboardAPI.get(id),
                ]);
                setContest(contestRes.data.contest);
                setProblems(problemsRes.data.problems);
                setLeaderboard(leaderboardRes.data.leaderboard);

                // Check if user joined
                if (isAuthenticated) {
                    try {
                        const statusRes = await contestsAPI.status(id);
                        setIsJoined(statusRes.data.is_joined);
                    } catch { }
                }
            } catch (err) {
                setError('Failed to load contest');
            } finally {
                setLoading(false);
            }
        };
        fetchData();
    }, [id, isAuthenticated]);

    const handleJoin = async () => {
        if (!isAuthenticated) {
            navigate('/login');
            return;
        }
        setJoining(true);
        try {
            await contestsAPI.join(id);
            setIsJoined(true);
        } catch (err) {
            setError(err.response?.data?.error || 'Failed to join');
        } finally {
            setJoining(false);
        }
    };

    // Refresh leaderboard periodically
    useEffect(() => {
        if (contest?.status !== 'active') return;
        const interval = setInterval(async () => {
            try {
                const res = await leaderboardAPI.get(id);
                setLeaderboard(res.data.leaderboard);
            } catch { }
        }, 15000);
        return () => clearInterval(interval);
    }, [id, contest?.status]);

    if (loading) {
        return (
            <div className="mx-auto max-w-5xl px-4 py-8 sm:px-6">
                <div className="skeleton h-10 w-64 mb-4" />
                <div className="skeleton h-6 w-96 mb-8" />
                <div className="skeleton h-80 w-full rounded-xl" />
            </div>
        );
    }

    if (!contest) {
        return (
            <div className="mx-auto max-w-5xl px-4 py-16 text-center">
                <h2 className="text-xl font-semibold">Contest not found</h2>
            </div>
        );
    }

    const tabs = [
        { key: 'problems', label: 'Problems', count: problems.length },
        { key: 'leaderboard', label: 'Leaderboard', count: leaderboard.length },
    ];

    return (
        <div className="mx-auto max-w-5xl px-4 py-12 sm:px-6 animate-fade-in">
            {/* Header */}
            <div className="mb-10 text-center sm:text-left">
                <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-6 mb-6">
                    <div>
                        <h1 className="mb-2 text-4xl font-bold tracking-tight text-arena-text">{contest.title}</h1>
                        <p className="text-arena-text-muted text-lg">{contest.description}</p>
                    </div>
                    <div className="flex-shrink-0 self-center sm:self-auto px-6 py-4 rounded-lg bg-arena-surface border border-arena-border">
                        <ContestTimer startTime={contest.start_time} endTime={contest.end_time} />
                    </div>
                </div>

                <div className="flex flex-wrap items-center justify-center sm:justify-start gap-6 border-b border-arena-border pb-6">
                    <span className="flex items-center gap-2 text-sm font-medium text-arena-text-muted">
                        <svg className="w-4 h-4 text-arena-primary hidden sm:block" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" /></svg>
                        {contest.participant_count} Enrolled Phase
                    </span>

                    {!isJoined && contest.status !== 'ended' && (
                        <button
                            onClick={handleJoin}
                            disabled={joining}
                            className="btn-primary px-6 py-2 text-sm disabled:opacity-50"
                        >
                            {joining ? 'Connecting...' : 'Join Contest'}
                        </button>
                    )}
                    {isJoined && (
                        <span className="flex items-center gap-2 rounded-md bg-arena-success/10 border border-arena-success/20 px-3 py-1.5 text-xs tracking-wide uppercase font-bold text-arena-success">
                            <span className="h-1.5 w-1.5 rounded-full bg-arena-success"></span> Registered
                        </span>
                    )}
                </div>
            </div>

            {error && (
                <div className="mb-6 rounded-md bg-arena-danger/10 border border-arena-danger/20 px-4 py-3 text-sm text-arena-danger">
                    {error}
                </div>
            )}

            {/* Tabs (Minimal segmented style) */}
            <div className="mb-8 flex gap-2">
                {tabs.map((tab) => (
                    <button
                        key={tab.key}
                        onClick={() => setActiveTab(tab.key)}
                        className={`cursor-pointer px-5 py-2 text-sm font-medium tracking-wide transition-colors rounded-md ${activeTab === tab.key
                                ? 'bg-arena-surface border border-arena-border text-arena-text shadow-sm'
                                : 'bg-transparent text-arena-text-muted hover:text-arena-text hover:bg-arena-surface-hover border border-transparent'
                            }`}
                    >
                        {tab.label}
                        <span className={`ml-2 rounded-md px-2 py-0.5 text-[10px] uppercase font-bold tracking-wider ${activeTab === tab.key ? 'bg-arena-bg text-arena-text-muted' : 'bg-arena-surface text-arena-text-muted'
                            }`}>
                            {tab.count}
                        </span>
                    </button>
                ))}
            </div>

            {/* Tab Content */}
            <div className="animate-fade-in">
                {activeTab === 'problems' && (
                    <div className="space-y-4">
                        {problems.length === 0 ? (
                            <div className="rounded-lg border border-arena-border bg-arena-surface py-20 text-center">
                                <h3 className="text-base font-semibold text-arena-text mb-2">Awaiting Release</h3>
                                <p className="text-sm text-arena-text-muted">Problems will be available when the contest starts.</p>
                            </div>
                        ) : (
                            problems.map((problem, idx) => (
                                <Link
                                    to={`/contests/${id}/problems/${problem.id}`}
                                    key={problem.id}
                                    className="group flex flex-col sm:flex-row items-start sm:items-center justify-between rounded-lg border border-arena-border bg-arena-surface p-5 py-4 no-underline transition-colors hover:border-arena-primary/50 hover:bg-arena-surface-hover"
                                >
                                    <div className="flex items-center gap-5">
                                        <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded bg-arena-bg border border-arena-border text-sm font-bold text-arena-primary font-mono group-hover:border-arena-primary/30 transition-colors">
                                            {String.fromCharCode(65 + idx)}
                                        </span>
                                        <div>
                                            <h3 className="font-semibold tracking-tight text-arena-text text-base mb-1 group-hover:text-arena-primary transition-colors">{problem.title}</h3>
                                            <span className="text-xs font-medium text-arena-text-muted flex gap-3">
                                                <span>⏱ {problem.time_limit}s</span>
                                                <span>💾 {problem.memory_limit}MB</span>
                                            </span>
                                        </div>
                                    </div>
                                    <div className="mt-4 sm:mt-0 flex items-center justify-between w-full sm:w-auto gap-4 pl-15 sm:pl-0">
                                        <span className="rounded-md bg-arena-bg border border-arena-border px-3 py-1 text-xs font-medium tracking-wide text-arena-primary">
                                            {problem.points} <span className="text-arena-text-muted">pts</span>
                                        </span>
                                        <svg className="w-5 h-5 text-arena-text-muted group-hover:text-arena-primary transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5l7 7-7 7" /></svg>
                                    </div>
                                </Link>
                            ))
                        )}
                    </div>
                )}

                {activeTab === 'leaderboard' && (
                    <div className="rounded-lg border border-arena-border bg-arena-surface overflow-hidden">
                        {leaderboard.length === 0 ? (
                            <div className="py-20 text-center">
                                <h3 className="text-base font-semibold text-arena-text mb-2">No Standings</h3>
                                <p className="text-sm text-arena-text-muted">Leaderboard will appear after the first submission.</p>
                            </div>
                        ) : (
                            <div className="overflow-x-auto">
                                <table className="w-full text-sm text-left whitespace-nowrap">
                                    <thead className="text-xs text-arena-text-muted uppercase tracking-widest bg-arena-bg border-b border-arena-border font-semibold">
                                        <tr>
                                            <th className="px-6 py-4 w-20 text-center">Rank</th>
                                            <th className="px-6 py-4">Participant</th>
                                            <th className="px-6 py-4 text-center">Solved</th>
                                            <th className="px-6 py-4 text-right">Score</th>
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-arena-border/50">
                                        {leaderboard.map((entry, idx) => (
                                            <tr
                                                key={entry.user_id}
                                                className={`transition-colors hover:bg-arena-bg ${entry.user_id === user?.id ? 'bg-arena-primary/5' : ''
                                                    }`}
                                            >
                                                <td className="px-6 py-4 text-center">
                                                    <span className={`inline-flex h-8 w-8 items-center justify-center rounded-md text-sm font-bold font-mono ${entry.rank === 1 ? 'bg-amber-400/10 text-amber-500 border border-amber-400/20' :
                                                            entry.rank === 2 ? 'bg-slate-300/10 text-slate-300 border border-slate-300/20' :
                                                                entry.rank === 3 ? 'bg-orange-400/10 text-orange-400 border border-orange-400/20' :
                                                                    'text-arena-text-muted bg-arena-bg border border-arena-border'
                                                        }`}>
                                                        {entry.rank}
                                                    </span>
                                                </td>
                                                <td className="px-6 py-4 font-medium text-arena-text flex items-center gap-2">
                                                    {entry.username}
                                                    {entry.user_id === user?.id && (
                                                        <span className="rounded bg-arena-primary/10 px-1.5 py-0.5 text-[10px] font-bold uppercase tracking-wider text-arena-primary">You</span>
                                                    )}
                                                </td>
                                                <td className="px-6 py-4 text-center font-mono text-arena-text-muted">
                                                    {entry.problems_solved}
                                                </td>
                                                <td className="px-6 py-4 text-right font-mono font-semibold text-arena-primary">
                                                    {entry.score}
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
}

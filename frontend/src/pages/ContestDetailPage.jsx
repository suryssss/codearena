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
        <div className="mx-auto max-w-5xl px-4 py-8 sm:px-6 animate-fade-in">
            {/* Header */}
            <div className="mb-8">
                <div className="flex items-start justify-between gap-4 mb-4">
                    <div>
                        <h1 className="mb-2 text-3xl font-bold">{contest.title}</h1>
                        <p className="text-arena-text-muted">{contest.description}</p>
                    </div>
                    <ContestTimer startTime={contest.start_time} endTime={contest.end_time} />
                </div>

                <div className="flex items-center gap-4">
                    <span className="text-sm text-arena-text-muted">
                        👥 {contest.participant_count} participants
                    </span>

                    {!isJoined && contest.status !== 'ended' && (
                        <button
                            onClick={handleJoin}
                            disabled={joining}
                            className="cursor-pointer rounded-lg bg-arena-accent px-5 py-2 text-sm font-semibold text-arena-bg transition-all hover:bg-arena-accent/80 hover:shadow-lg hover:shadow-arena-accent/20 disabled:opacity-50"
                        >
                            {joining ? 'Joining...' : 'Join Contest'}
                        </button>
                    )}
                    {isJoined && (
                        <span className="rounded-lg bg-arena-success/10 border border-arena-success/30 px-3 py-1.5 text-sm text-arena-success">
                            ✓ Joined
                        </span>
                    )}
                </div>
            </div>

            {error && (
                <div className="mb-6 rounded-lg bg-arena-danger/10 border border-arena-danger/20 px-4 py-3 text-sm text-arena-danger">
                    {error}
                </div>
            )}

            {/* Tabs */}
            <div className="mb-6 flex border-b border-arena-border">
                {tabs.map((tab) => (
                    <button
                        key={tab.key}
                        onClick={() => setActiveTab(tab.key)}
                        className={`cursor-pointer border-b-2 bg-transparent px-4 py-3 text-sm font-medium transition-colors ${activeTab === tab.key
                                ? 'border-arena-primary text-arena-primary-light'
                                : 'border-transparent text-arena-text-muted hover:text-arena-text'
                            }`}
                    >
                        {tab.label}
                        <span className="ml-2 rounded-full bg-arena-surface-2 px-2 py-0.5 text-xs">
                            {tab.count}
                        </span>
                    </button>
                ))}
            </div>

            {/* Tab Content */}
            {activeTab === 'problems' && (
                <div className="space-y-3">
                    {problems.length === 0 ? (
                        <div className="rounded-xl border border-arena-border bg-arena-surface py-16 text-center">
                            <p className="text-arena-text-muted">No problems available yet</p>
                        </div>
                    ) : (
                        problems.map((problem, idx) => (
                            <Link
                                to={`/contests/${id}/problems/${problem.id}`}
                                key={problem.id}
                                className="flex items-center justify-between rounded-xl border border-arena-border bg-arena-surface p-5 no-underline transition-all hover:border-arena-primary/40 hover:bg-arena-surface-2"
                            >
                                <div className="flex items-center gap-4">
                                    <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-arena-primary/10 text-sm font-bold text-arena-primary-light">
                                        {String.fromCharCode(65 + idx)}
                                    </span>
                                    <div>
                                        <h3 className="font-semibold text-arena-text">{problem.title}</h3>
                                        <span className="text-xs text-arena-text-muted">
                                            Time: {problem.time_limit}s · Memory: {problem.memory_limit}MB
                                        </span>
                                    </div>
                                </div>
                                <div className="flex items-center gap-3">
                                    <span className="rounded-full bg-arena-accent/10 px-3 py-1 text-xs font-medium text-arena-accent">
                                        {problem.points} pts
                                    </span>
                                    <span className="text-arena-text-muted">→</span>
                                </div>
                            </Link>
                        ))
                    )}
                </div>
            )}

            {activeTab === 'leaderboard' && (
                <div className="rounded-xl border border-arena-border bg-arena-surface overflow-hidden">
                    {leaderboard.length === 0 ? (
                        <div className="py-16 text-center text-arena-text-muted">
                            No participants yet
                        </div>
                    ) : (
                        <table className="w-full">
                            <thead>
                                <tr className="border-b border-arena-border bg-arena-surface-2">
                                    <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-arena-text-muted">Rank</th>
                                    <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-arena-text-muted">User</th>
                                    <th className="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wider text-arena-text-muted">Solved</th>
                                    <th className="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wider text-arena-text-muted">Score</th>
                                </tr>
                            </thead>
                            <tbody>
                                {leaderboard.map((entry, idx) => (
                                    <tr
                                        key={entry.user_id}
                                        className={`border-b border-arena-border/50 transition-colors hover:bg-arena-surface-2 ${entry.user_id === user?.id ? 'bg-arena-primary/5' : ''
                                            }`}
                                    >
                                        <td className="px-4 py-3">
                                            <span className={`inline-flex h-7 w-7 items-center justify-center rounded-full text-sm font-bold ${entry.rank === 1
                                                    ? 'bg-arena-warning/20 text-arena-warning'
                                                    : entry.rank === 2
                                                        ? 'bg-gray-400/20 text-gray-300'
                                                        : entry.rank === 3
                                                            ? 'bg-orange-400/20 text-orange-300'
                                                            : 'text-arena-text-muted'
                                                }`}>
                                                {entry.rank}
                                            </span>
                                        </td>
                                        <td className="px-4 py-3 font-medium">
                                            {entry.username}
                                            {entry.user_id === user?.id && (
                                                <span className="ml-2 text-xs text-arena-primary-light">(you)</span>
                                            )}
                                        </td>
                                        <td className="px-4 py-3 text-right text-arena-text-muted">
                                            {entry.problems_solved}
                                        </td>
                                        <td className="px-4 py-3 text-right font-mono font-semibold text-arena-accent">
                                            {entry.score}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    )}
                </div>
            )}
        </div>
    );
}

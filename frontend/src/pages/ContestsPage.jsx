import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { contestsAPI } from '../api/client';
import ContestTimer from '../components/ContestTimer';

export default function ContestsPage() {
    const [contests, setContests] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    useEffect(() => {
        const fetchContests = async () => {
            try {
                const res = await contestsAPI.list();
                setContests(res.data.contests);
            } catch (err) {
                setError('Failed to load contests');
            } finally {
                setLoading(false);
            }
        };
        fetchContests();
    }, []);

    const statusColors = {
        upcoming: 'border-arena-info/30 bg-arena-info/5',
        active: 'border-arena-success/30 bg-arena-success/5',
        ended: 'border-arena-border bg-arena-surface',
    };

    const statusLabels = {
        upcoming: { text: 'Upcoming', color: 'text-arena-info' },
        active: { text: '● Live', color: 'text-arena-success' },
        ended: { text: 'Ended', color: 'text-arena-text-muted' },
    };

    if (loading) {
        return (
            <div className="mx-auto max-w-5xl px-4 py-8 sm:px-6">
                <div className="mb-8">
                    <div className="skeleton h-8 w-48 mb-2" />
                    <div className="skeleton h-4 w-72" />
                </div>
                <div className="space-y-4">
                    {[1, 2, 3].map((i) => (
                        <div key={i} className="skeleton h-36 w-full rounded-xl" />
                    ))}
                </div>
            </div>
        );
    }

    return (
        <div className="mx-auto max-w-5xl px-4 py-8 sm:px-6">
            {/* Header */}
            <div className="mb-8 animate-fade-in">
                <h1 className="mb-2 text-3xl font-bold">Coding Contests</h1>
                <p className="text-arena-text-muted">
                    Join a contest, solve problems, and climb the leaderboard
                </p>
            </div>

            {error && (
                <div className="mb-6 rounded-lg bg-arena-danger/10 border border-arena-danger/20 px-4 py-3 text-sm text-arena-danger">
                    {error}
                </div>
            )}

            {/* Contests List */}
            {contests.length === 0 ? (
                <div className="flex flex-col items-center justify-center rounded-xl border border-arena-border bg-arena-surface py-20 text-center">
                    <span className="mb-4 text-4xl">🏟️</span>
                    <h3 className="mb-2 text-lg font-semibold">No contests yet</h3>
                    <p className="text-sm text-arena-text-muted">Check back later for upcoming contests</p>
                </div>
            ) : (
                <div className="space-y-4">
                    {contests.map((contest, idx) => (
                        <Link
                            to={`/contests/${contest.id}`}
                            key={contest.id}
                            className="block rounded-xl border bg-arena-surface p-6 no-underline transition-all hover:border-arena-primary/40 hover:bg-arena-surface-2 hover:shadow-lg hover:shadow-arena-primary/5 animate-fade-in"
                            style={{ animationDelay: `${idx * 0.05}s` }}
                        >
                            <div className="flex items-start justify-between gap-4">
                                <div className="flex-1">
                                    <div className="mb-2 flex items-center gap-3">
                                        <h2 className="text-xl font-semibold text-arena-text">{contest.title}</h2>
                                        <span className={`text-xs font-medium ${statusLabels[contest.status]?.color}`}>
                                            {statusLabels[contest.status]?.text}
                                        </span>
                                    </div>
                                    <p className="mb-4 text-sm text-arena-text-muted line-clamp-2">
                                        {contest.description || 'No description provided'}
                                    </p>
                                    <div className="flex flex-wrap items-center gap-4 text-xs text-arena-text-muted">
                                        <span>👥 {contest.participant_count} participants</span>
                                        <span>
                                            📅 {new Date(contest.start_time).toLocaleDateString('en-US', {
                                                month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit',
                                            })}
                                        </span>
                                    </div>
                                </div>

                                <div className="flex-shrink-0">
                                    <ContestTimer startTime={contest.start_time} endTime={contest.end_time} />
                                </div>
                            </div>
                        </Link>
                    ))}
                </div>
            )}
        </div>
    );
}

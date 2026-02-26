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
        <div className="mx-auto max-w-4xl px-4 py-12 sm:px-6">
            {/* Header */}
            <div className="mb-10 animate-fade-in border-b border-arena-border pb-6">
                <h1 className="mb-3 text-3xl font-bold tracking-tight text-arena-text">Contests</h1>
                <p className="text-arena-text-muted text-sm">
                    Enter the arena. Solve problems. See real-time rankings.
                </p>
            </div>

            {error && (
                <div className="mb-6 rounded-md bg-arena-danger/10 border border-arena-danger/20 px-4 py-3 text-sm text-arena-danger">
                    {error}
                </div>
            )}

            {/* Contests List */}
            {contests.length === 0 ? (
                <div className="flex flex-col items-center justify-center rounded-lg border border-arena-border bg-arena-surface py-24 text-center">
                    <h3 className="mb-2 text-base font-semibold text-arena-text">No active arenas</h3>
                    <p className="text-sm text-arena-text-muted">Check back later for upcoming contests.</p>
                </div>
            ) : (
                <div className="space-y-4">
                    {contests.map((contest, idx) => (
                        <Link
                            to={`/contests/${contest.id}`}
                            key={contest.id}
                            className={`block rounded-lg border bg-arena-surface p-6 no-underline transition-colors hover:bg-arena-surface-hover animate-fade-in ${contest.status === 'active'
                                    ? 'border-arena-primary/30 hover:border-arena-primary/50'
                                    : 'border-arena-border hover:border-arena-border/80'
                                }`}
                            style={{ animationDelay: `${idx * 0.05}s` }}
                        >
                            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-6">
                                <div className="flex-1">
                                    <div className="mb-3 flex items-center gap-4">
                                        <h2 className="text-lg font-semibold tracking-tight text-arena-text group-hover:text-arena-primary transition-colors">
                                            {contest.title}
                                        </h2>
                                        <span className={`text-[10px] uppercase font-bold tracking-widest px-2 py-0.5 rounded-sm ${contest.status === 'active' ? 'bg-arena-primary/10 text-arena-primary' :
                                                contest.status === 'upcoming' ? 'bg-arena-info/10 text-arena-info' :
                                                    'bg-arena-surface-hover text-arena-text-muted'
                                            }`}>
                                            {contest.status}
                                        </span>
                                    </div>
                                    <p className="mb-5 text-sm text-arena-text-muted line-clamp-2 leading-relaxed">
                                        {contest.description || 'No description provided.'}
                                    </p>
                                    <div className="flex flex-wrap items-center gap-6 text-xs font-medium text-arena-text-muted">
                                        <span className="flex items-center gap-2">
                                            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" /></svg>
                                            {contest.participant_count} enrolled
                                        </span>
                                        <span className="flex items-center gap-2">
                                            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg>
                                            {new Date(contest.start_time).toLocaleDateString('en-US', {
                                                month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit',
                                            })}
                                        </span>
                                    </div>
                                </div>

                                <div className="flex-shrink-0 pt-4 sm:pt-0 sm:border-l sm:border-arena-border sm:pl-6">
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

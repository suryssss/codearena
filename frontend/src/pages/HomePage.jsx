import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function HomePage() {
    const { isAuthenticated } = useAuth();

    return (
        <div className="relative min-h-[calc(100vh-64px)] flex flex-col items-center justify-center overflow-hidden">
            {/*Background glow */}
            <div className="pointer-events-none absolute inset-0 overflow-hidden">
                <div className="absolute left-1/2 top-0 h-[500px] w-[800px] -translate-x-1/2 -translate-y-1/2 rounded-full bg-arena-primary/10 opacity-50 blur-[120px]" />
            </div>

            {/* Hero Section */}
            <div className="relative z-10 mx-auto max-w-4xl px-6 py-20 text-center flex flex-col items-center">
                <div className="animate-fade-in flex flex-col items-center">
                    <div className="mb-8 inline-flex items-center gap-2 rounded-full bg-arena-surface border border-arena-border px-4 py-1.5 text-xs font-medium text-arena-text-muted transition-colors hover:border-arena-primary/50 cursor-default">
                        <span className="h-2 w-2 rounded-full bg-arena-primary animate-slowPulse" />
                        CodeArena Environment Online
                    </div>

                    <h1 className="mb-6 text-5xl font-bold tracking-tight text-arena-text sm:text-7xl">
                        Uninterrupted Focus.
                        <br />
                        <span className="text-arena-text-muted">Uncompromising Speed.</span>
                    </h1>

                    <p className="mx-auto mb-12 max-w-2xl text-lg text-arena-text-muted leading-relaxed">
                        A premium competitive coding environment engineered for optimal performance.
                        Sub-second auto-judging, live leaderboards, and a zero-distraction editor.
                    </p>

                    <div className="flex flex-col sm:flex-row items-center justify-center gap-4 w-full sm:w-auto">
                        <Link
                            to={isAuthenticated ? '/contests' : '/register'}
                            className="btn-primary px-8 py-3 text-sm flex w-full sm:w-auto justify-center no-underline"
                        >
                            {isAuthenticated ? 'Browse Contests' : 'Start Coding'}
                        </Link>
                        <Link
                            to="/contests"
                            className="rounded-md border border-arena-border bg-arena-surface px-8 py-3 text-sm font-medium text-arena-text transition-colors hover:bg-arena-surface-hover w-full sm:w-auto flex justify-center no-underline"
                        >
                            View Leaderboards
                        </Link>
                    </div>
                </div>

                {/*  Features Grid */}
                <div className="mt-32 w-full grid gap-4 sm:grid-cols-3 animate-fade-in-delay text-left">
                    {[
                        {
                            title: 'Zero Latency Judging',
                            desc: 'Redis-backed queue execution pipeline delivering results in milliseconds.',
                        },
                        {
                            title: 'Data-Driven Rankings',
                            desc: 'Live analytical leaderboards updating instantly without layout shifts.',
                        },
                        {
                            title: 'Immersive Environment',
                            desc: 'Dark-mode-first Monaco editor designed to eliminate ocular fatigue.',
                        },
                    ].map((feature, idx) => (
                        <div
                            key={idx}
                            className="panel-card p-6 border-arena-border hover:border-arena-border/80 bg-transparent hover:bg-arena-surface transition-colors"
                        >
                            <h3 className="mb-2 text-sm font-semibold text-arena-text tracking-wide">{feature.title}</h3>
                            <p className="text-sm text-arena-text-muted leading-relaxed">{feature.desc}</p>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
}

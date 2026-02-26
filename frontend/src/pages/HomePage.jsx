import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function HomePage() {
    const { isAuthenticated } = useAuth();

    return (
        <div className="relative overflow-hidden">
            {/* Background effects */}
            <div className="pointer-events-none absolute inset-0">
                <div className="absolute left-1/4 top-20 h-96 w-96 rounded-full bg-arena-primary/5 blur-3xl" />
                <div className="absolute right-1/4 top-40 h-96 w-96 rounded-full bg-arena-accent/5 blur-3xl" />
            </div>

            {/* Hero */}
            <div className="relative mx-auto max-w-5xl px-4 py-24 sm:px-6 text-center">
                <div className="animate-fade-in">
                    <div className="mb-6 inline-flex items-center gap-2 rounded-full bg-arena-primary/10 border border-arena-primary/20 px-4 py-1.5 text-sm text-arena-primary-light">
                        <span className="h-2 w-2 animate-pulse rounded-full bg-arena-accent" />
                        Live coding contests
                    </div>

                    <h1 className="mb-6 text-5xl font-extrabold leading-tight sm:text-6xl">
                        Code. Compete.
                        <br />
                        <span className="bg-gradient-to-r from-arena-primary-light via-arena-accent to-arena-accent-light bg-clip-text text-transparent">
                            Conquer.
                        </span>
                    </h1>

                    <p className="mx-auto mb-10 max-w-2xl text-lg text-arena-text-muted leading-relaxed">
                        Real-time coding contests with auto-judging, live leaderboards, and instant feedback.
                        Submit your solutions, compete with peers, and sharpen your skills.
                    </p>

                    <div className="flex flex-wrap items-center justify-center gap-4">
                        <Link
                            to={isAuthenticated ? '/contests' : '/register'}
                            className="rounded-xl bg-arena-primary px-8 py-3.5 text-base font-semibold text-white transition-all hover:bg-arena-primary/80 hover:shadow-xl hover:shadow-arena-primary/20 hover:-translate-y-0.5 no-underline"
                        >
                            {isAuthenticated ? 'Browse Contests' : 'Get Started — Free'}
                        </Link>
                        <Link
                            to="/contests"
                            className="rounded-xl border border-arena-border bg-arena-surface px-8 py-3.5 text-base font-semibold text-arena-text transition-all hover:border-arena-border-light hover:bg-arena-surface-2 no-underline"
                        >
                            View Contests
                        </Link>
                    </div>
                </div>

                {/* Features */}
                <div className="mt-24 grid gap-6 sm:grid-cols-3 animate-fade-in-delay">
                    {[
                        {
                            icon: '⚡',
                            title: 'Auto-Judge',
                            desc: 'Submit code and get results in seconds with our sandboxed execution engine.',
                        },
                        {
                            icon: '🏆',
                            title: 'Live Leaderboard',
                            desc: 'Real-time rankings updated after every submission. See where you stand.',
                        },
                        {
                            icon: '🔒',
                            title: 'Secure Sandbox',
                            desc: 'Code executes in isolated Docker containers with strict resource limits.',
                        },
                    ].map((feature, idx) => (
                        <div
                            key={idx}
                            className="group rounded-xl border border-arena-border bg-arena-surface p-6 text-left transition-all hover:border-arena-primary/30 hover:bg-arena-surface-2"
                        >
                            <span className="mb-4 inline-flex h-12 w-12 items-center justify-center rounded-lg bg-arena-surface-2 text-2xl transition-transform group-hover:scale-110">
                                {feature.icon}
                            </span>
                            <h3 className="mb-2 text-lg font-semibold">{feature.title}</h3>
                            <p className="text-sm text-arena-text-muted">{feature.desc}</p>
                        </div>
                    ))}
                </div>

                {/* Stats */}
                <div className="mt-20 flex flex-wrap justify-center gap-12 animate-fade-in-delay">
                    {[
                        { value: 'Python', label: 'Language Support' },
                        { value: '< 5s', label: 'Avg Judge Time' },
                        { value: '100%', label: 'Sandboxed' },
                    ].map((stat, idx) => (
                        <div key={idx} className="text-center">
                            <p className="text-3xl font-bold bg-gradient-to-r from-arena-primary-light to-arena-accent bg-clip-text text-transparent">
                                {stat.value}
                            </p>
                            <p className="mt-1 text-sm text-arena-text-muted">{stat.label}</p>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
}

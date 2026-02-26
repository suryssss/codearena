import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function LoginPage() {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);
    const { login } = useAuth();
    const navigate = useNavigate();

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setLoading(true);
        try {
            await login(email, password);
            navigate('/contests');
        } catch (err) {
            setError(err.response?.data?.error || 'Login failed');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="flex min-h-[calc(100vh-64px)] items-center justify-center px-4 bg-arena-bg relative overflow-hidden">
            {/* Minimalist ambient background glow */}
            <div className="pointer-events-none absolute inset-0 overflow-hidden">
                <div className="absolute left-1/2 top-1/2 h-[400px] w-[600px] -translate-x-1/2 -translate-y-1/2 rounded-full bg-arena-primary/5 opacity-50 blur-[100px]" />
            </div>

            <div className="w-full max-w-sm animate-fade-in relative z-10">
                {/* Header */}
                <div className="mb-10 text-center">
                    <h1 className="mb-2 text-3xl font-bold tracking-tight text-arena-text">Welcome Back</h1>
                    <p className="text-sm font-medium text-arena-text-muted">Authenticate to continue</p>
                </div>

                {/* Form Card */}
                <div className="rounded-lg border border-arena-border bg-arena-surface p-8">
                    {error && (
                        <div className="mb-6 rounded-md bg-arena-danger/10 border border-arena-danger/20 px-4 py-3 text-sm text-arena-danger text-center font-medium">
                            {error}
                        </div>
                    )}

                    <form onSubmit={handleSubmit} className="space-y-6">
                        <div>
                            <label className="mb-2 block text-xs font-semibold tracking-wide uppercase text-arena-text-muted">Email</label>
                            <input
                                type="email"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                required
                                className="input-field w-full text-sm"
                                placeholder="developer@example.com"
                            />
                        </div>

                        <div>
                            <label className="mb-2 block text-xs font-semibold tracking-wide uppercase text-arena-text-muted">Password</label>
                            <input
                                type="password"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                required
                                className="input-field w-full text-sm tracking-widest font-mono"
                                placeholder="••••••••"
                            />
                        </div>

                        <button
                            type="submit"
                            disabled={loading}
                            className="btn-primary w-full py-2.5 text-sm uppercase tracking-wide disabled:opacity-50"
                        >
                            {loading ? (
                                <span className="inline-flex items-center gap-2">
                                    <span className="h-4 w-4 animate-spin rounded-full border-2 border-white/30 border-t-white" />
                                    Authenticating
                                </span>
                            ) : (
                                'Sign In'
                            )}
                        </button>
                    </form>

                    <div className="mt-8 text-center text-xs font-medium text-arena-text-muted">
                        New to CodeArena?{' '}
                        <Link to="/register" className="text-arena-primary hover:text-arena-primary-hover hover:underline underline-offset-4 transition-colors">
                            Create Account
                        </Link>
                    </div>
                </div>
            </div>
        </div>
    );
}

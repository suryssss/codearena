import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function RegisterPage() {
    const [username, setUsername] = useState('');
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);
    const { register } = useAuth();
    const navigate = useNavigate();

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');

        if (password !== confirmPassword) {
            setError('Passwords do not match');
            return;
        }
        if (password.length < 6) {
            setError('Password must be at least 6 characters');
            return;
        }

        setLoading(true);
        try {
            await register(username, email, password);
            navigate('/login');
        } catch (err) {
            setError(err.response?.data?.error || 'Registration failed');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="flex min-h-[calc(100vh-64px)] items-center justify-center px-4">
            <div className="w-full max-w-md animate-fade-in">
                <div className="mb-8 text-center">
                    <h1 className="mb-2 text-3xl font-bold">Create your account</h1>
                    <p className="text-arena-text-muted">Join CodeArena and start competing</p>
                </div>

                <div className="rounded-xl border border-arena-border bg-arena-surface p-6 shadow-xl shadow-black/20">
                    {error && (
                        <div className="mb-4 rounded-lg bg-arena-danger/10 border border-arena-danger/20 px-4 py-3 text-sm text-arena-danger">
                            {error}
                        </div>
                    )}

                    <form onSubmit={handleSubmit} className="space-y-4">
                        <div>
                            <label className="mb-1.5 block text-sm font-medium text-arena-text-muted">Username</label>
                            <input
                                type="text"
                                value={username}
                                onChange={(e) => setUsername(e.target.value)}
                                required
                                minLength={3}
                                className="w-full rounded-lg border border-arena-border bg-arena-surface-2 px-4 py-2.5 text-arena-text outline-none transition-colors placeholder:text-arena-text-muted/50 focus:border-arena-primary focus:ring-1 focus:ring-arena-primary"
                                placeholder="coderX"
                            />
                        </div>

                        <div>
                            <label className="mb-1.5 block text-sm font-medium text-arena-text-muted">Email</label>
                            <input
                                type="email"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                required
                                className="w-full rounded-lg border border-arena-border bg-arena-surface-2 px-4 py-2.5 text-arena-text outline-none transition-colors placeholder:text-arena-text-muted/50 focus:border-arena-primary focus:ring-1 focus:ring-arena-primary"
                                placeholder="you@example.com"
                            />
                        </div>

                        <div>
                            <label className="mb-1.5 block text-sm font-medium text-arena-text-muted">Password</label>
                            <input
                                type="password"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                required
                                minLength={6}
                                className="w-full rounded-lg border border-arena-border bg-arena-surface-2 px-4 py-2.5 text-arena-text outline-none transition-colors placeholder:text-arena-text-muted/50 focus:border-arena-primary focus:ring-1 focus:ring-arena-primary"
                                placeholder="••••••••"
                            />
                        </div>

                        <div>
                            <label className="mb-1.5 block text-sm font-medium text-arena-text-muted">Confirm Password</label>
                            <input
                                type="password"
                                value={confirmPassword}
                                onChange={(e) => setConfirmPassword(e.target.value)}
                                required
                                className="w-full rounded-lg border border-arena-border bg-arena-surface-2 px-4 py-2.5 text-arena-text outline-none transition-colors placeholder:text-arena-text-muted/50 focus:border-arena-primary focus:ring-1 focus:ring-arena-primary"
                                placeholder="••••••••"
                            />
                        </div>

                        <button
                            type="submit"
                            disabled={loading}
                            className="w-full cursor-pointer rounded-lg bg-arena-primary px-4 py-2.5 font-medium text-white transition-all hover:bg-arena-primary/80 hover:shadow-lg hover:shadow-arena-primary/20 disabled:cursor-not-allowed disabled:opacity-50"
                        >
                            {loading ? (
                                <span className="inline-flex items-center gap-2">
                                    <span className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
                                    Creating account...
                                </span>
                            ) : (
                                'Create account'
                            )}
                        </button>
                    </form>

                    <div className="mt-6 text-center text-sm text-arena-text-muted">
                        Already have an account?{' '}
                        <Link to="/login" className="text-arena-primary-light hover:underline no-underline">
                            Sign in
                        </Link>
                    </div>
                </div>
            </div>
        </div>
    );
}

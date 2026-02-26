import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function Navbar() {
    const { user, isAuthenticated, isAdmin, logout } = useAuth();
    const navigate = useNavigate();

    const handleLogout = () => {
        logout();
        navigate('/login');
    };

    return (
        <nav className="sticky top-0 z-50 border-b border-arena-border bg-arena-surface/80 backdrop-blur-xl">
            <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3 sm:px-6">
                {/* Logo */}
                <Link to="/" className="flex items-center gap-2 text-xl font-bold no-underline">
                    <span className="inline-flex h-8 w-8 items-center justify-center rounded-lg bg-arena-primary text-sm text-white">
                        {'</>'}
                    </span>
                    <span className="bg-gradient-to-r from-arena-primary-light to-arena-accent bg-clip-text text-transparent">
                        CodeArena
                    </span>
                </Link>

                {/* Navigation Links */}
                <div className="flex items-center gap-1">
                    <Link
                        to="/contests"
                        className="rounded-lg px-3 py-2 text-sm text-arena-text-muted transition-colors hover:bg-arena-surface-2 hover:text-arena-text no-underline"
                    >
                        Contests
                    </Link>

                    {isAuthenticated ? (
                        <>
                            {isAdmin && (
                                <Link
                                    to="/admin"
                                    className="rounded-lg px-3 py-2 text-sm text-arena-warning transition-colors hover:bg-arena-surface-2 no-underline"
                                >
                                    Admin
                                </Link>
                            )}

                            <div className="ml-2 flex items-center gap-3 rounded-lg border border-arena-border bg-arena-surface-2 px-3 py-1.5">
                                <span className="text-sm text-arena-text-muted">
                                    {user?.username}
                                </span>
                                <button
                                    onClick={handleLogout}
                                    className="cursor-pointer rounded-md bg-transparent px-2 py-1 text-xs text-arena-danger transition-colors hover:bg-arena-danger/10"
                                >
                                    Logout
                                </button>
                            </div>
                        </>
                    ) : (
                        <div className="flex items-center gap-2 ml-2">
                            <Link
                                to="/login"
                                className="rounded-lg px-4 py-2 text-sm text-arena-text-muted transition-colors hover:text-arena-text no-underline"
                            >
                                Login
                            </Link>
                            <Link
                                to="/register"
                                className="rounded-lg bg-arena-primary px-4 py-2 text-sm font-medium text-white transition-all hover:bg-arena-primary/80 hover:shadow-lg hover:shadow-arena-primary/20 no-underline"
                            >
                                Sign Up
                            </Link>
                        </div>
                    )}
                </div>
            </div>
        </nav>
    );
}

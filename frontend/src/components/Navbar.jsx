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
        <nav className="sticky top-0 z-50 border-b border-arena-border bg-arena-bg/90 backdrop-blur-md">
            <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
                {/* Logo */}
                <Link to="/" className="flex items-center gap-3 text-xl font-semibold no-underline text-arena-text group animate-fade-in-delay">
                    {/* Minimalist Logo Icon */}
                    <svg className="w-5 h-5 text-arena-primary group-hover:text-arena-primary-hover transition-colors duration-200" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <polyline points="16 18 22 12 16 6"></polyline>
                        <polyline points="8 6 2 12 8 18"></polyline>
                    </svg>
                    <span className="tracking-tight text-arena-text">CodeArena</span>
                </Link>

                {/* Navigation Links */}
                <div className="flex items-center gap-1 animate-fade-in-delay-2">
                    <Link
                        to="/contests"
                        className="rounded-md px-3 py-1.5 text-sm font-medium text-arena-text-muted transition-colors hover:bg-arena-surface-hover hover:text-arena-text no-underline"
                    >
                        Contests
                    </Link>

                    {isAuthenticated ? (
                        <div className="flex items-center ml-2">
                            {isAdmin && (
                                <Link
                                    to="/admin"
                                    className="rounded-md px-3 py-1.5 text-sm font-medium text-arena-warning transition-colors hover:bg-arena-surface-hover no-underline mr-4"
                                >
                                    Admin
                                </Link>
                            )}

                            <div className="border-l border-arena-border pl-4 flex items-center gap-4">
                                <span className="text-sm font-medium text-arena-text-muted">
                                    {user?.username}
                                </span>
                                <button
                                    onClick={handleLogout}
                                    className="cursor-pointer rounded-md bg-transparent px-3 py-1.5 text-xs text-arena-danger/80 transition-colors hover:bg-arena-danger/10 hover:text-arena-danger font-medium"
                                >
                                    Logout
                                </button>
                            </div>
                        </div>
                    ) : (
                        <div className="flex items-center gap-3 ml-4 border-l border-arena-border pl-4">
                            <Link
                                to="/login"
                                className="rounded-md px-3 py-1.5 text-sm font-medium text-arena-text-muted transition-colors hover:text-arena-text hover:bg-arena-surface-hover no-underline"
                            >
                                Login
                            </Link>
                            <Link
                                to="/register"
                                className="btn-primary px-4 py-1.5 text-sm no-underline"
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

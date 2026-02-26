const statusConfig = {
    pending: { label: 'Pending', color: 'bg-arena-text-muted/10 text-arena-text-muted' },
    running: { label: 'Running', color: 'bg-arena-info/10 text-arena-info' },
    accepted: { label: 'Accepted', color: 'bg-arena-success/10 text-arena-success' },
    wrong_answer: { label: 'Wrong Answer', color: 'bg-arena-danger/10 text-arena-danger' },
    runtime_error: { label: 'Runtime Error', color: 'bg-arena-danger/10 text-arena-danger' },
    time_limit_exceeded: { label: 'TLE', color: 'bg-arena-warning/10 text-arena-warning' },
    memory_limit_exceeded: { label: 'MLE', color: 'bg-arena-warning/10 text-arena-warning' },
    compilation_error: { label: 'CE', color: 'bg-arena-danger/10 text-arena-danger' },
};

export default function StatusBadge({ status }) {
    const config = statusConfig[status] || statusConfig.pending;

    return (
        <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium tracking-wide ${config.color}`}>
            {status === 'running' && (
                <span className="mr-1.5 h-1.5 w-1.5 animate-pulse rounded-full bg-current" />
            )}
            {config.label}
        </span>
    );
}

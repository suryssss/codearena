import { useState, useEffect } from 'react';

export default function ContestTimer({ startTime, endTime }) {
    const [timeLeft, setTimeLeft] = useState('');
    const [status, setStatus] = useState('');

    useEffect(() => {
        const update = () => {
            const now = new Date();
            const start = new Date(startTime);
            const end = new Date(endTime);

            if (now < start) {
                setStatus('upcoming');
                setTimeLeft(formatDuration(start - now));
            } else if (now > end) {
                setStatus('ended');
                setTimeLeft('Contest ended');
            } else {
                setStatus('active');
                setTimeLeft(formatDuration(end - now));
            }
        };

        update();
        const interval = setInterval(update, 1000);
        return () => clearInterval(interval);
    }, [startTime, endTime]);

    const formatDuration = (ms) => {
        const totalSeconds = Math.floor(ms / 1000);
        const hours = Math.floor(totalSeconds / 3600);
        const minutes = Math.floor((totalSeconds % 3600) / 60);
        const seconds = totalSeconds % 60;

        const parts = [];
        if (hours > 0) parts.push(`${hours}h`);
        parts.push(`${String(minutes).padStart(2, '0')}m`);
        parts.push(`${String(seconds).padStart(2, '0')}s`);
        return parts.join(' ');
    };

    const colors = {
        upcoming: 'text-arena-info border-arena-info/30 bg-arena-info/10',
        active: 'text-arena-success border-arena-success/30 bg-arena-success/10',
        ended: 'text-arena-text-muted border-arena-border bg-arena-surface-2',
    };

    const labels = {
        upcoming: 'Starts in',
        active: 'Time left',
        ended: '',
    };

    return (
        <div className={`inline-flex items-center gap-2 rounded-lg border px-3 py-1.5 text-sm font-mono ${colors[status]}`}>
            {labels[status] && (
                <span className="text-xs opacity-70">{labels[status]}</span>
            )}
            <span className="font-semibold">{timeLeft}</span>
        </div>
    );
}

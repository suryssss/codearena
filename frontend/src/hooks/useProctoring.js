import { useEffect, useRef, useState, useCallback } from 'react';
import api from '../api/client';

/**
 * useProctoring — Manages proctored mode enforcement
 * 
 * Features:
 * - Force fullscreen during contest
 * - Detect tab switches (visibilitychange)
 * - Detect window blur
 * - Block copy/paste and right-click
 * - Log violations to backend
 * - Track local violation count
 */
export function useProctoring(contestId, enabled = true) {
    const [violations, setViolations] = useState(0);
    const [isFlagged, setIsFlagged] = useState(false);
    const [isFullscreen, setIsFullscreen] = useState(false);
    const violationCountRef = useRef(0);
    const enabledRef = useRef(enabled);

    useEffect(() => {
        enabledRef.current = enabled;
    }, [enabled]);

    const logViolation = useCallback(async (type, details = '') => {
        if (!enabledRef.current || !contestId) return;

        violationCountRef.current += 1;
        setViolations(violationCountRef.current);

        try {
            const res = await api.post('/proctoring/violation', {
                contest_id: contestId,
                violation_type: type,
                details,
            });
            if (res.data.total_violations >= 5) {
                setIsFlagged(true);
            }
        } catch (err) {
            console.error('[Proctor] Failed to log violation:', err);
        }
    }, [contestId]);

    // Request fullscreen
    const enterFullscreen = useCallback(() => {
        const el = document.documentElement;
        if (el.requestFullscreen) {
            el.requestFullscreen().catch(() => { });
        } else if (el.webkitRequestFullscreen) {
            el.webkitRequestFullscreen();
        } else if (el.msRequestFullscreen) {
            el.msRequestFullscreen();
        }
    }, []);

    useEffect(() => {
        if (!enabled || !contestId) return;

        // ── Tab switch detection ────────────────────────
        const handleVisibility = () => {
            if (document.hidden) {
                logViolation('tab_switch', 'User switched to another tab');
            }
        };

        // ── Window blur detection ──────────────────────
        const handleBlur = () => {
            logViolation('window_blur', 'Window lost focus');
        };

        // ── Copy/paste prevention ──────────────────────
        const handleCopy = (e) => {
            e.preventDefault();
            logViolation('copy_paste', 'Copy attempt blocked');
        };
        const handlePaste = (e) => {
            // Allow paste in the code editor only
            const target = e.target;
            if (target.closest('.monaco-editor')) return;
            e.preventDefault();
            logViolation('copy_paste', 'Paste attempt blocked');
        };

        // ── Right-click prevention ─────────────────────
        const handleContextMenu = (e) => {
            e.preventDefault();
            logViolation('right_click', 'Right-click attempt blocked');
        };

        // ── Fullscreen exit detection ──────────────────
        const handleFullscreenChange = () => {
            const isFS = !!document.fullscreenElement;
            setIsFullscreen(isFS);
            if (!isFS && enabledRef.current) {
                logViolation('fullscreen_exit', 'Exited fullscreen mode');
                // Re-request fullscreen after a short delay
                setTimeout(() => {
                    if (enabledRef.current) enterFullscreen();
                }, 1000);
            }
        };

        // Register listeners
        document.addEventListener('visibilitychange', handleVisibility);
        window.addEventListener('blur', handleBlur);
        document.addEventListener('copy', handleCopy);
        document.addEventListener('paste', handlePaste);
        document.addEventListener('contextmenu', handleContextMenu);
        document.addEventListener('fullscreenchange', handleFullscreenChange);

        // Enter fullscreen on mount
        enterFullscreen();

        // Fetch current violation status
        api.get(`/proctoring/status/${contestId}`)
            .then(res => {
                violationCountRef.current = res.data.violation_count;
                setViolations(res.data.violation_count);
                setIsFlagged(res.data.is_flagged);
            })
            .catch(() => { });

        return () => {
            document.removeEventListener('visibilitychange', handleVisibility);
            window.removeEventListener('blur', handleBlur);
            document.removeEventListener('copy', handleCopy);
            document.removeEventListener('paste', handlePaste);
            document.removeEventListener('contextmenu', handleContextMenu);
            document.removeEventListener('fullscreenchange', handleFullscreenChange);

            // Exit fullscreen on cleanup
            if (document.fullscreenElement) {
                document.exitFullscreen().catch(() => { });
            }
        };
    }, [enabled, contestId, logViolation, enterFullscreen]);

    return {
        violations,
        isFlagged,
        isFullscreen,
        enterFullscreen,
    };
}

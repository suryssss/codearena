import { createContext, useContext, useEffect, useRef, useState, useCallback } from 'react';
import { io } from 'socket.io-client';

const SocketContext = createContext(null);

export function SocketProvider({ children }) {
    const socketRef = useRef(null);
    const [isConnected, setIsConnected] = useState(false);
    const [contestRoom, setContestRoom] = useState(null);

    useEffect(() => {
        // Connect to SocketIO server
        const socket = io('/', {
            transports: ['websocket', 'polling'],
            autoConnect: true,
        });

        socket.on('connect', () => {
            console.log('[Socket] Connected:', socket.id);
            setIsConnected(true);
        });

        socket.on('disconnect', () => {
            console.log('[Socket] Disconnected');
            setIsConnected(false);
        });

        socket.on('connect_error', (err) => {
            console.log('[Socket] Connection error:', err.message);
        });

        socketRef.current = socket;

        return () => {
            socket.disconnect();
        };
    }, []);

    const joinContest = useCallback((contestId) => {
        if (socketRef.current && contestId) {
            socketRef.current.emit('join_contest', { contest_id: contestId });
            setContestRoom(contestId);
        }
    }, []);

    const leaveContest = useCallback((contestId) => {
        if (socketRef.current && contestId) {
            socketRef.current.emit('leave_contest', { contest_id: contestId });
            setContestRoom(null);
        }
    }, []);

    const onEvent = useCallback((event, handler) => {
        if (socketRef.current) {
            socketRef.current.on(event, handler);
            return () => socketRef.current?.off(event, handler);
        }
        return () => { };
    }, []);

    const value = {
        socket: socketRef.current,
        isConnected,
        contestRoom,
        joinContest,
        leaveContest,
        onEvent,
    };

    return (
        <SocketContext.Provider value={value}>
            {children}
        </SocketContext.Provider>
    );
}

export function useSocket() {
    const ctx = useContext(SocketContext);
    if (!ctx) throw new Error('useSocket must be used within SocketProvider');
    return ctx;
}

"""
SocketIO event handlers for CodeArena.

Events emitted by the server:
  - submission_result: When a submission finishes judging
  - leaderboard_update: When leaderboard data changes
  - contest_timer_update: Periodic contest timer sync
  - rank_change: When a user's rank changes after submission

Events received from client:
  - join_contest: Client joins a contest room for real-time updates
  - leave_contest: Client leaves a contest room
"""

from flask_socketio import emit, join_room, leave_room
from flask import request
from app.extensions import socketio


@socketio.on("connect")
def handle_connect():
    """Handle client connection."""
    print(f"[SocketIO] Client connected: {request.sid}")


@socketio.on("disconnect")
def handle_disconnect():
    """Handle client disconnection."""
    print(f"[SocketIO] Client disconnected: {request.sid}")


@socketio.on("join_contest")
def handle_join_contest(data):
    """Client joins a contest room for real-time updates."""
    contest_id = data.get("contest_id")
    if contest_id:
        room = f"contest_{contest_id}"
        join_room(room)
        print(f"[SocketIO] Client {request.sid} joined room {room}")
        emit("joined", {"contest_id": contest_id, "message": "Connected to contest feed"})


@socketio.on("leave_contest")
def handle_leave_contest(data):
    """Client leaves a contest room."""
    contest_id = data.get("contest_id")
    if contest_id:
        room = f"contest_{contest_id}"
        leave_room(room)
        print(f"[SocketIO] Client {request.sid} left room {room}")


def emit_submission_result(contest_id: int, submission_data: dict):
    """Emit submission result to the specific user and contest room."""
    socketio.emit(
        "submission_result",
        submission_data,
        room=f"contest_{contest_id}",
    )


def emit_leaderboard_update(contest_id: int, leaderboard_data: list):
    """Emit leaderboard update to all clients in the contest room."""
    socketio.emit(
        "leaderboard_update",
        {"contest_id": contest_id, "leaderboard": leaderboard_data},
        room=f"contest_{contest_id}",
    )


def emit_rank_change(contest_id: int, user_id: int, old_rank: int, new_rank: int, username: str):
    """Emit rank change event."""
    socketio.emit(
        "rank_change",
        {
            "contest_id": contest_id,
            "user_id": user_id,
            "username": username,
            "old_rank": old_rank,
            "new_rank": new_rank,
        },
        room=f"contest_{contest_id}",
    )

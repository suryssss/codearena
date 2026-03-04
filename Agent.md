1. Product Requirements Document (PRD)
   Objective

Build a competitive programming contest platform similar to LeetCode / Codeforces.

It must support:

1000 concurrent users

real-time code execution

multiple testcases (100+ hidden)

protected contest environment

real-time leaderboard

admin contest management

Core Features
User Features
Authentication

Two roles:

User

register/login

join contest

view problems

run code

submit solution

see submission history

leaderboard

Admin

create contest

create problems

upload testcases

view submissions

manage users

Contest Mode

Contest includes:

time window (start/end)

list of problems

scoring rules

leaderboard

Rules:

fullscreen required

minimize >3 times → ban

copy/paste disabled

devtools detection

Code Editor

Inside browser.

Features:

syntax highlighting

multi-language

run code

submit code

input/output preview

Recommended:

Monaco Editor (VSCode editor)

Judge System

Must support:

multiple languages

multiple testcases

hidden testcases

time limit

memory limit

Result types:

Accepted
Wrong Answer
Runtime Error
Compilation Error
Time Limit Exceeded
Memory Limit Exceeded 2. High Level System Architecture

Think of this as 4 layers.

Users
│
CDN
│
Next.js Frontend
│
API Gateway
│
Flask Backend
│
Redis Queue
│
Judge Workers (Docker)
│
Database
Architecture Diagram
┌───────────────┐
│ Next.js UI │
└──────┬────────┘
│
│ HTTP API
│
┌───────▼────────┐
│ Flask Backend │
└───────┬────────┘
│
┌──────────┼─────────────┐
│ │ │
▼ ▼ ▼
Redis PostgreSQL Object Storage
(Queue) (DB) (Testcases)

        │
        ▼

┌───────────────┐
│ Judge Workers │
│ (Docker) │
└───────────────┘ 3. Tech Stack (Corrected)

Your stack is mostly correct.

Frontend

Next.js
Tailwind
Monaco Editor
WebSocket

Backend

Python Flask
Gunicorn
Celery (task queue)

Queue

Redis

Database

PostgreSQL

Execution

Docker sandbox

Infra

NGINX
Docker
AWS / GCP 4. Backend Services

You should split backend logically.

1️⃣ API Service

Flask

Handles:

login
contest APIs
problem APIs
submission APIs
leaderboard
2️⃣ Judge Queue

When user submits code:

User Submit
↓
Store submission
↓
Push job → Redis Queue
3️⃣ Judge Worker

Worker pulls job from queue.

Steps:

1 compile code
2 run inside docker
3 execute testcases
4 calculate score
5 store result 5. Code Execution Pipeline

This is the core system.

Flow:

User Submit Code
│
▼
API saves submission
│
▼
Push job → Redis Queue
│
▼
Judge Worker picks job
│
▼
Create Docker Container
│
▼
Compile Code
│
▼
Run against Testcases
│
▼
Store Result
Docker Execution

Example:

docker run --rm \
--memory=256m \
--cpus=0.5 \
-v code:/app \
judge-python

Limits:

CPU limit
Memory limit
Timeout
Example Python Runner

Worker executes:

python solution.py < input.txt

Capture:

stdout
stderr
exit code 6. Database Design

Use PostgreSQL.

Users
users

---

id
name
email
password
role
created_at
Contests
contests

---

id
title
start_time
end_time
duration
created_by
Problems
problems

---

id
title
description
difficulty
time_limit
memory_limit
Testcases
testcases

---

id
problem_id
input
expected_output
is_hidden
Submissions
submissions

---

id
user_id
problem_id
code
language
status
runtime
memory
created_at
Leaderboard

Can be computed or stored.

## leaderboard

contest_id
user_id
score
rank 7. Redis Usage

Redis is critical.

Use it for:

1 Job Queue

Submission queue.

submit → push job
worker → pop job

Use:

Celery + Redis
2 Leaderboard Cache

Leaderboard updates frequently.

Cache:

contest_leaderboard
3 Rate limiting

Prevent spam submissions.

Example:

max 10 submissions / minute 8. Real-time Leaderboard

Use WebSockets.

Flow:

submission result
↓
update leaderboard
↓
publish event
↓
websocket pushes update 9. Fullscreen Protection System

Frontend JS:

Detect:

visibilitychange
fullscreenchange
blur
focus

Example:

document.addEventListener("visibilitychange", () => {})

If user exits fullscreen:

warning_count += 1

If:

warning_count >= 3

Call API:

POST /contest/ban 10. Editor Integration

Use Monaco Editor.

Features:

syntax highlight
multi-language
auto indent
themes

Languages:

Python
C++
Java
JavaScript 11. Code Run Feature

Two modes:

Run

Runs sample testcases only.

Submit

Runs all hidden testcases.

12. Scaling for 1000 Users

Critical mistake beginners make:

Running code in API server

Never do that.

Use workers.

Horizontal Scaling
Frontend instances: 2
Backend instances: 3
Judge workers: 10+
Redis: 1
Postgres: 1

Example:

1000 users
200 concurrent submissions
10 workers

Each worker:

~20 submissions/min 13. Docker Judge Architecture

Each language has its own container.

Example:

judge-python
judge-cpp
judge-java

Example Dockerfile

FROM python:3.10-slim

WORKDIR /app

COPY runner.py .

CMD ["python","runner.py"] 14. Security (Critical)

Running user code is dangerous.

Must restrict:

filesystem
network
memory
cpu
processes

Use:

Docker seccomp
read-only filesystem
no network

Example:

--network none
--read-only
--pids-limit 64 15. File Storage

Store testcases in:

S3 / MinIO

Structure:

problem_id/
input1.txt
output1.txt 16. Deployment Architecture
NGINX
│
Next.js
│
Flask API
│
Redis
│
Postgres
│
Judge Workers 17. MVP Scope (DO NOT OVERBUILD)

Your first version should include:

login
contest page
problem page
monaco editor
submit code
judge worker
testcase evaluation
leaderboard

Skip initially:

anti-cheat
multi language
realtime leaderboard
plagiarism detection

You’re trying to build too much too early.

18. Suggested Project Structure

Backend

backend
├── app
│ ├── routes
│ ├── models
│ ├── services
│ └── utils
├── judge
│ ├── worker.py
│ ├── runner.py
│ └── docker
└── celery.py

Frontend

frontend
├── pages
├── components
├── editor
├── contest
└── leaderboard

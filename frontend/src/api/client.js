import axios from 'axios';

const api = axios.create({
    baseURL: '/api',
    headers: { 'Content-Type': 'application/json' },
});

// Attach JWT token to every request
api.interceptors.request.use((config) => {
    const token = localStorage.getItem('token');
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

// Handle 401, 422, and 429 (rate limited) globally
api.interceptors.response.use(
    (response) => response,
    (error) => {
        const status = error.response?.status;

        // Auth errors
        const isAuthError = status === 401 ||
            (status === 422 && error.response?.data?.msg && error.response.data.msg.includes('Signature'));

        if (isAuthError) {
            localStorage.removeItem('token');
            localStorage.removeItem('user');
            if (!window.location.pathname.includes('/login') && !window.location.pathname.includes('/register')) {
                window.location.href = '/login';
            }
        }

        // Rate limit error — show a user-friendly message
        if (status === 429) {
            const retryAfter = error.response?.headers?.['retry-after'] || '60';
            error.friendlyMessage = `Too many requests. Please wait ${retryAfter}s before trying again.`;
        }

        return Promise.reject(error);
    }
);

// Auth

export const authAPI = {
    register: (data) => api.post('/auth/register', data),
    login: (data) => api.post('/auth/login', data),
    getProfile: () => api.get('/auth/me'),
};

//Contests

export const contestsAPI = {
    list: () => api.get('/contests'),
    get: (id) => api.get(`/contests/${id}`),
    create: (data) => api.post('/contests', data),
    update: (id, data) => api.put(`/contests/${id}`, data),
    delete: (id) => api.delete(`/contests/${id}`),
    join: (id) => api.post(`/contests/${id}/join`),
    status: (id) => api.get(`/contests/${id}/status`),
};

//Problems

export const problemsAPI = {
    listForContest: (contestId) => api.get(`/problems/contest/${contestId}`),
    get: (id) => api.get(`/problems/${id}`),
    create: (data) => api.post('/problems', data),
    update: (id, data) => api.put(`/problems/${id}`, data),
    delete: (id) => api.delete(`/problems/${id}`),
    addTestCase: (problemId, data) => api.post(`/problems/${problemId}/test-cases`, data),
    deleteTestCase: (id) => api.delete(`/problems/test-cases/${id}`),
};

//  Submissions

export const submissionsAPI = {
    // SUBMIT mode
    create: (data) => api.post('/submissions', data),
    // RUN mode (async — returns job_id, results arrive via SocketIO)
    run: (data) => api.post('/submissions/run', data),
    // RUN mode polling fallback
    getRunResult: (jobId) => api.get(`/submissions/run/${jobId}`),
    get: (id) => api.get(`/submissions/${id}`),
    my: (contestId) => api.get('/submissions/my', { params: { contest_id: contestId } }),
    forProblem: (problemId) => api.get(`/submissions/problem/${problemId}`),
    // Admin: replay a submission
    replay: (id) => api.post(`/submissions/${id}/replay`),
};

// Leaderboard 
export const leaderboardAPI = {
    get: (contestId) => api.get(`/leaderboard/${contestId}`),
    percentile: (contestId) => api.get(`/leaderboard/${contestId}/percentile`),
};

// Proctoring

export const proctoringAPI = {
    logViolation: (data) => api.post('/proctoring/violation', data),
    getViolations: (contestId) => api.get(`/proctoring/violations/${contestId}`),
    getFlagged: (contestId) => api.get(`/proctoring/flagged/${contestId}`),
    getStatus: (contestId) => api.get(`/proctoring/status/${contestId}`),
};

export default api;

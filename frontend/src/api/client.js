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

// Handle 401 globally
api.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response?.status === 401) {
            localStorage.removeItem('token');
            localStorage.removeItem('user');
            // Only redirect if not already on login/register
            if (!window.location.pathname.includes('/login') && !window.location.pathname.includes('/register')) {
                window.location.href = '/login';
            }
        }
        return Promise.reject(error);
    }
);

// ── Auth ──────────────────────────────────────────────────────────

export const authAPI = {
    register: (data) => api.post('/auth/register', data),
    login: (data) => api.post('/auth/login', data),
    getProfile: () => api.get('/auth/me'),
};

// ── Contests ──────────────────────────────────────────────────────

export const contestsAPI = {
    list: () => api.get('/contests'),
    get: (id) => api.get(`/contests/${id}`),
    create: (data) => api.post('/contests', data),
    update: (id, data) => api.put(`/contests/${id}`, data),
    delete: (id) => api.delete(`/contests/${id}`),
    join: (id) => api.post(`/contests/${id}/join`),
    status: (id) => api.get(`/contests/${id}/status`),
};

// ── Problems ──────────────────────────────────────────────────────

export const problemsAPI = {
    listForContest: (contestId) => api.get(`/problems/contest/${contestId}`),
    get: (id) => api.get(`/problems/${id}`),
    create: (data) => api.post('/problems', data),
    update: (id, data) => api.put(`/problems/${id}`, data),
    delete: (id) => api.delete(`/problems/${id}`),
    addTestCase: (problemId, data) => api.post(`/problems/${problemId}/test-cases`, data),
    deleteTestCase: (id) => api.delete(`/problems/test-cases/${id}`),
};

// ── Submissions ───────────────────────────────────────────────────

export const submissionsAPI = {
    create: (data) => api.post('/submissions', data),
    get: (id) => api.get(`/submissions/${id}`),
    my: (contestId) => api.get('/submissions/my', { params: { contest_id: contestId } }),
    forProblem: (problemId) => api.get(`/submissions/problem/${problemId}`),
};

// ── Leaderboard ───────────────────────────────────────────────────

export const leaderboardAPI = {
    get: (contestId) => api.get(`/leaderboard/${contestId}`),
};

export default api;

const API_BASE_URL = 'https://humble-orbit-4449q57jpqc77px-8080.app.github.dev'; // Replace with your backend URL

let currentUserId = '';

export const setUserId = (id) => {
    currentUserId = id;
};

const getHeaders = () => {
    const headers = {
        'Content-Type': 'application/json',
    };
    if (currentUserId) {
        headers['user_id'] = currentUserId;
    }
    return headers;
};

export const createSession = async () => {
    console.log(currentUserId);
    const response = await fetch(`${API_BASE_URL}/sessions`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'creator_id': currentUserId,
        },
    });
    return response.json();
};

export const joinSession = async (sessionId) => {
    const response = await fetch(`${API_BASE_URL}/sessions/${sessionId}/join`, {
        method: 'POST',
        headers: getHeaders(),
    });
    return response.json();
};

export const fetchMovies = async () => {
    const response = await fetch(`${API_BASE_URL}/movies`, {
        headers: getHeaders(),
    });
    return response.json();
};

export const startSession = async (sessionId) => {
    const response = await fetch(`${API_BASE_URL}/sessions/${sessionId}/start`, {
        method: 'POST',
        headers: getHeaders(),
    });
    return response.json();
};

export const getParticipants = async (sessionId) => {
    const response = await fetch(`${API_BASE_URL}/sessions/${sessionId}/participants`, {
        headers: getHeaders(),
    });
    if (!response.ok) {
        throw new Error('Failed to fetch participants');
    }
    return response.json();
};
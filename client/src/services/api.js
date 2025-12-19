const API_BASE_URL = 'http://your-backend-url.com/api'; // Replace with your backend URL

export const createSession = async () => {
    const response = await fetch(`${API_BASE_URL}/sessions`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
    });
    return response.json();
};

export const joinSession = async (sessionId) => {
    const response = await fetch(`${API_BASE_URL}/sessions/${sessionId}/join`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
    });
    return response.json();
};

export const fetchMovies = async () => {
    const response = await fetch(`${API_BASE_URL}/movies`);
    return response.json();
};

export const startSession = async (sessionId) => {
    const response = await fetch(`${API_BASE_URL}/sessions/${sessionId}/start`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
    });
    return response.json();
};

export const getParticipants = async (sessionId) => {
    const response = await fetch(`${API_BASE_URL}/sessions/${sessionId}/participants`);
    if (!response.ok) {
        throw new Error('Failed to fetch participants');
    }
    return response.json();
};
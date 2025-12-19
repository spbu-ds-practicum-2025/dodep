const API_BASE_URL = ''; // Relative path for same-origin

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
    const response = await fetch(`${API_BASE_URL}/sessions/create`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ creator_id: currentUserId }),
    });
    const data = await response.json();
    return data.session_code;
};

export const joinSession = async (sessionId) => {
    const response = await fetch(`${API_BASE_URL}/sessions/join`, {
        method: 'POST',
        headers: getHeaders(),
        body: JSON.stringify({ session_code: sessionId, user_id: currentUserId }),
    });
    return response.json();
};

export const fetchMovies = async (sessionId) => {
    const response = await fetch(`${API_BASE_URL}/movies?session=${sessionId}`, {
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

export const getSession = async (sessionId) => {
    const response = await fetch(`${API_BASE_URL}/sessions/${sessionId}`, {
        headers: getHeaders(),
    });
    if (!response.ok) {
        throw new Error('Failed to fetch session');
    }
    return response.json();
};

export const getParticipants = async (sessionId) => {
    const data = await getSession(sessionId);
    return data.participants;
};

export const sendSwipe = async (sessionId, movieId, direction, participants) => {
    const swipeValue = direction === 'right' ? 'want_now' : 'skip';
    const response = await fetch(`${API_BASE_URL}/swipe`, {
        method: 'POST',
        headers: getHeaders(),
        body: JSON.stringify({
            session_id: sessionId,
            user_id: currentUserId,
            movie_id: movieId,
            swipe_value: swipeValue,
            participants: participants
        }),
    });
    return response.json();
};

export const continueSession = async (sessionId) => {
    const response = await fetch(`${API_BASE_URL}/sessions/${sessionId}/continue`, {
        method: 'POST',
        headers: getHeaders(),
    });
    return response.json();
};

export const endSession = async (sessionId) => {
    const response = await fetch(`${API_BASE_URL}/sessions/${sessionId}/end`, {
        method: 'POST',
        headers: getHeaders(),
    });
    return response.json();
};
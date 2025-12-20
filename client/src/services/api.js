const API_BASE_URL = ''; // Relative path for same-origin

let currentUserId = localStorage.getItem('user_id') || '';

export const setUserId = (id) => {
    currentUserId = id;
    localStorage.setItem('user_id', id);
};

const ensureUserId = () => {
    if (!currentUserId) {
        currentUserId = `User_${Math.floor(Math.random() * 10000)}`;
        localStorage.setItem('user_id', currentUserId);
    }
    return currentUserId;
};

const getHeaders = () => {
    const headers = {
        'Content-Type': 'application/json',
        'user_id': ensureUserId()
    };
    return headers;
};

export const createSession = async () => {
    ensureUserId();
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
    ensureUserId();
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
    console.log(getHeaders());
    const response = await fetch(`${API_BASE_URL}/sessions/${sessionId}`, {
        method: 'POST',
        headers: getHeaders(),
        user_id: currentUserId,
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

export const updateCurrentMovie = async (sessionId, movieId) => {
    const response = await fetch(`${API_BASE_URL}/sessions/${sessionId}/movie`, {
        method: 'PUT',
        headers: getHeaders(),
        body: JSON.stringify({ current_movie_id: movieId }),
    });
    return response.json();
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
    // Call Match Service to handle continue logic (get next movie + update session)
    const response = await fetch(`${API_BASE_URL}/matches/${sessionId}/continue`, {
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

export const notifyVote = async (sessionId, movieId) => {
    await fetch(`${API_BASE_URL}/sessions/${sessionId}/vote`, {
        method: 'POST',
        headers: getHeaders(),
        body: JSON.stringify({ user_id: currentUserId, movie_id: movieId }),
    });
};
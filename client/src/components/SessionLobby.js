import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { createSession, joinSession, getParticipants, startSession, getSession } from '../services/api';

const SessionLobby = ({ onSessionStart }) => {
    const [sessionId, setSessionId] = useState('');
    const [inputSessionId, setInputSessionId] = useState(''); // Для поля ввода
    const [participants, setParticipants] = useState([]);
    const [isCreator, setIsCreator] = useState(false);
    const navigate = useNavigate();

    const handleCreateSession = async () => {
        try {
            const newSessionId = await createSession();
            setSessionId(newSessionId);
            setIsCreator(true);
        } catch (error) {
            console.error("Error creating session:", error);
        }
    };

    const handleJoinSession = async () => {
        if (inputSessionId) {
            try {
                await joinSession(inputSessionId);
                setSessionId(inputSessionId);
            } catch (error) {
                console.error("Error joining session:", error);
            }
        }
    };

    const checkSessionStatus = async () => {
        if (!sessionId) return;
        try {
            const session = await getSession(sessionId);
            setParticipants(session.participants || []);
            
            if (session.status === 'active' && !isCreator) {
                 if (onSessionStart) {
                    onSessionStart({ sessionId, isCreator, participants: session.participants });
                }
                navigate('/swipe');
            }
        } catch (error) {
            console.error("Error checking session status:", error);
        }
    };

    useEffect(() => {
        if (!sessionId) return;

        checkSessionStatus();
        const interval = setInterval(checkSessionStatus, 2000);
        return () => clearInterval(interval);
    }, [sessionId, isCreator]); // Added isCreator to dependencies

    const handleStartSession = async () => {
        try {
            await startSession(sessionId);
            if (onSessionStart) {
                onSessionStart({ sessionId, isCreator, participants });
            }
            // Переход на страницу свайпов
            navigate('/swipe');
        } catch (error) {
            console.error("Error starting session:", error);
        }
    };

    // ВАЖНО: Компонент должен возвращать JSX
    return (
        <div className="lobby-container">
            <h1>Выбор фильма</h1>
            
            {!sessionId ? (
                <div className="join-controls">
                    <button onClick={handleCreateSession}>Создать новую сессию</button>
                    <div className="divider"></div>
                    <input 
                        type="text" 
                        placeholder="ID сессии" 
                        value={inputSessionId}
                        onChange={(e) => setInputSessionId(e.target.value)}
                    />
                    <button onClick={handleJoinSession}>Присоединиться</button>
                </div>
            ) : (
                <div className="session-info">
                    <h2>ID Сессии: {sessionId}</h2>
                    <h3>Участники:</h3>
                    <ul>
                        {participants.map((p, index) => (
                            <li key={index}>{p.name || p}</li> 
                        ))}
                    </ul>
                    
                    {isCreator ? (
                        <button className="start-btn" onClick={handleStartSession}>
                            Начать выбор фильмов
                        </button>
                    ) : (
                        <p>Ожидание начала организатором...</p>
                    )}
                </div>
            )}
        </div>
    );
};

export default SessionLobby;
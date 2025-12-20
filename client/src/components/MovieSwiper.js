import React, { useState, useEffect } from 'react';
import { fetchMovies, sendSwipe, getSession, continueSession, endSession, notifyVote, updateCurrentMovie } from '../services/api';
import { useNavigate } from 'react-router-dom';
import MatchModal from './MatchModal';

const MovieSwiper = ({ sessionData }) => {
    const [movies, setMovies] = useState([]);
    const [currentMovie, setCurrentMovie] = useState(null);
    const [loading, setLoading] = useState(true);
    const [waiting, setWaiting] = useState(false);
    const [matchedMovie, setMatchedMovie] = useState(null);
    const [showMatchModal, setShowMatchModal] = useState(false);
    const navigate = useNavigate();

    // Load movies
    useEffect(() => {
        const loadMovies = async () => {
            try {
                const movieList = await fetchMovies(sessionData?.sessionId);
                setMovies(movieList || []);
                if (movieList && movieList.length > 0) {
                    // Default to first movie if no current_movie_id yet
                    setCurrentMovie(movieList[0]);
                    
                    // Initialize session current movie if not set
                    const session = await getSession(sessionData.sessionId);
                    if (!session.current_movie_id) {
                        await updateCurrentMovie(sessionData.sessionId, movieList[0].id);
                    }
                }
            } catch (error) {
                console.error("Failed to load movies", error);
            } finally {
                setLoading(false);
            }
        };

        if (sessionData?.sessionId) {
            loadMovies();
        }
    }, [sessionData]);

    // Poll session status
    useEffect(() => {
        if (!sessionData?.sessionId || movies.length === 0) return;

        const pollSession = async () => {
            try {
                const session = await getSession(sessionData.sessionId);
                
                if (session.match_movie_id) {
                    // Use loose comparison (==) to handle potential string/number mismatch
                    const matchedMovie = movies.find(m => m.id == session.match_movie_id);
                    if (matchedMovie) {
                        setMatchedMovie(matchedMovie);
                        setShowMatchModal(true);
                    }
                } else {
                    // If match was cleared (by creator continuing), hide modal
                    if (showMatchModal) {
                        setShowMatchModal(false);
                        setMatchedMovie(null);
                    }
                }

                if (session.status === 'abandoned') {
                    navigate('/');
                    return;
                }

                if (session.current_movie_id) {
                    const movie = movies.find(m => m.id == session.current_movie_id);
                    if (movie) {
                        if (currentMovie && movie.id !== currentMovie.id) {
                            // Movie changed, stop waiting
                            setWaiting(false);
                            setCurrentMovie(movie);
                        } else if (!currentMovie) {
                            setCurrentMovie(movie);
                        }
                    }
                }
            } catch (error) {
                console.error("Error polling session:", error);
            }
        };

        const interval = setInterval(pollSession, 2000);
        return () => clearInterval(interval);
    }, [sessionData, movies, currentMovie, showMatchModal, navigate]);

    const handleSwipe = async (direction) => {
        if (!currentMovie || waiting) return;

        try {
            setWaiting(true); // Optimistic waiting
            const response = await sendSwipe(
                sessionData.sessionId,
                currentMovie.id,
                direction,
                sessionData.participants
            );
            
            await notifyVote(sessionData.sessionId, currentMovie.id);

            console.log("Swipe response:", response);

            if (response.status === 'match_found') {
                setMatchedMovie(currentMovie);
                setShowMatchModal(true);
            } else if (response.status === 'next_movie') {
                // Wait for poll to update movie
                setWaiting(true);
            } else if (response.status === 'vote_recorded') {
                setWaiting(true);
            } else {
                setWaiting(false); // Error or unknown
            }

        } catch (error) {
            console.error("Error sending swipe:", error);
            setWaiting(false);
        }
    };

    const handleContinue = async () => {
        try {
            await continueSession(sessionData.sessionId);
            setShowMatchModal(false);
            setMatchedMovie(null);
        } catch (error) {
            console.error("Error continuing session:", error);
        }
    };

    const handleEndSession = async () => {
        try {
            await endSession(sessionData.sessionId);
            navigate('/');
        } catch (error) {
            console.error("Error ending session:", error);
        }
    };

    if (loading) return <div>Loading movies...</div>;
    if (movies.length === 0) return <div>No movies found for this session.</div>;
    if (!currentMovie) return <div>Initializing...</div>;

    return (
        <div className="swiper-container">
            {showMatchModal && (
                <MatchModal 
                    movie={matchedMovie} 
                    isCreator={sessionData?.isCreator}
                    onContinue={handleContinue}
                    onEndSession={handleEndSession}
                />
            )}

            <div className="movie-card">
                {/* {currentMovie.poster_url && (
                    <img src={currentMovie.poster_url} alt={currentMovie.title} className="movie-poster" />
                )} */}
                <h2>{currentMovie.title}</h2>
                <p>{currentMovie.description}</p>
                <p>Rating: {currentMovie.rating}</p>
                <p>Genre: {currentMovie.genre}</p>
                <p>Duration: {currentMovie.duration_minutes} min</p>
            </div>

            {waiting ? (
                <div className="waiting-message">
                    <h3>Waiting for other participants...</h3>
                    <div className="spinner"></div>
                </div>
            ) : (
                <div className="swipe-buttons">
                    <button 
                        className="swipe-button dislike" 
                        onClick={() => handleSwipe('left')}
                    >
                        👎 Dislike (Left)
                    </button>
                    <button 
                        className="swipe-button like" 
                        onClick={() => handleSwipe('right')}
                    >
                        👍 Like (Right)
                    </button>
                </div>
            )}
        </div>
    );
};

export default MovieSwiper;
import React, { useState, useEffect } from 'react';
import { fetchMovies } from '../services/api'; // We need to ensure this exists or create it
import { useNavigate } from 'react-router-dom';

const MovieSwiper = ({ sessionData, onMatch }) => {
    const [movies, setMovies] = useState([]);
    const [currentIndex, setCurrentIndex] = useState(0);
    const [loading, setLoading] = useState(true);
    const navigate = useNavigate();

    useEffect(() => {
        const loadMovies = async () => {
            try {
                // Assuming fetchMovies returns an array of movie objects
                // You might need to pass sessionId if your API requires it
                const movieList = await fetchMovies(sessionData?.sessionId); 
                setMovies(movieList || []);
            } catch (error) {
                console.error("Failed to load movies", error);
            } finally {
                setLoading(false);
            }
        };

        loadMovies();
    }, [sessionData]);

    const handleSwipe = (direction) => {
        const currentMovie = movies[currentIndex];
        
        // Logic to send vote to backend would go here
        // await sendVote(sessionData.sessionId, currentMovie.id, direction === 'right');

        console.log(`Swiped ${direction} on ${currentMovie.title}`);

        if (direction === 'right') {
            // Check for match logic here or via websocket/polling
            // For now, let's simulate a match if it's the last movie for demo purposes
            // onMatch(currentMovie); 
        }

        if (currentIndex < movies.length - 1) {
            setCurrentIndex(prev => prev + 1);
        } else {
            alert("No more movies!");
        }
    };

    if (loading) return <div>Loading movies...</div>;
    if (movies.length === 0) return <div>No movies found for this session.</div>;

    const currentMovie = movies[currentIndex];

    return (
        <div className="swiper-container">
            <div className="movie-card">
                {currentMovie.posterUrl && (
                    <img src={currentMovie.posterUrl} alt={currentMovie.title} className="movie-poster" />
                )}
                <h2>{currentMovie.title}</h2>
                <p>{currentMovie.description}</p>
                <p>Rating: {currentMovie.rating}</p>
            </div>

            <div className="controls">
                <button 
                    className="btn-dislike" 
                    onClick={() => handleSwipe('left')}
                    style={{ backgroundColor: '#ff4d4d', marginRight: '10px' }}
                >
                    👎 Dislike (Left)
                </button>
                <button 
                    className="btn-like" 
                    onClick={() => handleSwipe('right')}
                    style={{ backgroundColor: '#4dff4d' }}
                >
                    👍 Like (Right)
                </button>
            </div>
        </div>
    );
};

export default MovieSwiper;
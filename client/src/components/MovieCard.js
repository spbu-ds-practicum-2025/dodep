import React from 'react';
import './MovieCard.css'; // Assuming you have a CSS file for styling

const MovieCard = ({ movie, onSwipe }) => {
    const handleSwipe = (direction) => {
        onSwipe(movie.id, direction);
    };

    return (
        <div className="movie-card">
            {/* <img src={movie.poster} alt={movie.title} className="movie-poster" /> */}
            <h3 className="movie-title">{movie.title}</h3>
            <p className="movie-description">{movie.description}</p>
            <div className="swipe-buttons">
                <button onClick={() => handleSwipe('left')} className="swipe-button dislike">Dislike</button>
                <button onClick={() => handleSwipe('right')} className="swipe-button like">Like</button>
            </div>
        </div>
    );
};

export default MovieCard;
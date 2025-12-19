import React from 'react';

const MatchModal = ({ movie, onClose }) => {
    return (
        <div className="match-modal">
            <div className="match-modal-content">
                <h2>It's a Match!</h2>
                {movie ? (
                    <>
                        <h3>{movie.title}</h3>
                        <p>{movie.description}</p>
                        <img src={movie.poster_url} alt={movie.title} />
                    </>
                ) : (
                    <p>No match found.</p>
                )}
                <button onClick={onClose}>Close</button>
            </div>
        </div>
    );
};

export default MatchModal;
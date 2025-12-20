import React from 'react';

const MatchModal = ({ movie, isCreator, onContinue, onEndSession }) => {
    return (
        <div className="match-modal">
            <div className="match-modal-content">
                <h2>It's a Match!</h2>
                {movie ? (
                    <>
                        <h3>{movie.title}</h3>
                        <p>{movie.description}</p>
                        {/* <img src={movie.poster_url} alt={movie.title} /> */}
                    </>
                ) : (
                    <p>No match found.</p>
                )}
                
                <div className="match-actions">
                    {isCreator ? (
                        <>
                            <button onClick={onContinue} className="btn-continue">Continue</button>
                            <button onClick={onEndSession} className="btn-end">End Session</button>
                        </>
                    ) : (
                        <p>Waiting for host...</p>
                    )}
                </div>
            </div>
        </div>
    );
};

export default MatchModal;
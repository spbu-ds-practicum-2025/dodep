import React, { useState } from 'react';
// Change import from Switch to Routes
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import SessionLobby from './components/SessionLobby';
import MatchModal from './components/MatchModal';
import MovieSwiper from './components/MovieSwiper'; // Убедитесь, что этот файл существует
import './App.css';

function App() {
  const [sessionData, setSessionData] = useState(null);
  const [matchedMovie, setMatchedMovie] = useState(null);

  const handleSessionStart = (data) => {
    setSessionData(data);
  };

  const handleMatch = (movie) => {
    setMatchedMovie(movie);
  };

  return (
    <Router>
      <div className="App">
        {/* Replace Switch with Routes */}
        <Routes>
          {/* Old syntax: <Route path="/"><SessionLobby /></Route> */}
          {/* New syntax: use 'element' prop */}
          <Route path="/" element={<SessionLobby onSessionStart={handleSessionStart} />} />
          {/* Добавьте этот маршрут */}
          <Route path="/swipe" element={<MovieSwiper sessionData={sessionData} onMatch={handleMatch} />} />
          <Route path="/match" element={<MatchModal movie={matchedMovie} />} />
          
          {/* Add other routes similarly */}
          {/* <Route path="/swipe" element={<MovieSwiper />} /> */}
        </Routes>
      </div>
    </Router>
  );
}

export default App;
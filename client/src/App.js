import React, { useState } from 'react';
// Change import from Switch to Routes
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import SessionLobby from './components/SessionLobby';
import MatchModal from './components/MatchModal';
import MovieSwiper from './components/MovieSwiper'; // Убедитесь, что этот файл существует
import { setUserId } from './services/api';
import './App.css';

function App() {
  const [sessionData, setSessionData] = useState(null);
  const [userId, setUserIdState] = useState('');
  const [isUserIdLocked, setIsUserIdLocked] = useState(false);

  const handleSessionStart = (data) => {
    setSessionData(data);
    setIsUserIdLocked(true);
  };

  const handleSessionJoined = () => {
    setIsUserIdLocked(true);
  };

  const handleUserIdChange = (e) => {
    const id = e.target.value;
    setUserIdState(id);
    setUserId(id);
  };

  return (
    <Router>
      <div className="user-id-container">
        <label htmlFor="user-id-input">User ID: </label>
        <input 
          id="user-id-input"
          type="text" 
          value={userId} 
          onChange={handleUserIdChange} 
          placeholder="Enter User ID"
          disabled={isUserIdLocked}
        />
      </div>
      <div className="App">
        {/* Replace Switch with Routes */}
        <Routes>
          {/* Old syntax: <Route path="/"><SessionLobby /></Route> */}
          {/* New syntax: use 'element' prop */}
          <Route path="/" element={<SessionLobby onSessionStart={handleSessionStart} onSessionJoined={handleSessionJoined} />} />
          {/* Добавьте этот маршрут */}
          <Route path="/swipe" element={<MovieSwiper sessionData={sessionData} />} />
          
          {/* Add other routes similarly */}
          {/* <Route path="/swipe" element={<MovieSwiper />} /> */}
        </Routes>
      </div>
    </Router>
  );
}

export default App;
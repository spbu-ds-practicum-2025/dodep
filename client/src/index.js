import React from 'react';
import ReactDOM from 'react-dom/client'; // Import from client
// import './index.css';
import App from './App';

// Find the root element
const rootElement = document.getElementById('root');
const root = ReactDOM.createRoot(rootElement);

// Render the app
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
# Movie Matcher App

## Overview
Movie Matcher is a collaborative movie selection application that allows users to create or join sessions to swipe through movie options. Users can express their preferences by swiping right for liked movies and left for disliked ones. When all participants have swiped, the app displays a matched movie.

## Features
- Create and join movie selection sessions
- Swipe functionality for liking or disliking movies
- Real-time matching of movies based on participant preferences
- User-friendly interface for seamless interaction

## Project Structure
```
movie-matcher-app
├── public
│   ├── index.html          # Main HTML file for the React app
│   └── manifest.json       # Metadata for Progressive Web App features
├── src
│   ├── components
│   │   ├── MovieCard.js    # Component for displaying individual movie details
│   │   ├── SessionLobby.js  # Component for managing session creation and joining
│   │   └── MatchModal.js    # Component for displaying matched movie
│   ├── services
│   │   └── api.js          # API service for backend interactions
│   ├── App.js              # Main application component
│   ├── App.css             # Styles for the application
│   └── index.js            # Entry point for the React application
├── package.json             # npm configuration file
└── README.md                # Project documentation
```

## Installation
1. Clone the repository:
   ```
   git clone <repository-url>
   ```
2. Navigate to the project directory:
   ```
   cd movie-matcher-app
   ```
3. Install dependencies:
   ```
   npm install
   ```

## Usage
1. Start the development server:
   ```
   npm start
   ```
2. Open your browser and navigate to `http://localhost:3000` to view the application.

## Contributing
Contributions are welcome! Please open an issue or submit a pull request for any enhancements or bug fixes.

## License
This project is licensed under the MIT License. See the LICENSE file for details.
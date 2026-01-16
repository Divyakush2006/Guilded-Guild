# AI Based Content Recommendation System

## Project Overview

An AI-powered content recommendation system that provides personalized movie and music recommendations using advanced machine learning models.

**Features:**
- **Movie Recommendations**: Uses SASRec (Self-Attentive Sequential Recommendation) model for sequential movie recommendations
- **Music Recommendations**: Integrates with Spotify API for real-time music recommendations
- **Modern UI**: Built with React, TypeScript, and Tailwind CSS for a premium user experience

## Tech Stack

### Frontend
- **Framework**: React 18 with TypeScript
- **Build Tool**: Vite
- **UI Components**: shadcn-ui with Radix UI primitives
- **Styling**: Tailwind CSS with custom animations
- **State Management**: TanStack React Query
- **Routing**: React Router DOM

### Backend
- **Framework**: Flask (Python)
- **ML Model**: SASRec for movie recommendations
- **Music API**: Spotify Web API
- **Movie Metadata**: TMDB (The Movie Database) API

## Getting Started

### Prerequisites
- Node.js & npm ([install with nvm](https://github.com/nvm-sh/nvm#installing-and-updating))
- Python 3.8+
- Spotify API credentials
- TMDB API key

### Installation

```sh
# Clone the repository
git clone <YOUR_GIT_URL>

# Navigate to the frontend directory
cd harmony-hub-main

# Install dependencies
npm install

# Start the development server
npm run dev
```

### Backend Setup

```sh
# Navigate to the Flask app directory
cd flask_app

# Install Python dependencies
pip install -r requirements.txt

# Set up environment variables (create .env file)
# Add your Spotify and TMDB API credentials

# Start the Flask server
python app.py
```

## Available Scripts

- `npm run dev` - Start development server with hot reload
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint
- `npm test` - Run tests

## Project Structure

```
├── harmony-hub-main/          # Frontend React application
│   ├── src/
│   │   ├── components/        # React components
│   │   ├── pages/            # Page components
│   │   └── main.tsx          # Application entry point
│   └── public/               # Static assets
│
└── flask_app/                # Backend Flask application
    ├── app.py               # Main Flask application
    ├── inference_sasrec.py  # Movie recommendation engine
    ├── spotify_recommender.py # Music recommendation engine
    └── tmdb_fetcher.py      # TMDB API integration
```

## Environment Variables

Create a `.env` file in the root directory with:

```env
SPOTIFY_CLIENT_ID=your_spotify_client_id
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret
TMDB_API_KEY=your_tmdb_api_key
```

## Deployment

Build the frontend for production:

```sh
npm run build
```

The production-ready files will be in the `dist` folder.

## License

This project is part of an academic/research initiative.

## Contributors

Developed by The Guilded Guild team.

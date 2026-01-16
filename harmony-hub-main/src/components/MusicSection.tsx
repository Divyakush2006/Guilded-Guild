import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Headphones, Loader2 } from "lucide-react";
import { RecommendationForm } from "./RecommendationForm";
import { MusicCard, Song } from "./MusicCard";

export const MusicSection = () => {
  const [recommendations, setRecommendations] = useState<Song[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (current: string, history: string) => {
    setIsLoading(true);
    setHasSearched(true);
    setError(null);

    try {
      const response = await fetch('/api/recommend/music', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          current: current,
          history: history
        })
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Failed to get recommendations');
      }

      // Map API response to Song format
      const songs: Song[] = (data.recommendations || []).map((item: any, index: number) => ({
        id: item.id || String(index),
        title: item.title || 'Unknown',
        artist: item.artist || 'Unknown Artist',
        album: item.album || 'Unknown Album',
        artwork: item.artwork || 'https://images.unsplash.com/photo-1493225457124-a3eb161ffa5f?w=400&h=400&fit=crop',
        spotifyUrl: item.spotifyUrl || 'https://open.spotify.com',
        duration: item.duration || ''
      }));

      setRecommendations(songs);

    } catch (err) {
      console.error('API Error:', err);
      setError(err instanceof Error ? err.message : 'Something went wrong');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="spotify-theme min-h-screen pt-24 pb-12 px-4 md:px-8">
      {/* Hero Section */}
      <motion.div
        className="relative mb-12"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <div className="max-w-4xl mx-auto text-center py-12 md:py-20">
          <motion.div
            className="inline-flex items-center gap-2 px-4 py-2 bg-spotify-green/10 rounded-full mb-6"
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.1 }}
          >
            <Headphones className="w-5 h-5 text-spotify-green" />
            <span className="text-spotify-green font-medium">Powered by Spotify API</span>
          </motion.div>

          <motion.h1
            className="text-4xl md:text-6xl font-bold mb-6"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
          >
            Find Your Next
            <span className="text-spotify-green"> Favorite Song</span>
          </motion.h1>

          <motion.p
            className="text-lg md:text-xl text-muted-foreground mb-10 max-w-2xl mx-auto"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
          >
            Real song recommendations from Spotify - Hindi & English, all genres
          </motion.p>

          <RecommendationForm
            type="music"
            onSubmit={handleSubmit}
            isLoading={isLoading}
          />
        </div>
      </motion.div>

      {/* Error State */}
      {error && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="max-w-2xl mx-auto bg-red-500/10 border border-red-500/30 rounded-lg p-4 mb-8 text-red-400 text-center"
        >
          ⚠️ {error}
        </motion.div>
      )}

      {/* Recommendations Grid */}
      <AnimatePresence mode="wait">
        {hasSearched && !isLoading && recommendations.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 40 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="max-w-7xl mx-auto"
          >
            <div className="flex items-center gap-3 mb-6">
              <div className="w-1 h-8 bg-spotify-green rounded-full" />
              <h2 className="text-2xl font-bold">Recommended For You</h2>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4 md:gap-6">
              {recommendations.map((song, index) => (
                <MusicCard key={song.id} song={song} index={index} />
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Empty State */}
      {!hasSearched && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5 }}
          className="text-center py-12"
        >
          <div className="max-w-md mx-auto">
            <div className="w-24 h-24 mx-auto mb-6 rounded-full bg-spotify-green/10 flex items-center justify-center">
              <Headphones className="w-12 h-12 text-spotify-green" />
            </div>
            <p className="text-muted-foreground">
              Share your current vibe and listening history to discover new music tailored to your taste
            </p>
          </div>
        </motion.div>
      )}

      {/* Loading State */}
      {isLoading && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="flex flex-col items-center justify-center py-12"
        >
          <Loader2 className="w-10 h-10 animate-spin text-spotify-green mb-4" />
          <span className="text-muted-foreground">Finding similar songs on Spotify...</span>
        </motion.div>
      )}

      {/* No Results State */}
      {hasSearched && !isLoading && recommendations.length === 0 && !error && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="text-center py-12"
        >
          <div className="max-w-md mx-auto">
            <p className="text-muted-foreground">
              No similar songs found. Try a different song or check the spelling.
            </p>
          </div>
        </motion.div>
      )}
    </div>
  );
};

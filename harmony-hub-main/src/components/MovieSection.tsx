import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronLeft, ChevronRight, Popcorn, Film, Clapperboard, Loader2 } from "lucide-react";
import { RecommendationForm } from "./RecommendationForm";
import { MovieCard, Movie } from "./MovieCard";

export const MovieSection = () => {
  const [recommendations, setRecommendations] = useState<Movie[]>([]);
  const [historyBased, setHistoryBased] = useState<Movie[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (current: string, history: string) => {
    setIsLoading(true);
    setHasSearched(true);
    setError(null);

    try {
      const response = await fetch('/api/recommend/movies', {
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

      // Map API response to Movie format
      const mapToMovie = (item: any, index: number): Movie => ({
        id: item.id || String(index),
        title: item.title,
        poster: item.poster || `https://via.placeholder.com/300x450?text=${encodeURIComponent(item.title)}`,
        year: item.year || '2024',
        genre: item.genre || 'Movie',
        rating: item.rating || '8.0',
        description: item.description || `Recommended based on your preferences`,
        trailerId: item.trailerId || ''
      });

      setRecommendations((data.current_context || []).map(mapToMovie));
      setHistoryBased((data.history_based || []).map(mapToMovie));

    } catch (err) {
      console.error('API Error:', err);
      setError(err instanceof Error ? err.message : 'Something went wrong');
    } finally {
      setIsLoading(false);
    }
  };

  const MovieRow = ({ title, movies }: { title: string; movies: Movie[] }) => {
    const [scrollPosition, setScrollPosition] = useState(0);

    const scroll = (direction: "left" | "right") => {
      const container = document.getElementById(`movie-row-${title.replace(/\s/g, "-")}`);
      if (container) {
        const scrollAmount = direction === "left" ? -400 : 400;
        container.scrollBy({ left: scrollAmount, behavior: "smooth" });
        setScrollPosition(container.scrollLeft + scrollAmount);
      }
    };

    return (
      <div className="relative group">
        <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
          <Popcorn className="w-5 h-5 text-primary" />
          {title}
        </h2>

        <div className="relative">
          <button
            onClick={() => scroll("left")}
            className="absolute left-0 top-1/2 -translate-y-1/2 z-10 w-12 h-full bg-gradient-to-r from-background to-transparent opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-start pl-2"
          >
            <ChevronLeft className="w-8 h-8" />
          </button>

          <div
            id={`movie-row-${title.replace(/\s/g, "-")}`}
            className="flex gap-4 overflow-x-auto scrollbar-hide pb-4 px-1"
          >
            {movies.map((movie, index) => (
              <MovieCard key={movie.id} movie={movie} index={index} />
            ))}
          </div>

          <button
            onClick={() => scroll("right")}
            className="absolute right-0 top-1/2 -translate-y-1/2 z-10 w-12 h-full bg-gradient-to-l from-background to-transparent opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-end pr-2"
          >
            <ChevronRight className="w-8 h-8" />
          </button>
        </div>
      </div>
    );
  };

  return (
    <div className="min-h-screen pt-20 pb-12 px-4 md:px-8">
      {/* Hero Section */}
      <motion.div
        className="relative min-h-[60vh] md:min-h-[70vh] rounded-2xl overflow-hidden mb-12 mt-4"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <div
          className="absolute inset-0 bg-cover bg-center"
          style={{
            backgroundImage: `url('https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?w=1920&h=1080&fit=crop')`
          }}
        />
        <div className="absolute inset-0 bg-gradient-to-r from-background via-background/70 to-transparent" />
        <div className="absolute inset-0 bg-gradient-to-t from-background via-transparent to-transparent" />

        <div className="relative h-full flex flex-col justify-center max-w-2xl px-8 md:px-12 pt-12">
          <motion.div
            className="inline-flex items-center gap-2 px-4 py-2 bg-primary/10 rounded-full mb-6 w-fit"
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.1 }}
          >
            <Film className="w-5 h-5 text-primary" />
            <span className="text-primary font-medium">AI-Powered Movie Discovery</span>
          </motion.div>

          <motion.h1
            className="text-4xl md:text-6xl font-bold mb-4 text-shadow-hero"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
          >
            Discover Your Next
            <span className="text-primary"> Favorite Movie</span>
          </motion.h1>
          <motion.p
            className="text-lg md:text-xl text-muted-foreground mb-8"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
          >
            Powered by SASRec AI to find movies you'll love based on your taste
          </motion.p>

          <RecommendationForm
            type="movies"
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
          className="bg-red-500/10 border border-red-500/30 rounded-lg p-4 mb-8 text-red-400"
        >
          ⚠️ {error}
        </motion.div>
      )}

      {/* Loading State */}
      {isLoading && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="flex items-center justify-center py-12"
        >
          <Loader2 className="w-8 h-8 animate-spin text-primary" />
          <span className="ml-3 text-muted-foreground">Finding perfect movies for you...</span>
        </motion.div>
      )}

      {/* Recommendations */}
      <AnimatePresence mode="wait">
        {hasSearched && !isLoading && (
          <motion.div
            initial={{ opacity: 0, y: 40 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="space-y-12"
          >
            {recommendations.length > 0 && (
              <MovieRow title="Based on What You're Watching" movies={recommendations} />
            )}
            {historyBased.length > 0 && (
              <MovieRow title="From Your Watch History" movies={historyBased} />
            )}
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
            <div className="w-24 h-24 mx-auto mb-6 rounded-full bg-primary/10 flex items-center justify-center">
              <Clapperboard className="w-12 h-12 text-primary" />
            </div>
            <p className="text-muted-foreground">
              Share what you're watching and your watch history to discover new movies tailored to your taste
            </p>
          </div>
        </motion.div>
      )}
    </div>
  );
};

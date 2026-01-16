import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Play, Star, Info, X, Volume2, VolumeX } from "lucide-react";

export interface Movie {
  id: string;
  title: string;
  poster: string;
  year: string;
  genre: string;
  rating: string;
  description?: string;
  trailerId?: string; // YouTube video ID
}

interface MovieCardProps {
  movie: Movie;
  index: number;
}

// Helper to extract YouTube video ID from various URL formats
const getYouTubeEmbedUrl = (videoId: string) => {
  return `https://www.youtube.com/embed/${videoId}?autoplay=1&mute=1&controls=0&modestbranding=1&loop=1&playlist=${videoId}&showinfo=0&rel=0`;
};

export const MovieCard = ({ movie, index }: MovieCardProps) => {
  const [isHovered, setIsHovered] = useState(false);
  const [showModal, setShowModal] = useState(false);
  const [showTrailer, setShowTrailer] = useState(false);
  const [isMuted, setIsMuted] = useState(true);
  const [hoverTimeout, setHoverTimeout] = useState<NodeJS.Timeout | null>(null);

  // Delay before showing trailer on hover
  useEffect(() => {
    if (isHovered && movie.trailerId) {
      const timeout = setTimeout(() => {
        setShowTrailer(true);
      }, 800); // 800ms delay before showing trailer
      setHoverTimeout(timeout);
    } else {
      if (hoverTimeout) {
        clearTimeout(hoverTimeout);
      }
      setShowTrailer(false);
    }

    return () => {
      if (hoverTimeout) {
        clearTimeout(hoverTimeout);
      }
    };
  }, [isHovered, movie.trailerId]);

  // Lock body scroll when modal is open
  useEffect(() => {
    if (showModal) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = 'unset';
    }
    return () => {
      document.body.style.overflow = 'unset';
    };
  }, [showModal]);

  const handleCardClick = () => {
    setShowModal(true);
    setShowTrailer(false);
  };

  return (
    <>
      <motion.div
        className="relative flex-shrink-0 w-[180px] md:w-[280px] cursor-pointer group"
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ delay: index * 0.1 }}
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
        onClick={handleCardClick}
        whileHover={{ scale: 1.05, zIndex: 10 }}
      >
        <div className="relative aspect-[2/3] rounded-lg overflow-hidden shadow-xl">
          {/* Poster Image */}
          <img
            src={movie.poster}
            alt={movie.title}
            className={`w-full h-full object-cover transition-all duration-500 ${showTrailer ? "opacity-0" : "opacity-100"
              }`}
          />

          {/* YouTube Trailer on Hover */}
          <AnimatePresence>
            {showTrailer && movie.trailerId && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="absolute inset-0"
              >
                <iframe
                  src={getYouTubeEmbedUrl(movie.trailerId)}
                  className="w-full h-full object-cover"
                  allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                  allowFullScreen
                  style={{ border: 0, pointerEvents: 'none' }}
                />
              </motion.div>
            )}
          </AnimatePresence>

          {/* Gradient Overlay */}
          <motion.div
            className="absolute inset-0 bg-gradient-to-t from-background via-background/20 to-transparent"
            initial={{ opacity: 0 }}
            animate={{ opacity: isHovered ? 1 : 0 }}
            transition={{ duration: 0.3 }}
          />

          {/* Hover Info */}
          <AnimatePresence>
            {isHovered && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: 20 }}
                className="absolute bottom-0 left-0 right-0 p-3 space-y-2"
              >
                <h3 className="font-bold text-sm line-clamp-2">{movie.title}</h3>
                <div className="flex items-center gap-2 text-xs text-muted-foreground">
                  <span className="flex items-center gap-1 text-yellow-400">
                    <Star className="w-3 h-3 fill-current" />
                    {movie.rating}
                  </span>
                  <span>{movie.year}</span>
                  <span className="text-primary">{movie.genre}</span>
                </div>
                <div className="flex gap-2">
                  <motion.button
                    whileHover={{ scale: 1.1 }}
                    whileTap={{ scale: 0.9 }}
                    className="flex items-center justify-center w-8 h-8 bg-foreground text-background rounded-full"
                    onClick={(e) => {
                      e.stopPropagation();
                      setShowModal(true);
                    }}
                  >
                    <Play className="w-4 h-4 ml-0.5" fill="currentColor" />
                  </motion.button>
                  <motion.button
                    whileHover={{ scale: 1.1 }}
                    whileTap={{ scale: 0.9 }}
                    className="flex items-center justify-center w-8 h-8 bg-secondary/80 rounded-full"
                    onClick={(e) => {
                      e.stopPropagation();
                      setShowModal(true);
                    }}
                  >
                    <Info className="w-4 h-4" />
                  </motion.button>
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Playing indicator */}
          {showTrailer && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="absolute top-2 right-2 px-2 py-1 bg-primary rounded text-xs font-medium flex items-center gap-1"
            >
              <span className="w-2 h-2 bg-foreground rounded-full animate-pulse" />
              Preview
            </motion.div>
          )}

          <div className="absolute inset-0 ring-2 ring-transparent group-hover:ring-primary transition-all duration-300 rounded-lg" />
        </div>
      </motion.div>

      {/* Movie Modal with Full Trailer */}
      <AnimatePresence>
        {showModal && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-background/90 backdrop-blur-md overflow-y-auto"
            onClick={() => setShowModal(false)}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0, y: 20 }}
              animate={{ scale: 1, opacity: 1, y: 0 }}
              exit={{ scale: 0.9, opacity: 0, y: 20 }}
              className="relative w-full max-w-4xl bg-card rounded-xl card-glow-netflix my-auto max-h-[90vh] overflow-y-auto scrollbar-hide"
              onClick={(e) => e.stopPropagation()}
              style={{
                scrollbarWidth: 'none', /* Firefox */
                msOverflowStyle: 'none', /* IE and Edge */
              }}
            >
              <button
                onClick={() => setShowModal(false)}
                className="sticky top-4 right-4 z-20 p-2 bg-background/80 rounded-full hover:bg-background transition-colors ml-auto mr-4 float-right"
              >
                <X className="w-5 h-5" />
              </button>

              {/* Trailer Player */}
              <div className="relative w-full bg-black" style={{ aspectRatio: '16/9' }}>
                {movie.trailerId ? (
                  <>
                    <iframe
                      src={`https://www.youtube.com/embed/${movie.trailerId}?autoplay=1&mute=${isMuted ? 1 : 0}&modestbranding=1&rel=0`}
                      className="w-full h-full"
                      allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                      allowFullScreen
                      style={{ border: 0 }}
                    />
                    {/* Mute/Unmute Button */}
                    <motion.button
                      whileHover={{ scale: 1.1 }}
                      whileTap={{ scale: 0.9 }}
                      onClick={() => setIsMuted(!isMuted)}
                      className="absolute bottom-4 right-4 p-3 bg-background/80 rounded-full hover:bg-background transition-colors"
                    >
                      {isMuted ? (
                        <VolumeX className="w-5 h-5" />
                      ) : (
                        <Volume2 className="w-5 h-5" />
                      )}
                    </motion.button>
                  </>
                ) : (
                  <>
                    <img
                      src={movie.poster}
                      alt={movie.title}
                      className="w-full h-full object-cover"
                    />
                    <div className="absolute inset-0 bg-gradient-to-t from-card via-card/50 to-transparent" />
                    <div className="absolute inset-0 flex items-center justify-center">
                      <div className="text-center">
                        <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-foreground/20 flex items-center justify-center">
                          <Play className="w-8 h-8 text-foreground" />
                        </div>
                        <p className="text-muted-foreground">Trailer not available</p>
                      </div>
                    </div>
                  </>
                )}
              </div>

              {/* Movie Info */}
              <div className="p-6 space-y-4">
                <h2 className="text-2xl md:text-3xl font-bold">{movie.title}</h2>

                <div className="flex flex-wrap items-center gap-4 text-sm">
                  <span className="flex items-center gap-1 text-yellow-400">
                    <Star className="w-4 h-4 fill-current" />
                    {movie.rating} IMDb
                  </span>
                  <span className="text-muted-foreground">{movie.year}</span>
                  <span className="px-3 py-1 bg-primary/20 text-primary rounded-full text-xs font-medium">
                    {movie.genre}
                  </span>
                </div>

                <p className="text-muted-foreground leading-relaxed">
                  {movie.description || "An incredible cinematic experience that will leave you on the edge of your seat. Discover a world of adventure, drama, and unforgettable moments."}
                </p>

                <div className="flex gap-3 pt-2">
                  <motion.button
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    className="flex items-center gap-2 px-6 py-3 bg-foreground text-background rounded-lg font-semibold"
                  >
                    <Play className="w-5 h-5" fill="currentColor" />
                    Watch Now
                  </motion.button>
                  <motion.button
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    className="flex items-center gap-2 px-6 py-3 bg-secondary text-foreground rounded-lg font-semibold"
                  >
                    <Info className="w-5 h-5" />
                    More Info
                  </motion.button>
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
};

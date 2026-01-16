import { motion } from "framer-motion";
import { Play, ExternalLink } from "lucide-react";

export interface Song {
  id: string;
  title: string;
  artist: string;
  album: string;
  artwork: string;
  spotifyUrl?: string;
  duration?: string;
}

interface MusicCardProps {
  song: Song;
  index: number;
}

export const MusicCard = ({ song, index }: MusicCardProps) => {
  const handlePlayClick = () => {
    if (song.spotifyUrl) {
      window.open(song.spotifyUrl, "_blank");
    }
  };

  return (
    <motion.div
      className="group relative bg-card hover:bg-card-hover rounded-lg p-4 transition-all duration-300 cursor-pointer"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.05 }}
      whileHover={{ y: -4 }}
    >
      <div className="relative aspect-square mb-4 rounded-md overflow-hidden shadow-lg">
        <img
          src={song.artwork}
          alt={`${song.title} - ${song.artist}`}
          className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
        />
        
        <motion.button
          onClick={handlePlayClick}
          className="absolute bottom-2 right-2 w-12 h-12 bg-spotify-green rounded-full flex items-center justify-center shadow-xl opacity-0 group-hover:opacity-100 transition-all duration-300 hover:scale-105"
          initial={{ opacity: 0, y: 10 }}
          whileHover={{ scale: 1.1 }}
          whileTap={{ scale: 0.95 }}
        >
          <Play className="w-5 h-5 text-background ml-0.5" fill="currentColor" />
        </motion.button>
      </div>

      <div className="space-y-1">
        <h3 className="font-semibold text-foreground truncate group-hover:text-spotify-green transition-colors">
          {song.title}
        </h3>
        <p className="text-sm text-muted-foreground truncate">
          {song.artist}
        </p>
        <div className="flex items-center justify-between">
          <p className="text-xs text-muted-foreground/70 truncate flex-1">
            {song.album}
          </p>
          {song.duration && (
            <span className="text-xs text-muted-foreground/70 ml-2">
              {song.duration}
            </span>
          )}
        </div>
      </div>

      {song.spotifyUrl && (
        <motion.div
          className="absolute top-3 right-3 opacity-0 group-hover:opacity-100 transition-opacity"
          initial={{ scale: 0.8 }}
          whileHover={{ scale: 1.1 }}
        >
          <a
            href={song.spotifyUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center justify-center w-8 h-8 bg-background/80 rounded-full"
            onClick={(e) => e.stopPropagation()}
          >
            <ExternalLink className="w-4 h-4 text-spotify-green" />
          </a>
        </motion.div>
      )}
    </motion.div>
  );
};

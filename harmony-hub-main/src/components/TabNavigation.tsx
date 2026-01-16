import { motion } from "framer-motion";
import { Film, Music } from "lucide-react";

type TabType = "movies" | "music";

interface TabNavigationProps {
  activeTab: TabType;
  onTabChange: (tab: TabType) => void;
}

export const TabNavigation = ({ activeTab, onTabChange }: TabNavigationProps) => {
  return (
    <div className="fixed top-0 left-0 right-0 z-50 bg-background/80 backdrop-blur-lg border-b border-border">
      <div className="container mx-auto px-4">
        <nav className="flex items-center justify-between py-4">
          <motion.div
            className="flex items-center gap-2"
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
          >
            <img
              src="/logo.jpg"
              alt="Guilded Guild Logo"
              className="w-10 h-10 rounded-full object-cover ring-2 ring-primary/20"
            />
            <span className="text-2xl font-bold bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent">
              Guilded Guild
            </span>
          </motion.div>

          <div className="flex gap-2 bg-secondary/50 p-1 rounded-lg">
            <motion.button
              onClick={() => onTabChange("movies")}
              className={`relative flex items-center gap-2 px-6 py-2.5 rounded-md text-sm font-medium transition-all duration-200 ${activeTab === "movies"
                ? "text-foreground"
                : "text-muted-foreground hover:text-foreground"
                }`}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
            >
              {activeTab === "movies" && (
                <motion.div
                  layoutId="activeTab"
                  className="absolute inset-0 bg-netflix-red rounded-md"
                  transition={{ type: "spring", bounce: 0.2, duration: 0.6 }}
                />
              )}
              <Film className="w-4 h-4 relative z-10" />
              <span className="relative z-10">Movies</span>
            </motion.button>

            <motion.button
              onClick={() => onTabChange("music")}
              className={`relative flex items-center gap-2 px-6 py-2.5 rounded-md text-sm font-medium transition-all duration-200 ${activeTab === "music"
                ? "text-foreground"
                : "text-muted-foreground hover:text-foreground"
                }`}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
            >
              {activeTab === "music" && (
                <motion.div
                  layoutId="activeTab"
                  className="absolute inset-0 bg-spotify-green rounded-md"
                  transition={{ type: "spring", bounce: 0.2, duration: 0.6 }}
                />
              )}
              <Music className="w-4 h-4 relative z-10" />
              <span className="relative z-10">Music</span>
            </motion.button>
          </div>

          <div className="w-32" />
        </nav>
      </div>
    </div>
  );
};

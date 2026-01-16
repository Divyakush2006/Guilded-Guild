import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { TabNavigation } from "@/components/TabNavigation";
import { MovieSection } from "@/components/MovieSection";
import { MusicSection } from "@/components/MusicSection";

type TabType = "movies" | "music";

const Index = () => {
  const [activeTab, setActiveTab] = useState<TabType>("movies");

  return (
    <div className={`min-h-screen ${activeTab === "music" ? "spotify-theme" : ""}`}>
      <TabNavigation activeTab={activeTab} onTabChange={setActiveTab} />
      
      <AnimatePresence mode="wait">
        <motion.div
          key={activeTab}
          initial={{ opacity: 0, x: activeTab === "movies" ? -20 : 20 }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0, x: activeTab === "movies" ? 20 : -20 }}
          transition={{ duration: 0.3, ease: "easeInOut" }}
        >
          {activeTab === "movies" ? <MovieSection /> : <MusicSection />}
        </motion.div>
      </AnimatePresence>
    </div>
  );
};

export default Index;

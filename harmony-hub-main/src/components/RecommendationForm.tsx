import { useState } from "react";
import { motion } from "framer-motion";
import { Search, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

interface RecommendationFormProps {
  type: "movies" | "music";
  onSubmit: (current: string, history: string) => void;
  isLoading: boolean;
}

export const RecommendationForm = ({ type, onSubmit, isLoading }: RecommendationFormProps) => {
  const [current, setCurrent] = useState("");
  const [history, setHistory] = useState("");

  const isMovie = type === "movies";
  
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (current.trim()) {
      onSubmit(current, history);
    }
  };

  return (
    <motion.form
      onSubmit={handleSubmit}
      className="w-full max-w-2xl mx-auto space-y-4"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.2 }}
    >
      <div className="space-y-2">
        <label className="text-sm font-medium text-muted-foreground">
          What are you {isMovie ? "watching" : "listening to"} right now?
        </label>
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
          <Input
            type="text"
            value={current}
            onChange={(e) => setCurrent(e.target.value)}
            placeholder={isMovie 
              ? "e.g. Inception, The Dark Knight, Interstellar" 
              : "e.g. Kesariya, Shape of You, Tum Hi Ho"
            }
            className="pl-10 h-12 bg-input border-border focus:border-primary focus:ring-primary/20"
          />
        </div>
      </div>

      <div className="space-y-2">
        <label className="text-sm font-medium text-muted-foreground">
          Your {isMovie ? "watch" : "listening"} history (comma separated)
        </label>
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
          <Input
            type="text"
            value={history}
            onChange={(e) => setHistory(e.target.value)}
            placeholder={isMovie 
              ? "e.g. Avengers, Iron Man, Thor" 
              : "e.g. Tujhko Jo Paaya, Allah Duhai Hai, Kesariya"
            }
            className="pl-10 h-12 bg-input border-border focus:border-primary focus:ring-primary/20"
          />
        </div>
      </div>

      <Button
        type="submit"
        disabled={!current.trim() || isLoading}
        className="w-full h-12 text-base font-semibold group"
      >
        {isLoading ? (
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
          >
            <Sparkles className="w-5 h-5" />
          </motion.div>
        ) : (
          <>
            <Sparkles className="w-5 h-5 mr-2 group-hover:animate-pulse" />
            Get AI Recommendations
          </>
        )}
      </Button>
    </motion.form>
  );
};

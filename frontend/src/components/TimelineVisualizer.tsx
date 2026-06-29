import React from 'react';
import { Film, Calendar } from 'lucide-react';
import { Citation } from '../services/api';

interface TimelineVisualizerProps {
  citations: Citation[];
}

export const TimelineVisualizer: React.FC<TimelineVisualizerProps> = ({ citations }) => {
  // Filter citations representing movies
  const movies = citations.filter(c => c.category === 'movies' && c.title);
  
  if (movies.length === 0) {
    return (
      <div className="text-center p-4 text-jarvis-muted text-xs border border-dashed border-jarvis-border rounded bg-slate-900/10">
        No timeline events detected in current response query.
      </div>
    );
  }

  return (
    <div className="relative border-l border-jarvis-cyan/30 ml-3 pl-5 space-y-6 my-4">
      {movies.map((movie, index) => (
        <div key={index} className="relative group">
          {/* Neon Connector Node */}
          <div className="absolute -left-[26px] top-1.5 w-3.5 h-3.5 rounded-full bg-[#020813] border-2 border-jarvis-cyan group-hover:bg-jarvis-cyan transition-colors duration-300 shadow-glow" />
          
          <div className="jarvis-panel p-3.5 rounded-lg group-hover:border-jarvis-blue/30 transition-all duration-300">
            <div className="flex items-center justify-between gap-2 mb-1.5">
              <span className="text-xs font-tech text-jarvis-cyan flex items-center gap-1">
                <Film className="w-3 h-3" />
                {movie.title}
              </span>
              <span className="text-[10px] text-jarvis-gold px-1.5 py-0.5 rounded bg-jarvis-gold/10 border border-jarvis-gold/20 font-tech">
                Active Cutoff
              </span>
            </div>
            
            <p className="text-xs text-jarvis-muted flex items-center gap-2">
              <Calendar className="w-3.5 h-3.5 text-jarvis-blue" />
              Source Reference Document: <span className="text-jarvis-text font-mono">{movie.source.split('/').pop()}</span>
            </p>
          </div>
        </div>
      ))}
    </div>
  );
};
export default TimelineVisualizer;

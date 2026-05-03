import React from 'react';
import { motion } from 'framer-motion';
import { Send } from 'lucide-react';

export const NeonInput = ({ input, setInput, onSend, isStreaming, onStop }) => {
  return (
    <div className="p-8 pt-0">
      <div className="relative group">
        <div className="absolute -inset-1 bg-gradient-to-r from-neon-blue to-neon-purple rounded-3xl blur opacity-25 group-hover:opacity-50 transition duration-1000 group-focus-within:opacity-100" />
        <div className="relative bg-background-light rounded-2xl flex items-center p-2 border border-white/10">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && onSend()}
            disabled={isStreaming}
            placeholder={isStreaming ? "Telvyn is processing..." : "Transmit instructions to Telvyn..."}
            className="flex-1 bg-transparent border-none outline-none px-6 text-sm text-white placeholder:text-white/20 disabled:opacity-50"
          />
          {isStreaming ? (
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={onStop}
              className="p-3 bg-red-500/20 text-red-500 border border-red-500/30 rounded-xl font-black shadow-lg shadow-red-500/10"
            >
              <div className="w-4 h-4 bg-red-500 rounded-sm" />
            </motion.button>
          ) : (
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={onSend}
              className="p-3 bg-neon-blue text-background-deep rounded-xl font-black shadow-lg shadow-neon-blue/40"
            >
              <Send size={20} />
            </motion.button>
          )}
        </div>
      </div>
    </div>
  );
};

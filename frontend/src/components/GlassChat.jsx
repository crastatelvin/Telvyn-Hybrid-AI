import React, { useRef, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Cpu } from 'lucide-react';

export const GlassChat = ({ messages, scrollRef, currentThought }) => {
  return (
    <div 
      ref={scrollRef}
      className="flex-1 overflow-y-auto p-8 flex flex-col gap-8 scroll-smooth"
    >
      {messages.length === 0 && (
        <div className="h-full flex flex-col items-center justify-center text-center">
          <motion.div
            animate={{ y: [0, -10, 0] }}
            transition={{ duration: 4, repeat: Infinity, ease: 'easeInOut' }}
            className="p-6 bg-neon-blue/5 rounded-full border border-neon-blue/20 mb-6"
          >
            <Cpu size={64} className="text-neon-blue/40" />
          </motion.div>
          <h2 className="text-2xl font-bold text-white/80 mb-2">Neural Interface Ready</h2>
          <p className="text-sm text-white/40 max-w-sm">Awaiting architect instructions. Knowledge base indexed and persistent memory active.</p>
        </div>
      )}
      
      {messages.map((msg, idx) => (
        <motion.div
          key={idx}
          initial={{ opacity: 0, x: msg.role === 'human' ? 20 : -20 }}
          animate={{ opacity: 1, x: 0 }}
          className={`flex ${msg.role === 'human' ? 'justify-end' : 'justify-start'}`}
        >
          <div className={`max-w-[80%] rounded-2xl p-5 ${
            msg.role === 'human' 
            ? 'bg-white/10 border border-white/10 rounded-tr-none' 
            : 'bg-neon-blue/10 border border-neon-blue/20 rounded-tl-none shadow-[0_0_20px_rgba(0,191,255,0.05)]'
          }`}>
            <div className="text-[10px] font-black uppercase tracking-widest text-white/30 mb-2">
              {msg.role === 'human' ? 'Architect' : 'Telvyn AI'}
            </div>
            <div className="text-sm leading-relaxed text-white/90 whitespace-pre-wrap">
              {msg.content}
            </div>
          </div>
        </motion.div>
      ))}

      {currentThought && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex justify-start"
        >
          <div className="bg-neon-purple/5 border border-neon-purple/20 rounded-2xl p-4 flex items-center gap-3 max-w-[60%]">
            <div className="relative">
              <div className="w-2 h-2 bg-neon-purple rounded-full animate-ping absolute inset-0" />
              <div className="w-2 h-2 bg-neon-purple rounded-full" />
            </div>
            <div className="text-[10px] font-bold text-neon-purple uppercase tracking-[0.2em] animate-pulse">
              {currentThought}
            </div>
          </div>
        </motion.div>
      )}
    </div>
  );
};

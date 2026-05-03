import React from 'react';
import { motion } from 'framer-motion';
import { Cpu, Activity, Database, Shield, RefreshCw, Zap } from 'lucide-react';

const GlassCard = ({ children, className = "", glowColor = "blue" }) => (
  <motion.div 
    initial={{ opacity: 0, y: 20 }}
    animate={{ opacity: 1, y: 0 }}
    className={`glass-panel rounded-3xl p-6 ${glowColor === 'blue' ? 'neon-border-blue' : 'neon-border-purple'} ${className}`}
  >
    {children}
  </motion.div>
);

const SidebarItem = ({ icon: Icon, label, active, onClick }) => (
  <motion.div
    whileHover={{ x: 5, backgroundColor: 'rgba(255,255,255,0.05)' }}
    onClick={onClick}
    className={`flex items-center gap-4 p-4 rounded-2xl cursor-pointer transition-all ${active ? 'bg-white/10 text-neon-blue' : 'text-white/60'}`}
  >
    <Icon size={20} className={active ? 'drop-shadow-[0_0_8px_rgba(0,191,255,0.8)]' : ''} />
    <span className="font-medium">{label}</span>
  </motion.div>
);

const StatusCard = ({ label, value, icon: Icon, color }) => (
  <div className="bg-white/5 rounded-2xl p-4 border border-white/5 flex items-center gap-4">
    <div className={`p-3 rounded-xl bg-black/20 text-white/80 border border-white/10`}>
      <Icon size={18} className={color === 'neon-blue' ? 'text-neon-blue' : 'text-neon-purple'} />
    </div>
    <div>
      <div className="text-xs text-white/40 uppercase tracking-wider">{label}</div>
      <div className="text-sm font-bold text-white/90">{value}</div>
    </div>
  </div>
);

export const CyberSidebar = ({ isSyncing, onSync, sessions, currentSessionId, onSelectSession, onNewChat }) => {
  return (
    <motion.aside 
      initial={{ x: -100, opacity: 0 }}
      animate={{ x: 0, opacity: 1 }}
      className="w-80 z-10 flex flex-col gap-6"
    >
      <GlassCard className="flex items-center gap-4 py-8">
        <div className="p-3 bg-neon-blue/20 rounded-2xl border border-neon-blue/30 shadow-[0_0_15px_rgba(0,191,255,0.4)]">
          <Cpu className="text-neon-blue" size={32} />
        </div>
        <div>
          <h1 className="text-xl font-black tracking-tighter text-white">TELVYN <span className="text-neon-blue">HYBRID</span></h1>
          <p className="text-[10px] uppercase tracking-[0.2em] text-white/40 font-bold">Advanced Neural AI</p>
        </div>
      </GlassCard>

      <GlassCard className="flex-1 flex flex-col gap-2 overflow-y-auto min-h-0">
        <div className="flex items-center justify-between mb-2 px-4">
          <div className="text-[10px] uppercase tracking-widest text-white/30 font-bold">Conversations</div>
          <motion.button
            whileHover={{ scale: 1.1, color: '#00BFFF' }}
            onClick={onNewChat}
            className="text-white/40"
          >
            <Zap size={14} />
          </motion.button>
        </div>

        <div className="flex flex-col gap-1 overflow-y-auto pr-2 custom-scrollbar">
          {sessions.map((session) => (
            <motion.div
              key={session.id}
              whileHover={{ x: 4, backgroundColor: 'rgba(255,255,255,0.05)' }}
              onClick={() => onSelectSession(session.id)}
              className={`p-3 rounded-xl cursor-pointer transition-all border ${
                currentSessionId === session.id 
                ? 'bg-white/10 border-neon-blue/30 text-neon-blue' 
                : 'border-transparent text-white/40'
              }`}
            >
              <div className="text-xs font-medium truncate mb-1">{session.id}</div>
              <div className="text-[8px] opacity-40 uppercase">{new Date(session.last_active).toLocaleDateString()}</div>
            </motion.div>
          ))}
          {sessions.length === 0 && (
            <div className="px-4 py-8 text-center text-[10px] text-white/20 uppercase tracking-widest">No history detected</div>
          )}
        </div>
        
        <div className="mt-auto pt-6 border-t border-white/5 flex flex-col gap-4">
          <div className="text-[10px] uppercase tracking-widest text-white/30 font-bold px-4">System Core</div>
          <StatusCard label="Neural Load" value="12.4 TFLOPS" icon={Zap} color="neon-blue" />
          
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={onSync}
            className="w-full py-4 rounded-2xl bg-gradient-to-r from-neon-blue to-neon-purple font-bold text-sm shadow-lg shadow-neon-blue/20 flex items-center justify-center gap-3"
          >
            <RefreshCw size={18} className={isSyncing ? 'animate-spin' : ''} />
            SYNC KNOWLEDGE
          </motion.button>
        </div>
      </GlassCard>
    </motion.aside>
  );
};

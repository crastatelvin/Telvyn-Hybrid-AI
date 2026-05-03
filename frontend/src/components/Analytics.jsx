import React from 'react';
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip } from 'recharts';
import { motion } from 'framer-motion';

export const Analytics = ({ data }) => {
  // Mock data for initial view
  const chartData = data || [
    { name: 'Mon', value: 400 },
    { name: 'Tue', value: 300 },
    { name: 'Wed', value: 600 },
    { name: 'Thu', value: 800 },
    { name: 'Fri', value: 500 },
    { name: 'Sat', value: 900 },
    { name: 'Sun', value: 1100 },
  ];

  return (
    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="w-full h-full p-8 flex flex-col gap-8"
    >
      <div className="flex justify-between items-end">
        <div>
          <h2 className="text-2xl font-black text-white tracking-tighter">CORPORATE <span className="text-neon-blue">ANALYTICS</span></h2>
          <p className="text-xs text-white/40 uppercase tracking-widest font-bold">Neural Trend Analysis & Market Intelligence</p>
        </div>
        <div className="flex gap-4">
          <div className="p-4 bg-white/5 border border-white/10 rounded-2xl">
            <div className="text-[10px] text-white/40 uppercase font-black mb-1">Market Sentiment</div>
            <div className="text-xl font-black text-green-400">+12.4%</div>
          </div>
          <div className="p-4 bg-white/5 border border-white/10 rounded-2xl">
            <div className="text-[10px] text-white/40 uppercase font-black mb-1">Competitor Activity</div>
            <div className="text-xl font-black text-neon-purple">HIGH</div>
          </div>
        </div>
      </div>

      <div className="flex-1 bg-black/20 rounded-3xl border border-white/5 p-8 relative group overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-neon-blue/5 to-transparent pointer-events-none" />
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={chartData}>
            <defs>
              <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#00BFFF" stopOpacity={0.3}/>
                <stop offset="95%" stopColor="#00BFFF" stopOpacity={0}/>
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
            <XAxis dataKey="name" stroke="rgba(255,255,255,0.2)" fontSize={10} axisLine={false} tickLine={false} />
            <YAxis stroke="rgba(255,255,255,0.2)" fontSize={10} axisLine={false} tickLine={false} />
            <Tooltip 
              contentStyle={{ backgroundColor: 'rgba(0,0,0,0.8)', borderColor: 'rgba(255,255,255,0.1)', borderRadius: '12px' }}
              itemStyle={{ color: '#00BFFF', fontSize: '12px', fontWeight: 'bold' }}
            />
            <Area type="monotone" dataKey="value" stroke="#00BFFF" strokeWidth={3} fillOpacity={1} fill="url(#colorValue)" />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </motion.div>
  );
};

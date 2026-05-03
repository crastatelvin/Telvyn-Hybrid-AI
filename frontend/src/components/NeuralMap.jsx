import React, { useMemo } from 'react';
import ForceGraph3D from 'react-force-graph-3d';
import { motion } from 'framer-motion';

export const NeuralMap = ({ sessions }) => {
  const data = useMemo(() => {
    const nodes = sessions.map(s => ({ id: s.id, type: 'session', group: 1 }));
    nodes.push({ id: 'TELVYN_CORE', type: 'core', group: 0 });
    
    const links = sessions.map(s => ({ source: 'TELVYN_CORE', target: s.id }));
    
    return { nodes, links };
  }, [sessions]);

  return (
    <motion.div 
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="w-full h-full relative"
    >
      <ForceGraph3D
        graphData={data}
        backgroundColor="rgba(0,0,0,0)"
        nodeColor={node => node.group === 0 ? '#00BFFF' : '#BF00FF'}
        linkColor={() => 'rgba(255,255,255,0.1)'}
        nodeLabel="id"
        nodeRelSize={6}
        linkOpacity={0.2}
      />
      <div className="absolute top-8 left-8 p-4 bg-black/40 backdrop-blur-xl border border-white/10 rounded-2xl">
        <h3 className="text-xs font-black text-white/60 tracking-widest uppercase mb-1">Knowledge Topology</h3>
        <p className="text-[10px] text-white/30 uppercase">Neural connections between active sessions and company core.</p>
      </div>
    </motion.div>
  );
};

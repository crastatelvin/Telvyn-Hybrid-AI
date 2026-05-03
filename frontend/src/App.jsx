import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Menu, User } from 'lucide-react';
import axios from 'axios';

import { CyberSidebar } from './components/CyberSidebar';
import { GlassChat } from './components/GlassChat';
import { NeonInput } from './components/NeonInput';
import { ThreeBackground } from './components/ThreeBackground';

export default function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isSyncing, setIsSyncing] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const [currentThought, setCurrentThought] = useState('');
  const [telemetry, setTelemetry] = useState({ total_tokens: 0 });
  const [sessions, setSessions] = useState([]);
  const [currentSessionId, setCurrentSessionId] = useState('default_session');
  
  const scrollRef = useRef(null);
  const abortControllerRef = useRef(null);

  useEffect(() => {
    fetchSessions();
    fetchHistory(currentSessionId);
    fetchTelemetry(currentSessionId);
  }, [currentSessionId]);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, currentThought]);

  const fetchSessions = async () => {
    try {
      const res = await axios.get('http://localhost:8000/sessions');
      setSessions(res.data);
    } catch (err) {
      console.error("Sessions fetch failed", err);
    }
  };

  const fetchHistory = async (sid) => {
    try {
      const res = await axios.get(`http://localhost:8000/history/${sid}`);
      setMessages(res.data);
    } catch (err) {
      console.error("History fetch failed", err);
    }
  };

  const fetchTelemetry = async (sid) => {
    try {
      const res = await axios.get(`http://localhost:8000/telemetry/${sid}`);
      setTelemetry(res.data);
    } catch (err) {
      console.error("Telemetry fetch failed", err);
    }
  };

  const handleNewChat = () => {
    const newSid = `session_${Math.random().toString(36).substr(2, 9)}`;
    setCurrentSessionId(newSid);
    setMessages([]);
  };

  const streamChat = async () => {
    if (!input.trim()) return;

    setIsStreaming(true);
    setCurrentThought('Analyzing request...');
    
    const userMsg = { role: 'human', content: input };
    setMessages(prev => [...prev, userMsg]);
    const currentInput = input;
    setInput('');

    const aiMsg = { role: 'ai', content: '' };
    setMessages(prev => [...prev, aiMsg]);

    abortControllerRef.current = new AbortController();

    try {
      const response = await fetch('http://localhost:8000/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: currentInput, session_id: currentSessionId }),
        signal: abortControllerRef.current.signal
      });

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let accumulatedResponse = "";

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        
        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split('\n');
        
        for (const line of lines) {
          if (line.trim().startsWith('event: thought')) {
            // Next line will be data
          } else if (line.trim().startsWith('data: ')) {
            const dataStr = line.replace('data: ', '').trim();
            
            // Heuristic to distinguish thoughts from content
            if (dataStr.startsWith('Exec') || dataStr.includes('Tool') || dataStr.includes('Refining')) {
              setCurrentThought(dataStr);
            } else {
              setCurrentThought('');
              accumulatedResponse += dataStr;
              setMessages(prev => {
                const newMsgs = [...prev];
                if (newMsgs.length > 0) {
                  newMsgs[newMsgs.length - 1].content = accumulatedResponse;
                }
                return newMsgs;
              });
            }
          }
        }
      }
    } catch (err) {
      if (err.name === 'AbortError') {
        console.log("Stream stopped by user");
      } else {
        console.error("Streaming failed", err);
      }
    } finally {
      setIsStreaming(false);
      setCurrentThought('');
      fetchTelemetry(currentSessionId);
      fetchSessions();
    }
  };

  const handleStop = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
  };

  return (
    <div className="flex h-screen w-full bg-background-deep p-6 gap-6 relative overflow-hidden">
      <ThreeBackground />
      <CyberSidebar 
        isSyncing={isSyncing} 
        onSync={() => {}} 
        sessions={sessions}
        currentSessionId={currentSessionId}
        onSelectSession={setCurrentSessionId}
        onNewChat={handleNewChat}
      />

      <main className="flex-1 z-10 flex flex-col gap-6 min-w-0">
        <div className="flex items-center justify-between px-4">
          <div className="flex items-center gap-6">
            <div className="flex items-center gap-2 bg-white/5 px-4 py-2 rounded-full border border-white/10 backdrop-blur-md">
              <div className="w-2 h-2 rounded-full bg-green-500 animate-ping" />
              <span className="text-[10px] font-bold text-white/60 tracking-widest uppercase">System Online</span>
            </div>
            <div className="flex items-center gap-2 bg-white/5 px-4 py-2 rounded-full border border-white/10 backdrop-blur-md">
              <span className="text-[10px] font-bold text-white/40 tracking-widest uppercase">Tokens:</span>
              <span className="text-[10px] font-black text-neon-blue">{telemetry.total_tokens.toLocaleString()}</span>
            </div>
          </div>
        </div>

        <motion.div 
          initial={{ opacity: 0, scale: 0.98 }}
          animate={{ opacity: 1, scale: 1 }}
          className="flex-1 flex flex-col p-0 overflow-hidden glass-panel rounded-3xl bg-black/20 neon-border-purple"
        >
          <GlassChat messages={messages} scrollRef={scrollRef} currentThought={currentThought} />
          <NeonInput 
            input={input} 
            setInput={setInput} 
            onSend={streamChat} 
            isStreaming={isStreaming}
            onStop={handleStop}
          />
        </motion.div>
      </main>
    </div>
  );
}

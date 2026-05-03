import React, { useRef, useMemo } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import * as THREE from 'three';

const NeuralWaves = () => {
  const mesh = useRef();
  
  // Create a grid of particles
  const count = 50;
  const sep = 0.5;
  const particles = useMemo(() => {
    const positions = new Float32Array(count * count * 3);
    for (let xi = 0; xi < count; xi++) {
      for (let zi = 0; zi < count; zi++) {
        const i = (xi * count + zi) * 3;
        positions[i] = (xi - count / 2) * sep;
        positions[i + 1] = 0;
        positions[i + 2] = (zi - count / 2) * sep;
      }
    }
    return positions;
  }, []);

  useFrame((state) => {
    const time = state.clock.getElapsedTime();
    const pos = mesh.current.geometry.attributes.position.array;
    
    for (let xi = 0; xi < count; xi++) {
      for (let zi = 0; zi < count; zi++) {
        const i = (xi * count + zi) * 3;
        // Wave animation
        pos[i + 1] = Math.sin(xi / 5 + time) * 0.3 + Math.cos(zi / 5 + time) * 0.3;
      }
    }
    mesh.current.geometry.attributes.position.needsUpdate = true;
  });

  return (
    <points ref={mesh}>
      <bufferGeometry>
        <bufferAttribute
          attach="attributes-position"
          count={particles.length / 3}
          array={particles}
          itemSize={3}
        />
      </bufferGeometry>
      <pointsMaterial
        size={0.03}
        color="#00BFFF"
        transparent
        opacity={0.4}
        sizeAttenuation
      />
    </points>
  );
};

export const ThreeBackground = () => {
  return (
    <div className="absolute inset-0 z-0 bg-background-deep pointer-events-none">
      <Canvas camera={{ position: [10, 10, 10], fov: 45 }}>
        <color attach="background" args={['#050816']} />
        <fog attach="fog" args={['#050816', 5, 25]} />
        <ambientLight intensity={0.5} />
        <NeuralWaves />
      </Canvas>
      
      {/* Overlay Gradients for Cinematic Feel */}
      <div className="absolute inset-0 bg-gradient-to-t from-background-deep via-transparent to-transparent opacity-80" />
      <div className="absolute top-[-20%] left-[-10%] w-[60%] h-[60%] bg-neon-blue/10 blur-[140px] rounded-full animate-pulse mix-blend-screen" />
      <div className="absolute bottom-[-20%] right-[-10%] w-[60%] h-[60%] bg-neon-purple/10 blur-[140px] rounded-full animate-pulse mix-blend-screen" style={{ animationDelay: '2s' }} />
    </div>
  );
};

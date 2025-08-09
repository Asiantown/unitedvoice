'use client'

import { Suspense, useRef, useMemo } from 'react'
import { Canvas, useFrame } from '@react-three/fiber'
import { OrbitControls, Environment } from '@react-three/drei'
import { EffectComposer, Bloom, ChromaticAberration } from '@react-three/postprocessing'
import * as THREE from 'three'
import VoiceOrb, { type OrbState } from './VoiceOrb'
import AmbientParticles from './AmbientParticles'

interface ParticleSystemProps {
  count?: number
}

function ParticleSystem({ count = 100 }: ParticleSystemProps) {
  const pointsRef = useRef<THREE.Points>(null)
  
  const [positions, colors] = useMemo(() => {
    const positions = new Float32Array(count * 3)
    const colors = new Float32Array(count * 3)
    
    // Create particles in a sphere around the orb
    for (let i = 0; i < count; i++) {
      const i3 = i * 3
      
      // Random position in sphere
      const radius = 3 + Math.random() * 4
      const theta = Math.random() * Math.PI * 2
      const phi = Math.acos(2 * Math.random() - 1)
      
      positions[i3] = radius * Math.sin(phi) * Math.cos(theta)
      positions[i3 + 1] = radius * Math.sin(phi) * Math.sin(theta)
      positions[i3 + 2] = radius * Math.cos(phi)
      
      // Random colors (blue to pink gradient)
      const t = Math.random()
      if (t < 0.33) {
        // Blue
        colors[i3] = 0.29     // R
        colors[i3 + 1] = 0.56 // G
        colors[i3 + 2] = 1.0  // B
      } else if (t < 0.66) {
        // Purple
        colors[i3] = 0.66     // R
        colors[i3 + 1] = 0.33 // G
        colors[i3 + 2] = 0.97 // B
      } else {
        // Pink
        colors[i3] = 0.93     // R
        colors[i3 + 1] = 0.28 // G
        colors[i3 + 2] = 0.6  // B
      }
    }
    
    return [positions, colors]
  }, [count])
  
  useFrame((state) => {
    if (!pointsRef.current) return
    
    const time = state.clock.getElapsedTime()
    const positions = pointsRef.current.geometry.attributes.position.array as Float32Array
    
    // Animate particles with slow floating motion
    for (let i = 0; i < count; i++) {
      const i3 = i * 3
      const x = positions[i3]
      const y = positions[i3 + 1]
      const z = positions[i3 + 2]
      
      // Add subtle floating animation
      positions[i3 + 1] = y + Math.sin(time * 0.5 + i * 0.1) * 0.01
      positions[i3] = x + Math.cos(time * 0.3 + i * 0.2) * 0.005
    }
    
    pointsRef.current.geometry.attributes.position.needsUpdate = true
    
    // Rotate the entire particle system slowly
    pointsRef.current.rotation.y = time * 0.05
  })
  
  return (
    <points ref={pointsRef}>
      <bufferGeometry>
        <bufferAttribute
          attach="attributes-position"
          args={[positions, 3]}
        />
        <bufferAttribute
          attach="attributes-color"
          args={[colors, 3]}
        />
      </bufferGeometry>
      <pointsMaterial
        size={0.02}
        vertexColors
        transparent
        opacity={0.6}
        sizeAttenuation
        blending={THREE.AdditiveBlending}
      />
    </points>
  )
}

interface BackgroundOrbsProps {
  count?: number
}

function BackgroundOrbs({ count = 3 }: BackgroundOrbsProps) {
  const groupRef = useRef<THREE.Group>(null)
  
  const orbs = useMemo(() => {
    return Array.from({ length: count }, (_, i) => ({
      id: i,
      position: [
        (Math.random() - 0.5) * 20,
        (Math.random() - 0.5) * 15,
        -10 - Math.random() * 10
      ] as [number, number, number],
      scale: 0.3 + Math.random() * 0.5,
      speed: 0.1 + Math.random() * 0.2
    }))
  }, [count])
  
  useFrame((state) => {
    if (!groupRef.current) return
    
    const time = state.clock.getElapsedTime()
    groupRef.current.children.forEach((child, i) => {
      const orb = orbs[i]
      child.position.y = orb.position[1] + Math.sin(time * orb.speed + i) * 2
      child.rotation.y = time * orb.speed * 0.5
    })
  })
  
  return (
    <group ref={groupRef}>
      {orbs.map((orb) => (
        <mesh key={orb.id} position={orb.position} scale={orb.scale}>
          <sphereGeometry args={[1, 32, 32]} />
          <meshBasicMaterial
            color="#4a90ff"
            transparent
            opacity={0.1}
          />
        </mesh>
      ))}
    </group>
  )
}

interface SceneLightingProps {
  // Currently no props, but keeping interface for future extensibility
}

function SceneLighting({}: SceneLightingProps) {
  return (
    <>
      {/* Main key light */}
      <directionalLight
        position={[5, 5, 5]}
        intensity={2}
        color="#ffffff"
        castShadow
        shadow-mapSize-width={2048}
        shadow-mapSize-height={2048}
      />
      
      {/* Fill light */}
      <directionalLight
        position={[-3, 2, 4]}
        intensity={1}
        color="#a855f7"
      />
      
      {/* Rim light */}
      <directionalLight
        position={[0, -3, -5]}
        intensity={0.8}
        color="#ec4899"
      />
      
      {/* Ambient light */}
      <ambientLight intensity={0.3} color="#4a90ff" />
      
      {/* Point lights for extra drama */}
      <pointLight
        position={[3, 0, 2]}
        intensity={1.5}
        color="#4a90ff"
        distance={10}
        decay={2}
      />
      
      <pointLight
        position={[-3, 0, 2]}
        intensity={1.2}
        color="#a855f7"
        distance={8}
        decay={2}
      />
    </>
  )
}

interface OrbSceneProps {
  orbState?: OrbState
  audioLevel?: number
  frequency?: number
  className?: string
  enableControls?: boolean
  cameraPosition?: [number, number, number]
}

export default function OrbScene({ 
  orbState = 'idle', 
  audioLevel = 0,
  frequency = 0,
  className = '',
  enableControls = false,
  cameraPosition = [0, 0, 5]
}: OrbSceneProps) {
  return (
    <div className={`w-full h-full ${className}`}>
      <Canvas
        camera={{
          position: cameraPosition,
          fov: 45,
          near: 0.1,
          far: 100
        }}
        gl={{
          antialias: true,
          alpha: true,
          powerPreference: 'high-performance'
        }}
        dpr={[1, 2]}
      >
        <Suspense fallback={null}>
          {/* Scene lighting */}
          <SceneLighting />
          
          {/* Environment map for reflections */}
          <Environment preset="city" background={false} />
          
          {/* Main voice orb */}
          <VoiceOrb
            state={orbState}
            audioLevel={audioLevel}
            frequency={frequency}
            size={1.2}
          />
          
          {/* Enhanced ambient particles */}
          <AmbientParticles 
            count={180} 
            audioLevel={audioLevel}
            radius={4.5}
            speed={0.4}
          />
          
          {/* Background orbs for depth */}
          <BackgroundOrbs count={5} />
          
          {/* Camera controls (optional) */}
          {enableControls && (
            <OrbitControls
              enableZoom={false}
              enablePan={false}
              minPolarAngle={Math.PI / 4}
              maxPolarAngle={3 * Math.PI / 4}
              autoRotate
              autoRotateSpeed={0.5}
            />
          )}
          
          {/* Post-processing effects */}
          <EffectComposer>
            {/* Bloom effect for glow */}
            <Bloom
              intensity={0.8}
              luminanceThreshold={0.2}
              luminanceSmoothing={0.9}
              height={512}
              opacity={0.8}
            />
            
            {/* Subtle chromatic aberration for premium look */}
            <ChromaticAberration
              offset={[0.001, 0.001]}
            />
          </EffectComposer>
        </Suspense>
      </Canvas>
    </div>
  )
}
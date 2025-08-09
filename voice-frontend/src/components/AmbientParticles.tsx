'use client'

import { useRef, useMemo, useEffect } from 'react'
import { useFrame } from '@react-three/fiber'
import * as THREE from 'three'

interface AmbientParticlesProps {
  count?: number
  audioLevel?: number
  radius?: number
  speed?: number
}

interface ParticleData {
  originalPosition: THREE.Vector3
  velocity: THREE.Vector3
  phase: number
  size: number
  color: THREE.Color
  life: number
  maxLife: number
}

export default function AmbientParticles({ 
  count = 200, 
  audioLevel = 0, 
  radius = 4, 
  speed = 0.5 
}: AmbientParticlesProps) {
  const pointsRef = useRef<THREE.Points>(null)
  const materialRef = useRef<THREE.ShaderMaterial>(null)
  
  // Particle data for advanced animations
  const particlesData = useMemo(() => {
    const data: ParticleData[] = []
    
    for (let i = 0; i < count; i++) {
      const phi = Math.acos(2 * Math.random() - 1)
      const theta = 2 * Math.PI * Math.random()
      const r = radius + Math.random() * radius * 0.5
      
      const position = new THREE.Vector3(
        r * Math.sin(phi) * Math.cos(theta),
        r * Math.sin(phi) * Math.sin(theta),
        r * Math.cos(phi)
      )
      
      data.push({
        originalPosition: position.clone(),
        velocity: new THREE.Vector3(
          (Math.random() - 0.5) * 0.01,
          (Math.random() - 0.5) * 0.01,
          (Math.random() - 0.5) * 0.01
        ),
        phase: Math.random() * Math.PI * 2,
        size: 0.5 + Math.random() * 1.5,
        color: new THREE.Color().setHSL(
          0.6 + Math.random() * 0.3, // Hue: blue to pink
          0.8 + Math.random() * 0.2, // Saturation
          0.5 + Math.random() * 0.5  // Lightness
        ),
        life: Math.random(),
        maxLife: 2 + Math.random() * 3
      })
    }
    
    return data
  }, [count, radius])
  
  // Create buffer attributes
  const [positions, colors, sizes] = useMemo(() => {
    const positions = new Float32Array(count * 3)
    const colors = new Float32Array(count * 3)
    const sizes = new Float32Array(count)
    
    particlesData.forEach((particle, i) => {
      const i3 = i * 3
      
      positions[i3] = particle.originalPosition.x
      positions[i3 + 1] = particle.originalPosition.y
      positions[i3 + 2] = particle.originalPosition.z
      
      colors[i3] = particle.color.r
      colors[i3 + 1] = particle.color.g
      colors[i3 + 2] = particle.color.b
      
      sizes[i] = particle.size
    })
    
    return [positions, colors, sizes]
  }, [count, particlesData])
  
  // Custom shader material for particles
  const material = useMemo(() => {
    return new THREE.ShaderMaterial({
      vertexShader: `
        attribute float size;
        attribute vec3 color;
        
        varying vec3 vColor;
        varying float vOpacity;
        
        uniform float uTime;
        uniform float uAudioLevel;
        
        void main() {
          vColor = color;
          
          // Audio-reactive size
          float audioSize = size * (1.0 + uAudioLevel * 2.0);
          
          // Pulsing effect
          float pulse = sin(uTime * 3.0 + position.x + position.y + position.z) * 0.3 + 0.7;
          
          // Distance-based opacity
          vec4 mvPosition = modelViewMatrix * vec4(position, 1.0);
          float dist = length(mvPosition.xyz);
          vOpacity = 1.0 - smoothstep(5.0, 15.0, dist);
          
          gl_PointSize = audioSize * pulse * vOpacity * 100.0;
          gl_Position = projectionMatrix * mvPosition;
        }
      `,
      fragmentShader: `
        varying vec3 vColor;
        varying float vOpacity;
        
        uniform float uTime;
        
        void main() {
          // Create circular particles
          vec2 center = vec2(0.5);
          float dist = distance(gl_PointCoord, center);
          
          // Soft circular fade
          float alpha = 1.0 - smoothstep(0.2, 0.5, dist);
          
          // Add shimmer effect
          float shimmer = sin(uTime * 5.0 + gl_PointCoord.x * 10.0) * 0.3 + 0.7;
          
          // Final color with glow
          vec3 finalColor = vColor * shimmer;
          finalColor += vColor * 0.5; // Add glow
          
          gl_FragColor = vec4(finalColor, alpha * vOpacity * 0.8);
        }
      `,
      uniforms: {
        uTime: { value: 0 },
        uAudioLevel: { value: 0 }
      },
      transparent: true,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
      vertexColors: true
    })
  }, [])
  
  // Animation loop
  useFrame((state) => {
    if (!pointsRef.current) return
    
    const time = state.clock.getElapsedTime()
    const positions = pointsRef.current.geometry.attributes.position.array as Float32Array
    const colors = pointsRef.current.geometry.attributes.color.array as Float32Array
    
    // Update material uniforms
    if (materialRef.current) {
      materialRef.current.uniforms.uTime.value = time
      materialRef.current.uniforms.uAudioLevel.value = audioLevel
    }
    
    // Animate particles
    particlesData.forEach((particle, i) => {
      const i3 = i * 3
      
      // Update life
      particle.life += 0.016 // ~60fps
      if (particle.life > particle.maxLife) {
        particle.life = 0
        
        // Respawn particle
        const phi = Math.acos(2 * Math.random() - 1)
        const theta = 2 * Math.PI * Math.random()
        const r = radius + Math.random() * radius * 0.5
        
        particle.originalPosition.set(
          r * Math.sin(phi) * Math.cos(theta),
          r * Math.sin(phi) * Math.sin(theta),
          r * Math.cos(phi)
        )
        
        // New random color
        particle.color.setHSL(
          0.6 + Math.random() * 0.3,
          0.8 + Math.random() * 0.2,
          0.5 + Math.random() * 0.5
        )
        
        colors[i3] = particle.color.r
        colors[i3 + 1] = particle.color.g
        colors[i3 + 2] = particle.color.b
      }
      
      // Floating animation
      const floatX = Math.sin(time * speed + particle.phase) * 0.02
      const floatY = Math.cos(time * speed * 1.3 + particle.phase + 1) * 0.015
      const floatZ = Math.sin(time * speed * 0.8 + particle.phase + 2) * 0.025
      
      // Audio-reactive movement
      const audioFloat = audioLevel * Math.sin(time * 5.0 + i * 0.1) * 0.1
      
      // Update positions
      positions[i3] = particle.originalPosition.x + floatX + audioFloat
      positions[i3 + 1] = particle.originalPosition.y + floatY + particle.velocity.y * time
      positions[i3 + 2] = particle.originalPosition.z + floatZ
      
      // Slight drift
      particle.originalPosition.add(particle.velocity)
    })
    
    // Update attributes
    pointsRef.current.geometry.attributes.position.needsUpdate = true
    pointsRef.current.geometry.attributes.color.needsUpdate = true
    
    // Slow rotation of the entire system
    pointsRef.current.rotation.y = time * 0.02
    pointsRef.current.rotation.x = Math.sin(time * 0.01) * 0.1
  })
  
  // Update material reference
  useEffect(() => {
    if (pointsRef.current?.material) {
      materialRef.current = pointsRef.current.material as THREE.ShaderMaterial
    }
  }, [])
  
  return (
    <points ref={pointsRef} material={material}>
      <bufferGeometry>
        <bufferAttribute
          attach="attributes-position"
          args={[positions, 3]}
        />
        <bufferAttribute
          attach="attributes-color"
          args={[colors, 3]}
        />
        <bufferAttribute
          attach="attributes-size"
          args={[sizes, 1]}
        />
      </bufferGeometry>
    </points>
  )
}
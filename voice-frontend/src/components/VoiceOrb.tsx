'use client'

import { useRef, useMemo, useEffect, Suspense } from 'react'
import { Canvas, useFrame } from '@react-three/fiber'
import { Sphere, Environment } from '@react-three/drei'
import { EffectComposer, Bloom } from '@react-three/postprocessing'
import * as THREE from 'three'
import { createHolographicMaterial } from './HolographicMaterial'

export type OrbState = 'idle' | 'listening' | 'speaking' | 'thinking'

interface VoiceOrbProps {
  state?: OrbState
  audioLevel?: number
  size?: 'small' | 'medium' | 'large' | 'xl' | number
  frequency?: number
  isRecording?: boolean
  isConnected?: boolean
  className?: string
}

interface InternalOrbProps {
  state: OrbState
  audioLevel?: number
  size?: number
  frequency?: number
}

const vertexShader = `
  varying vec3 vPosition;
  varying vec3 vNormal;
  varying vec2 vUv;
  varying vec3 vWorldPosition;
  
  uniform float uTime;
  uniform float uAudioLevel;
  uniform float uDistortion;
  
  // Noise function for organic distortion
  vec3 mod289(vec3 x) {
    return x - floor(x * (1.0 / 289.0)) * 289.0;
  }
  
  vec4 mod289(vec4 x) {
    return x - floor(x * (1.0 / 289.0)) * 289.0;
  }
  
  vec4 permute(vec4 x) {
    return mod289(((x*34.0)+1.0)*x);
  }
  
  vec4 taylorInvSqrt(vec4 r) {
    return 1.79284291400159 - 0.85373472095314 * r;
  }
  
  float snoise(vec3 v) {
    const vec2  C = vec2(1.0/6.0, 1.0/3.0) ;
    const vec4  D = vec4(0.0, 0.5, 1.0, 2.0);
    
    vec3 i  = floor(v + dot(v, C.yyy) );
    vec3 x0 =   v - i + dot(i, C.xxx) ;
    
    vec3 g = step(x0.yzx, x0.xyz);
    vec3 l = 1.0 - g;
    vec3 i1 = min( g.xyz, l.zxy );
    vec3 i2 = max( g.xyz, l.zxy );
    
    vec3 x1 = x0 - i1 + C.xxx;
    vec3 x2 = x0 - i2 + C.yyy;
    vec3 x3 = x0 - D.yyy;
    
    i = mod289(i);
    vec4 p = permute( permute( permute(
               i.z + vec4(0.0, i1.z, i2.z, 1.0 ))
             + i.y + vec4(0.0, i1.y, i2.y, 1.0 ))
             + i.x + vec4(0.0, i1.x, i2.x, 1.0 ));
    
    float n_ = 0.142857142857;
    vec3  ns = n_ * D.wyz - D.xzx;
    
    vec4 j = p - 49.0 * floor(p * ns.z * ns.z);
    
    vec4 x_ = floor(j * ns.z);
    vec4 y_ = floor(j - 7.0 * x_ );
    
    vec4 x = x_ *ns.x + ns.yyyy;
    vec4 y = y_ *ns.x + ns.yyyy;
    vec4 h = 1.0 - abs(x) - abs(y);
    
    vec4 b0 = vec4( x.xy, y.xy );
    vec4 b1 = vec4( x.zw, y.zw );
    
    vec4 s0 = floor(b0)*2.0 + 1.0;
    vec4 s1 = floor(b1)*2.0 + 1.0;
    vec4 sh = -step(h, vec4(0.0));
    
    vec4 a0 = b0.xzyw + s0.xzyw*sh.xxyy ;
    vec4 a1 = b1.xzyw + s1.xzyw*sh.zzww ;
    
    vec3 p0 = vec3(a0.xy,h.x);
    vec3 p1 = vec3(a0.zw,h.y);
    vec3 p2 = vec3(a1.xy,h.z);
    vec3 p3 = vec3(a1.zw,h.w);
    
    vec4 norm = taylorInvSqrt(vec4(dot(p0,p0), dot(p1,p1), dot(p2, p2), dot(p3,p3)));
    p0 *= norm.x;
    p1 *= norm.y;
    p2 *= norm.z;
    p3 *= norm.w;
    
    vec4 m = max(0.6 - vec4(dot(x0,x0), dot(x1,x1), dot(x2,x2), dot(x3,x3)), 0.0);
    m = m * m;
    return 42.0 * dot( m*m, vec4( dot(p0,x0), dot(p1,x1), dot(p2,x2), dot(p3,x3) ) );
  }
  
  void main() {
    vUv = uv;
    vNormal = normalize(normalMatrix * normal);
    
    // Create organic distortion based on noise
    vec3 pos = position;
    float noise = snoise(pos * 3.0 + uTime * 0.5) * 0.1;
    float audioNoise = snoise(pos * 5.0 + uTime * 2.0) * uAudioLevel * 0.2;
    
    // Breathing animation
    float breathe = sin(uTime * 1.5) * 0.02;
    
    // Apply distortions
    pos += normal * (noise + audioNoise + breathe) * uDistortion;
    
    vPosition = pos;
    vec4 worldPosition = modelMatrix * vec4(pos, 1.0);
    vWorldPosition = worldPosition.xyz;
    
    gl_Position = projectionMatrix * modelViewMatrix * vec4(pos, 1.0);
  }
`

const fragmentShader = `
  varying vec3 vPosition;
  varying vec3 vNormal;
  varying vec2 vUv;
  varying vec3 vWorldPosition;
  
  uniform float uTime;
  uniform float uAudioLevel;
  uniform vec3 uColor1;
  uniform vec3 uColor2;
  uniform vec3 uColor3;
  uniform float uMetallic;
  uniform float uRoughness;
  uniform float uOpacity;
  
  // Fresnel calculation
  float fresnel(vec3 viewDirection, vec3 normal, float power) {
    return pow(1.0 - dot(viewDirection, normal), power);
  }
  
  // Noise for surface details
  float random(vec2 st) {
    return fract(sin(dot(st.xy, vec2(12.9898,78.233))) * 43758.5453123);
  }
  
  float noise(vec2 st) {
    vec2 i = floor(st);
    vec2 f = fract(st);
    
    float a = random(i);
    float b = random(i + vec2(1.0, 0.0));
    float c = random(i + vec2(0.0, 1.0));
    float d = random(i + vec2(1.0, 1.0));
    
    vec2 u = f * f * (3.0 - 2.0 * f);
    
    return mix(a, b, u.x) + (c - a)* u.y * (1.0 - u.x) + (d - b) * u.x * u.y;
  }
  
  void main() {
    vec3 viewDirection = normalize(vec3(0.0, 0.0, 4.0) - vWorldPosition);
    vec3 normal = normalize(vNormal);
    
    // Fresnel effect for metallic look
    float fresnelTerm = fresnel(viewDirection, normal, 2.0);
    
    // Create gradient based on position and time
    float gradient = dot(normal, vec3(0.0, 1.0, 0.0)) * 0.5 + 0.5;
    gradient += sin(uTime * 2.0 + vPosition.y * 5.0) * 0.1;
    
    // Audio reactive shimmer
    float shimmer = noise(vUv * 20.0 + uTime) * uAudioLevel * 0.3;
    
    // Mix colors based on gradient and effects
    vec3 color = mix(uColor1, uColor2, gradient);
    color = mix(color, uColor3, fresnelTerm * 0.7);
    
    // Add metallic highlights
    color += fresnelTerm * 0.3;
    color += shimmer;
    
    // Add subtle noise for surface detail
    float surfaceNoise = noise(vUv * 50.0) * 0.05;
    color += surfaceNoise;
    
    // Enhance edges with glow
    float edge = 1.0 - abs(dot(viewDirection, normal));
    color += edge * edge * 0.2;
    
    gl_FragColor = vec4(color, uOpacity);
  }
`

function InternalVoiceOrb({ state = 'idle', audioLevel = 0, size = 1, frequency = 0 }: InternalOrbProps) {
  const meshRef = useRef<THREE.Mesh>(null)
  const innerMeshRef = useRef<THREE.Mesh>(null)
  const materialRef = useRef<THREE.ShaderMaterial>(null)
  
  // Create enhanced holographic material
  const material = useMemo(() => {
    return createHolographicMaterial({
      color1: '#4a90ff', // Electric blue
      color2: '#a855f7', // Purple
      color3: '#ec4899', // Hot pink
      metallic: 0.95,
      roughness: 0.05,
      opacity: 0.88,
      fresnelPower: 2.5,
      hologramStrength: 0.8,
      noiseScale: 1.2
    })
  }, [])
  
  // Inner glow material
  const innerMaterial = useMemo(() => {
    return new THREE.MeshBasicMaterial({
      color: '#4a90ff',
      transparent: true,
      opacity: 0.15,
      side: THREE.BackSide,
      blending: THREE.AdditiveBlending
    })
  }, [])
  
  // Enhanced animation and state effects
  useFrame((frameState) => {
    if (!materialRef.current) return
    
    const time = frameState.clock.getElapsedTime()
    materialRef.current.uniforms.uTime.value = time
    materialRef.current.uniforms.uAudioLevel.value = audioLevel
    
    // Frequency-based color shifting
    if (frequency > 0) {
      const hue = (frequency / 1000) % 1 // Map frequency to hue
      const color = new THREE.Color().setHSL(hue * 0.3 + 0.6, 0.8, 0.6)
      materialRef.current.uniforms.uColor3.value = color
    }
    
    // State-specific behaviors
    switch (state) {
      case 'idle':
        // Gentle breathing
        const breathScale = 1 + Math.sin(time * 1.5) * 0.02
        if (meshRef.current) {
          meshRef.current.scale.setScalar(breathScale)
        }
        // Soft hologram effect
        materialRef.current.uniforms.uHologramStrength.value = THREE.MathUtils.lerp(
          materialRef.current.uniforms.uHologramStrength.value,
          0.3,
          0.02
        )
        break
        
      case 'listening':
        // Active pulsing
        const pulse = 1 + Math.sin(time * 6) * 0.08 + audioLevel * 0.15
        if (meshRef.current) {
          meshRef.current.scale.setScalar(pulse)
        }
        // Increased hologram intensity
        materialRef.current.uniforms.uHologramStrength.value = THREE.MathUtils.lerp(
          materialRef.current.uniforms.uHologramStrength.value,
          0.7,
          0.05
        )
        // Listening rotation
        if (meshRef.current) {
          meshRef.current.rotation.y += 0.005
        }
        break
        
      case 'speaking':
        // Audio-reactive scaling and distortion
        const speakScale = 1 + audioLevel * 0.3 + Math.sin(time * 8) * 0.05
        if (meshRef.current) {
          meshRef.current.scale.setScalar(speakScale)
        }
        // Maximum hologram effect
        materialRef.current.uniforms.uHologramStrength.value = THREE.MathUtils.lerp(
          materialRef.current.uniforms.uHologramStrength.value,
          1.2 + audioLevel,
          0.1
        )
        break
        
      case 'thinking':
        // Slow thoughtful rotation with subtle pulsing
        if (meshRef.current) {
          meshRef.current.rotation.y = time * 0.3
          meshRef.current.rotation.x = Math.sin(time * 0.5) * 0.1
          const thinkScale = 1 + Math.sin(time * 2) * 0.03
          meshRef.current.scale.setScalar(thinkScale)
        }
        // Moderate hologram effect
        materialRef.current.uniforms.uHologramStrength.value = THREE.MathUtils.lerp(
          materialRef.current.uniforms.uHologramStrength.value,
          0.6,
          0.03
        )
        break
    }
    
    // Update inner glow opacity based on activity
    if (innerMeshRef.current && innerMeshRef.current.material instanceof THREE.MeshBasicMaterial) {
      const targetOpacity = 0.1 + audioLevel * 0.2 + (state === 'speaking' ? 0.1 : 0)
      innerMeshRef.current.material.opacity = THREE.MathUtils.lerp(
        innerMeshRef.current.material.opacity,
        targetOpacity,
        0.1
      )
    }
  })
  
  // Update material reference
  useEffect(() => {
    if (meshRef.current?.material) {
      materialRef.current = meshRef.current.material as THREE.ShaderMaterial
    }
  }, [])
  
  return (
    <group>
      {/* Main holographic orb */}
      <Sphere ref={meshRef} args={[size, 96, 96]} material={material} />
      
      {/* Inner glow sphere */}
      <Sphere ref={innerMeshRef} args={[size * 0.92, 48, 48]} material={innerMaterial} />
      
      {/* Additional glow layers for depth */}
      <Sphere args={[size * 0.85, 32, 32]}>
        <meshBasicMaterial
          color="#a855f7"
          transparent
          opacity={0.08}
          side={THREE.BackSide}
          blending={THREE.AdditiveBlending}
        />
      </Sphere>
      
      <Sphere args={[size * 0.78, 24, 24]}>
        <meshBasicMaterial
          color="#ec4899"
          transparent
          opacity={0.05}
          side={THREE.BackSide}
          blending={THREE.AdditiveBlending}
        />
      </Sphere>
    </group>
  )
}

// Main wrapper component that provides the Canvas and full interface
export default function VoiceOrb({ 
  state,
  audioLevel = 0, 
  size = 'medium', 
  frequency = 0,
  isRecording = false,
  isConnected = false,
  className = ''
}: VoiceOrbProps) {
  // Determine orb state based on props
  const orbState: OrbState = useMemo(() => {
    if (!isConnected) return 'idle'
    if (isRecording) return 'listening'
    if (state) return state
    return 'idle'
  }, [state, isRecording, isConnected])

  // Size mapping
  const sizeValue = useMemo(() => {
    if (typeof size === 'number') return size
    switch (size) {
      case 'small': return 0.8
      case 'medium': return 1.2  
      case 'large': return 1.6
      case 'xl': return 2.0
      default: return 1.2
    }
  }, [size])

  return (
    <div className={`w-full h-full ${className}`} data-testid="voice-orb">
      <Canvas
        camera={{
          position: [0, 0, 4],
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
          <ambientLight intensity={0.4} color="#4a90ff" />
          <pointLight
            position={[3, 3, 3]}
            intensity={2}
            color="#4a90ff"
            distance={10}
            decay={2}
          />
          <pointLight
            position={[-3, -3, 3]}
            intensity={1.5}
            color="#a855f7"
            distance={8}
            decay={2}
          />
          
          {/* Environment for reflections */}
          <Environment preset="city" background={false} />
          
          {/* The actual orb */}
          <InternalVoiceOrb
            state={orbState}
            audioLevel={audioLevel}
            frequency={frequency}
            size={sizeValue}
          />
          
          {/* Post-processing effects */}
          <EffectComposer>
            <Bloom
              intensity={isRecording ? 1.2 : 0.8}
              luminanceThreshold={0.2}
              luminanceSmoothing={0.9}
              height={512}
              opacity={0.8}
            />
          </EffectComposer>
        </Suspense>
      </Canvas>
    </div>
  )
}


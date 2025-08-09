'use client'

import { useMemo } from 'react'
import * as THREE from 'three'

export interface HolographicMaterialProps {
  color1?: string
  color2?: string
  color3?: string
  metallic?: number
  roughness?: number
  opacity?: number
  fresnelPower?: number
  hologramStrength?: number
  noiseScale?: number
  time?: number
  audioLevel?: number
}

export function createHolographicMaterial({
  color1 = '#4a90ff',
  color2 = '#a855f7', 
  color3 = '#ec4899',
  metallic = 0.9,
  roughness = 0.1,
  opacity = 0.85,
  fresnelPower = 2.0,
  hologramStrength = 1.0,
  noiseScale = 1.0,
  time = 0,
  audioLevel = 0
}: HolographicMaterialProps = {}) {
  
  const vertexShader = `
    varying vec3 vPosition;
    varying vec3 vNormal;
    varying vec2 vUv;
    varying vec3 vWorldPosition;
    varying vec3 vViewPosition;
    
    uniform float uTime;
    uniform float uAudioLevel;
    uniform float uHologramStrength;
    uniform float uNoiseScale;
    
    // Advanced noise functions
    vec3 permute(vec3 x) { return mod(((x*34.0)+1.0)*x, 289.0); }
    
    float snoise(vec2 v) {
      const vec4 C = vec4(0.211324865405187, 0.366025403784439, -0.577350269189626, 0.024390243902439);
      vec2 i  = floor(v + dot(v, C.yy) );
      vec2 x0 = v -   i + dot(i, C.xx);
      vec2 i1;
      i1 = (x0.x > x0.y) ? vec2(1.0, 0.0) : vec2(0.0, 1.0);
      vec4 x12 = x0.xyxy + C.xxzz;
      x12.xy -= i1;
      i = mod(i, 289.0);
      vec3 p = permute( permute( i.y + vec3(0.0, i1.y, 1.0 )) + i.x + vec3(0.0, i1.x, 1.0 ));
      vec3 m = max(0.5 - vec3(dot(x0,x0), dot(x12.xy,x12.xy), dot(x12.zw,x12.zw)), 0.0);
      m = m*m ;
      m = m*m ;
      vec3 x = 2.0 * fract(p * C.www) - 1.0;
      vec3 h = abs(x) - 0.5;
      vec3 ox = floor(x + 0.5);
      vec3 a0 = x - ox;
      m *= 1.79284291400159 - 0.85373472095314 * ( a0*a0 + h*h );
      vec3 g;
      g.x  = a0.x  * x0.x  + h.x  * x0.y;
      g.yz = a0.yz * x12.xz + h.yz * x12.yw;
      return 130.0 * dot(m, g);
    }
    
    float turbulence(vec2 P) {
      float val = 0.0;
      float freq = 1.0;
      for(int i = 0; i < 4; i++) {
        val += abs(snoise(P * freq)) / freq;
        freq *= 2.0;
      }
      return val;
    }
    
    void main() {
      vUv = uv;
      vNormal = normalize(normalMatrix * normal);
      
      // Create complex surface distortion
      vec3 pos = position;
      
      // Multiple noise layers for organic feel
      float noise1 = snoise(pos.xy * uNoiseScale + uTime * 0.1) * 0.05;
      float noise2 = snoise(pos.xz * uNoiseScale * 2.0 + uTime * 0.2) * 0.03;
      float noise3 = snoise(pos.yz * uNoiseScale * 3.0 + uTime * 0.15) * 0.02;
      
      // Audio-reactive pulsing with turbulence
      float audioNoise = turbulence(pos.xy * 5.0 + uTime) * uAudioLevel * 0.3;
      
      // Breathing effect
      float breathe = sin(uTime * 1.2) * cos(uTime * 0.8) * 0.015;
      
      // Hologram-style scan lines
      float scanLines = sin(pos.y * 50.0 + uTime * 10.0) * 0.005 * uHologramStrength;
      
      // Apply all distortions
      vec3 distortion = normal * (noise1 + noise2 + noise3 + audioNoise + breathe + scanLines);
      pos += distortion;
      
      vPosition = pos;
      vec4 worldPosition = modelMatrix * vec4(pos, 1.0);
      vWorldPosition = worldPosition.xyz;
      
      vec4 mvPosition = modelViewMatrix * vec4(pos, 1.0);
      vViewPosition = -mvPosition.xyz;
      
      gl_Position = projectionMatrix * mvPosition;
    }
  `
  
  const fragmentShader = `
    varying vec3 vPosition;
    varying vec3 vNormal;
    varying vec2 vUv;
    varying vec3 vWorldPosition;
    varying vec3 vViewPosition;
    
    uniform float uTime;
    uniform float uAudioLevel;
    uniform vec3 uColor1;
    uniform vec3 uColor2;
    uniform vec3 uColor3;
    uniform float uMetallic;
    uniform float uRoughness;
    uniform float uOpacity;
    uniform float uFresnelPower;
    uniform float uHologramStrength;
    uniform float uNoiseScale;
    
    // Enhanced noise
    vec3 permute(vec3 x) { return mod(((x*34.0)+1.0)*x, 289.0); }
    
    float snoise(vec2 v) {
      const vec4 C = vec4(0.211324865405187, 0.366025403784439, -0.577350269189626, 0.024390243902439);
      vec2 i  = floor(v + dot(v, C.yy) );
      vec2 x0 = v -   i + dot(i, C.xx);
      vec2 i1;
      i1 = (x0.x > x0.y) ? vec2(1.0, 0.0) : vec2(0.0, 1.0);
      vec4 x12 = x0.xyxy + C.xxzz;
      x12.xy -= i1;
      i = mod(i, 289.0);
      vec3 p = permute( permute( i.y + vec3(0.0, i1.y, 1.0 )) + i.x + vec3(0.0, i1.x, 1.0 ));
      vec3 m = max(0.5 - vec3(dot(x0,x0), dot(x12.xy,x12.xy), dot(x12.zw,x12.zw)), 0.0);
      m = m*m ;
      m = m*m ;
      vec3 x = 2.0 * fract(p * C.www) - 1.0;
      vec3 h = abs(x) - 0.5;
      vec3 ox = floor(x + 0.5);
      vec3 a0 = x - ox;
      m *= 1.79284291400159 - 0.85373472095314 * ( a0*a0 + h*h );
      vec3 g;
      g.x  = a0.x  * x0.x  + h.x  * x0.y;
      g.yz = a0.yz * x12.xz + h.yz * x12.yw;
      return 130.0 * dot(m, g);
    }
    
    // Fresnel with customizable power
    float fresnel(vec3 viewDir, vec3 normal, float power) {
      return pow(1.0 - max(0.0, dot(viewDir, normal)), power);
    }
    
    // Hologram interference pattern
    float hologramPattern(vec2 uv, float time) {
      float pattern1 = sin(uv.y * 100.0 + time * 5.0) * 0.5 + 0.5;
      float pattern2 = sin(uv.x * 80.0 + time * 3.0) * 0.5 + 0.5;
      float pattern3 = sin((uv.x + uv.y) * 60.0 + time * 7.0) * 0.5 + 0.5;
      
      return (pattern1 + pattern2 + pattern3) / 3.0;
    }
    
    // Chromatic shift effect
    vec3 chromaticShift(vec2 uv, float amount) {
      vec2 shift = vec2(amount, 0.0);
      float r = snoise(uv - shift);
      float g = snoise(uv);
      float b = snoise(uv + shift);
      return vec3(r, g, b) * 0.5 + 0.5;
    }
    
    void main() {
      vec3 viewDirection = normalize(vec3(0.0, 0.0, 4.0) - vWorldPosition);
      vec3 normal = normalize(vNormal);
      
      // Enhanced Fresnel
      float fresnelTerm = fresnel(viewDirection, normal, uFresnelPower);
      
      // Multi-layer color mixing
      float gradient1 = dot(normal, vec3(0.0, 1.0, 0.0)) * 0.5 + 0.5;
      float gradient2 = dot(normal, vec3(1.0, 0.0, 0.0)) * 0.5 + 0.5;
      float gradient3 = dot(normal, vec3(0.0, 0.0, 1.0)) * 0.5 + 0.5;
      
      // Time-based color shifts
      gradient1 += sin(uTime * 2.0 + vPosition.y * 5.0) * 0.1;
      gradient2 += cos(uTime * 1.5 + vPosition.x * 4.0) * 0.1;
      gradient3 += sin(uTime * 1.8 + vPosition.z * 3.0) * 0.1;
      
      // Base color mixing
      vec3 color = mix(uColor1, uColor2, gradient1);
      color = mix(color, uColor3, gradient2 * fresnelTerm);
      
      // Holographic effects
      float hologram = hologramPattern(vUv, uTime) * uHologramStrength;
      color += hologram * 0.2;
      
      // Chromatic aberration
      vec3 chromatic = chromaticShift(vUv, 0.01);
      color = mix(color, chromatic, 0.15);
      
      // Audio-reactive shimmer
      float shimmer = snoise(vUv * 30.0 + uTime * 2.0) * uAudioLevel;
      color += shimmer * 0.4;
      
      // Metallic highlights
      float metallicHighlight = pow(fresnelTerm, 3.0) * uMetallic;
      color += metallicHighlight * 0.5;
      
      // Edge glow
      float edge = 1.0 - abs(dot(viewDirection, normal));
      color += pow(edge, 3.0) * 0.3;
      
      // Scan lines effect
      float scanLines = sin(vUv.y * 200.0 + uTime * 15.0) * 0.02 * uHologramStrength;
      color += scanLines;
      
      // Surface detail noise
      float surfaceNoise = snoise(vUv * 100.0 + uTime * 0.5) * 0.03;
      color += surfaceNoise;
      
      // Final color enhancement
      color = pow(color, vec3(0.9)); // Slight gamma correction
      color = mix(color, vec3(1.0), fresnelTerm * 0.1); // Add subtle white rim
      
      gl_FragColor = vec4(color, uOpacity);
    }
  `
  
  return new THREE.ShaderMaterial({
    vertexShader,
    fragmentShader,
    uniforms: {
      uTime: { value: time },
      uAudioLevel: { value: audioLevel },
      uColor1: { value: new THREE.Color(color1) },
      uColor2: { value: new THREE.Color(color2) },
      uColor3: { value: new THREE.Color(color3) },
      uMetallic: { value: metallic },
      uRoughness: { value: roughness },
      uOpacity: { value: opacity },
      uFresnelPower: { value: fresnelPower },
      uHologramStrength: { value: hologramStrength },
      uNoiseScale: { value: noiseScale }
    },
    transparent: true,
    side: THREE.DoubleSide,
    blending: THREE.NormalBlending,
    depthWrite: false
  })
}

export function useHolographicMaterial(props: HolographicMaterialProps = {}) {
  return useMemo(() => createHolographicMaterial(props), [
    props.color1,
    props.color2, 
    props.color3,
    props.metallic,
    props.roughness,
    props.opacity,
    props.fresnelPower,
    props.hologramStrength,
    props.noiseScale
  ])
}
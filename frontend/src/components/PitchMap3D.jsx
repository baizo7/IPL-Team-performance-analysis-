import React, { useRef, useState, useEffect } from 'react'
import { Canvas, useFrame } from '@react-three/fiber'
import { OrbitControls, Text, Html } from '@react-three/drei'
import * as THREE from 'three'
import axios from 'axios'

const API_BASE = 'http://localhost:8000/api'

// A glowing scatter point for the pitched ball
function PitchPoint({ position, outcome, bowler, speed }) {
  const [hovered, setHover] = useState(false)
  
  // Color mapping based on outcome
  const getColor = () => {
    switch(outcome) {
      case 'Wicket': return '#f43f5e' // Red
      case 'Boundary': return '#38bdf8' // Blue
      case 'Dot Ball': return '#94a3b8' // Gray
      default: return '#4ade80' // Green for singles/runs
    }
  }

  return (
    <group position={position}>
      <mesh
        onPointerOver={(e) => { e.stopPropagation(); setHover(true) }}
        onPointerOut={(e) => setHover(false)}
      >
        <sphereGeometry args={[hovered ? 0.3 : 0.15, 16, 16]} />
        <meshStandardMaterial 
          color={getColor()} 
          emissive={getColor()} 
          emissiveIntensity={hovered ? 2 : 0.5} 
        />
      </mesh>
      
      {/* HTML tooltip on hover */}
      {hovered && (
        <Html distanceFactor={15} zIndexRange={[100, 0]}>
          <div style={{
            background: 'rgba(15, 23, 42, 0.9)',
            border: `1px solid ${getColor()}`,
            padding: '10px',
            borderRadius: '8px',
            color: 'white',
            width: '150px',
            pointerEvents: 'none',
            backdropFilter: 'blur(4px)'
          }}>
            <div style={{fontWeight: 'bold', marginBottom: '4px', color: getColor()}}>{outcome}</div>
            <div style={{fontSize: '12px', color: '#94a3b8'}}>Bowler: {bowler}</div>
            <div style={{fontSize: '12px', color: '#94a3b8'}}>Speed: {speed} km/h</div>
          </div>
        </Html>
      )}
    </group>
  )
}

function CricketPitch() {
  return (
    <group>
      {/* Grass Outfield */}
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.1, 0]} receiveShadow>
        <planeGeometry args={[100, 100]} />
        <meshStandardMaterial color="#0f3d1f" />
      </mesh>
      
      {/* The Pitch itself (20.12m long, 3.05m wide) */}
      <mesh rotation={[-Math.PI / 2, 0, 0]} receiveShadow>
        <planeGeometry args={[3.05, 20.12]} />
        <meshStandardMaterial color="#c2b280" />
      </mesh>
      
      {/* Crease Lines */}
      {/* Popping Crease (1.22m in front of stumps) */}
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0.01, 8.84]}>
        <planeGeometry args={[3.66, 0.05]} />
        <meshBasicMaterial color="white" />
      </mesh>
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0.01, -8.84]}>
        <planeGeometry args={[3.66, 0.05]} />
        <meshBasicMaterial color="white" />
      </mesh>
      
      {/* Bowling Crease (in line with stumps) */}
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0.01, 10.06]}>
        <planeGeometry args={[2.64, 0.05]} />
        <meshBasicMaterial color="white" />
      </mesh>
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0.01, -10.06]}>
        <planeGeometry args={[2.64, 0.05]} />
        <meshBasicMaterial color="white" />
      </mesh>

      {/* Stumps (Batsman End) */}
      <group position={[0, 0.35, 10.06]}>
        <mesh position={[-0.11, 0, 0]}><cylinderGeometry args={[0.02, 0.02, 0.71]} /><meshStandardMaterial color="white" /></mesh>
        <mesh position={[0, 0, 0]}><cylinderGeometry args={[0.02, 0.02, 0.71]} /><meshStandardMaterial color="white" /></mesh>
        <mesh position={[0.11, 0, 0]}><cylinderGeometry args={[0.02, 0.02, 0.71]} /><meshStandardMaterial color="white" /></mesh>
      </group>
      
      {/* Stumps (Bowler End) */}
      <group position={[0, 0.35, -10.06]}>
        <mesh position={[-0.11, 0, 0]}><cylinderGeometry args={[0.02, 0.02, 0.71]} /><meshStandardMaterial color="white" /></mesh>
        <mesh position={[0, 0, 0]}><cylinderGeometry args={[0.02, 0.02, 0.71]} /><meshStandardMaterial color="white" /></mesh>
        <mesh position={[0.11, 0, 0]}><cylinderGeometry args={[0.02, 0.02, 0.71]} /><meshStandardMaterial color="white" /></mesh>
      </group>

      {/* Text Labels */}
      <Text position={[0, 0.1, 11]} rotation={[-Math.PI/2, 0, 0]} fontSize={0.5} color="white">
        Batsman End
      </Text>
      <Text position={[0, 0.1, -11]} rotation={[-Math.PI/2, 0, 0]} fontSize={0.5} color="white">
        Bowler End
      </Text>
    </group>
  )
}

export default function PitchMap3D({ team }) {
  const [data, setData] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!team) return;
    setLoading(true)
    axios.get(`${API_BASE}/pitch-map-data?team=${encodeURIComponent(team)}`)
      .then(res => {
        setData(res.data.data || [])
        setLoading(false)
      })
      .catch(err => {
        console.error("Error fetching pitch map data:", err)
        setLoading(false)
      })
  }, [team])

  return (
    <div className="glass-panel" style={{ width: '100%', height: '600px', position: 'relative' }}>
      
      {/* Overlay UI */}
      <div style={{ position: 'absolute', top: 20, left: 20, zIndex: 10, color: 'white' }}>
        <h3 style={{ fontSize: '20px', marginBottom: '8px' }}>3D Bowling Length Analysis</h3>
        <p style={{ color: 'var(--text-secondary)' }}>Top 5 Bowlers for {team}</p>
        
        <div style={{ display: 'flex', gap: '16px', marginTop: '16px', fontSize: '12px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <div style={{ width: 12, height: 12, borderRadius: '50%', background: '#f43f5e' }}></div> Wicket
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <div style={{ width: 12, height: 12, borderRadius: '50%', background: '#38bdf8' }}></div> Boundary
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <div style={{ width: 12, height: 12, borderRadius: '50%', background: '#94a3b8' }}></div> Dot
          </div>
        </div>
      </div>

      {loading && (
        <div style={{ position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)', color: 'white', zIndex: 10 }}>
          Generating 3D Models...
        </div>
      )}

      {/* Three.js Canvas */}
      {!loading && (
        <Canvas camera={{ position: [0, 8, 15], fov: 45 }} shadows>
          <color attach="background" args={['#070B19']} />
          <ambientLight intensity={0.5} />
          <directionalLight position={[10, 10, 5]} intensity={1} castShadow />
          <pointLight position={[-10, 10, -10]} intensity={0.5} color="#0ea5e9" />
          
          <CricketPitch />
          
          {data.map((point, i) => (
            <PitchPoint 
              key={i} 
              position={[point.x, point.y, point.z]} 
              outcome={point.outcome}
              bowler={point.bowler}
              speed={point.speed}
            />
          ))}

          {/* Smooth Controls */}
          <OrbitControls 
            enablePan={false} 
            maxPolarAngle={Math.PI / 2 - 0.1} // Prevent looking from under the ground
            minDistance={5}
            maxDistance={30}
          />
        </Canvas>
      )}
    </div>
  )
}

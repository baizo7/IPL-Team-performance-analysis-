import React, { useState, useEffect } from 'react'
import { Canvas } from '@react-three/fiber'
import { OrbitControls, Text, Html, Line } from '@react-three/drei'
import axios from 'axios'

const API_BASE = 'http://localhost:8000/api'

function ShotTrajectory({ point }) {
  const [hovered, setHover] = useState(false)
  
  // Color mapping based on runs
  const getColor = () => {
    switch(point.runs) {
      case 6: return '#f43f5e' // Red
      case 4: return '#d946ef' // Purple
      case 3: return '#f59e0b' // Orange
      case 2: return '#3b82f6' // Blue
      default: return '#4ade80' // Green
    }
  }

  const color = getColor()
  
  // Start point is the center of the pitch (0,0,0)
  // We'll lift the arc slightly to look like a ball trajectory
  // Simple quadratic bezier curve approximation for 3D trajectory
  const points = []
  const segments = 20
  for (let i = 0; i <= segments; i++) {
    const t = i / segments
    const x = point.x * t
    const z = point.z * t
    // Parabolic arc for y: y = 4 * height * t * (1 - t)
    const maxHeight = point.runs === 6 ? 15 : (point.runs === 4 ? 2 : 0.5)
    const y = 4 * maxHeight * t * (1 - t)
    points.push([x, y, z])
  }

  return (
    <group>
      {/* The Line Trajectory */}
      <Line 
        points={points} 
        color={hovered ? 'white' : color} 
        lineWidth={hovered ? 3 : 1.5} 
        transparent 
        opacity={0.8}
        onPointerOver={(e) => { e.stopPropagation(); setHover(true) }}
        onPointerOut={(e) => setHover(false)}
      />
      
      {/* The Ball Landing Point */}
      <mesh position={[point.x, point.y, point.z]}>
        <sphereGeometry args={[hovered ? 1.5 : 0.8, 16, 16]} />
        <meshStandardMaterial color={color} emissive={color} emissiveIntensity={hovered ? 2 : 0.5} />
      </mesh>
      
      {/* HTML tooltip on hover */}
      {hovered && (
        <Html position={[point.x, point.y + 2, point.z]} distanceFactor={60} zIndexRange={[100, 0]}>
          <div style={{
            background: 'rgba(15, 23, 42, 0.9)',
            border: `1px solid ${color}`,
            padding: '10px',
            borderRadius: '8px',
            color: 'white',
            width: '120px',
            pointerEvents: 'none',
            backdropFilter: 'blur(4px)'
          }}>
            <div style={{fontWeight: 'bold', marginBottom: '4px', color: color}}>{point.runs} Runs</div>
            <div style={{fontSize: '12px', color: '#94a3b8'}}>{point.batter}</div>
          </div>
        </Html>
      )}
    </group>
  )
}

function GroundBoundary() {
  return (
    <group>
      {/* Grass Outfield */}
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.1, 0]} receiveShadow>
        <cylinderGeometry args={[85, 85, 0.1, 64]} />
        <meshStandardMaterial color="#0f3d1f" />
      </mesh>
      
      {/* 30-Yard Circle */}
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0, 0]}>
        <ringGeometry args={[27.4, 27.8, 64]} />
        <meshBasicMaterial color="rgba(255,255,255,0.3)" side={2} transparent />
      </mesh>

      {/* Boundary Rope */}
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0.2, 0]}>
        <torusGeometry args={[80, 0.3, 16, 100]} />
        <meshStandardMaterial color="white" />
      </mesh>
      
      {/* The Pitch */}
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0.05, 0]} receiveShadow>
        <planeGeometry args={[3.05, 20.12]} />
        <meshStandardMaterial color="#c2b280" />
      </mesh>

      {/* Ground Labels */}
      <Text position={[0, 0.5, 90]} rotation={[-Math.PI/2, 0, Math.PI]} fontSize={4} color="rgba(255,255,255,0.5)">
        Straight
      </Text>
      <Text position={[90, 0.5, 0]} rotation={[-Math.PI/2, 0, Math.PI/2]} fontSize={4} color="rgba(255,255,255,0.5)">
        Cover / Mid Wicket
      </Text>
      <Text position={[-90, 0.5, 0]} rotation={[-Math.PI/2, 0, -Math.PI/2]} fontSize={4} color="rgba(255,255,255,0.5)">
        Square Leg / Point
      </Text>
    </group>
  )
}

export default function WagonWheel3D({ team }) {
  const [data, setData] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!team) return;
    setLoading(true)
    axios.get(`${API_BASE}/wagon-wheel-data?team=${encodeURIComponent(team)}`)
      .then(res => {
        setData(res.data.data || [])
        setLoading(false)
      })
      .catch(err => {
        console.error("Error fetching wagon wheel data:", err)
        setLoading(false)
      })
  }, [team])

  return (
    <div className="glass-panel" style={{ width: '100%', height: '600px', position: 'relative' }}>
      
      {/* Overlay UI */}
      <div style={{ position: 'absolute', top: 20, left: 20, zIndex: 10, color: 'white' }}>
        <h3 style={{ fontSize: '20px', marginBottom: '8px' }}>3D Wagon Wheel</h3>
        <p style={{ color: 'var(--text-secondary)' }}>Scoring Trajectories for {team}</p>
        
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginTop: '16px', fontSize: '12px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <div style={{ width: 12, height: 12, borderRadius: '50%', background: '#f43f5e' }}></div> 6 Runs (Over Boundary)
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <div style={{ width: 12, height: 12, borderRadius: '50%', background: '#d946ef' }}></div> 4 Runs (Boundary)
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <div style={{ width: 12, height: 12, borderRadius: '50%', background: '#f59e0b' }}></div> 3 Runs
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <div style={{ width: 12, height: 12, borderRadius: '50%', background: '#3b82f6' }}></div> 2 Runs
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <div style={{ width: 12, height: 12, borderRadius: '50%', background: '#4ade80' }}></div> 1 Run
          </div>
        </div>
      </div>

      {loading && (
        <div style={{ position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)', color: 'white', zIndex: 10 }}>
          Calculating Trajectories...
        </div>
      )}

      {/* Three.js Canvas */}
      {!loading && (
        <Canvas camera={{ position: [0, 60, 100], fov: 60 }} shadows>
          <color attach="background" args={['#070B19']} />
          <ambientLight intensity={0.6} />
          <directionalLight position={[50, 100, 50]} intensity={1.5} castShadow />
          
          <GroundBoundary />
          
          {data.map((point, i) => (
            <ShotTrajectory key={i} point={point} />
          ))}

          {/* Smooth Controls */}
          <OrbitControls 
            enablePan={false} 
            maxPolarAngle={Math.PI / 2 - 0.1} // Prevent looking from under the ground
            minDistance={20}
            maxDistance={150}
          />
        </Canvas>
      )}
    </div>
  )
}

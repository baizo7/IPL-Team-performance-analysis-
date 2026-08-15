import React, { useRef, useState, useEffect } from 'react'
import { Canvas } from '@react-three/fiber'
import { OrbitControls, Text, Html } from '@react-three/drei'
import api from '../utils/api'
import { useFilters } from '../context/FilterContext'
import { getTeamTheme } from '../utils/teamColors'

function PitchPoint({ position, outcome, bowler, speed }) {
  const [hovered, setHover] = useState(false)
  
  const getColor = () => {
    switch(outcome) {
      case 'Wicket': return '#f43f5e'
      case 'Boundary': return '#38bdf8'
      case 'Dot Ball': return '#94a3b8'
      default: return '#4ade80'
    }
  }

  const color = getColor()

  return (
    <group position={position}>
      <mesh
        onPointerOver={(e) => { e.stopPropagation(); setHover(true) }}
        onPointerOut={() => setHover(false)}
      >
        <sphereGeometry args={[hovered ? 0.3 : 0.15, 16, 16]} />
        <meshStandardMaterial 
          color={color} 
          emissive={color} 
          emissiveIntensity={hovered ? 2 : 0.5} 
        />
      </mesh>
      
      {hovered && (
        <Html distanceFactor={15} zIndexRange={[100, 0]}>
          <div style={{
            background: 'rgba(15, 23, 42, 0.95)',
            border: `1px solid ${color}`,
            padding: '8px 12px',
            borderRadius: '8px',
            color: 'white',
            width: '150px',
            pointerEvents: 'none',
            backdropFilter: 'blur(6px)',
            fontSize: '12px'
          }}>
            <div style={{fontWeight: 'bold', marginBottom: '4px', color: color}}>{outcome || 'Delivery'}</div>
            <div style={{color: '#94a3b8'}}>Bowler: {bowler}</div>
            <div style={{color: '#94a3b8'}}>Speed: {speed} km/h</div>
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
      
      {/* The Pitch (20.12m long, 3.05m wide) */}
      <mesh rotation={[-Math.PI / 2, 0, 0]} receiveShadow>
        <planeGeometry args={[3.05, 20.12]} />
        <meshStandardMaterial color="#c2b280" />
      </mesh>
      
      {/* Length Zones Markers */}
      {/* Yorker (0-2m) */}
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0.005, 9.0]}>
        <planeGeometry args={[3.05, 2]} />
        <meshBasicMaterial color="rgba(244, 63, 94, 0.15)" side={2} transparent />
      </mesh>
      {/* Full (2-6m) */}
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0.005, 5.0]}>
        <planeGeometry args={[3.05, 4]} />
        <meshBasicMaterial color="rgba(56, 189, 248, 0.15)" side={2} transparent />
      </mesh>
      {/* Good Length (6-8m) */}
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0.005, -1.0]}>
        <planeGeometry args={[3.05, 4]} />
        <meshBasicMaterial color="rgba(74, 222, 128, 0.15)" side={2} transparent />
      </mesh>
      
      {/* Crease Lines */}
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0.01, 8.84]}>
        <planeGeometry args={[3.66, 0.05]} />
        <meshBasicMaterial color="white" />
      </mesh>
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0.01, -8.84]}>
        <planeGeometry args={[3.66, 0.05]} />
        <meshBasicMaterial color="white" />
      </mesh>
      
      {/* Stumps */}
      <group position={[0, 0.35, 10.06]}>
        {[-0.11, 0, 0.11].map((x, i) => (
          <mesh key={i} position={[x, 0, 0]}>
            <cylinderGeometry args={[0.02, 0.02, 0.71]} />
            <meshStandardMaterial color="white" />
          </mesh>
        ))}
      </group>

      <Text position={[0, 0.1, 11]} rotation={[-Math.PI/2, 0, 0]} fontSize={0.5} color="white">
        Batter End
      </Text>
      <Text position={[0, 0.1, -11]} rotation={[-Math.PI/2, 0, 0]} fontSize={0.5} color="white">
        Bowler End
      </Text>
    </group>
  )
}

export default function PitchMap3D() {
  const { selectedTeam, selectedBowlerType, selectedPhase } = useFilters();
  const theme = getTeamTheme(selectedTeam);

  const [data, setData] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    let query = `?team=${encodeURIComponent(selectedTeam)}`
    if (selectedBowlerType && selectedBowlerType !== 'All') query += `&bowler_type=${encodeURIComponent(selectedBowlerType)}`
    if (selectedPhase && selectedPhase !== 'All Phases') query += `&phase=${encodeURIComponent(selectedPhase)}`

    api.get(`/pitch-map-data${query}`)
      .then(res => {
        setData(res.data.data || [])
        setLoading(false)
      })
      .catch(err => {
        console.error("Error fetching pitch map data:", err)
        setLoading(false)
      })
  }, [selectedTeam, selectedBowlerType, selectedPhase])

  return (
    <div className="glass-panel" style={{ width: '100%', height: '600px', position: 'relative', borderRadius: '16px', overflow: 'hidden' }}>
      <div style={{ position: 'absolute', top: 20, left: 20, zIndex: 10, color: 'white' }}>
        <h3 style={{ fontSize: '20px', marginBottom: '4px' }}>3D Bowling Length & Pitch Analysis</h3>
        <p style={{ color: 'var(--text-secondary)', fontSize: '13px' }}>Hawk-Eye Delivery Heatmap ({selectedTeam})</p>
        
        <div style={{ display: 'flex', gap: '16px', marginTop: '14px', fontSize: '12px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ width: 10, height: 10, borderRadius: '50%', background: '#f43f5e' }}></span> Wicket
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ width: 10, height: 10, borderRadius: '50%', background: '#38bdf8' }}></span> Boundary
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ width: 10, height: 10, borderRadius: '50%', background: '#4ade80' }}></span> Runs/Single
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ width: 10, height: 10, borderRadius: '50%', background: '#94a3b8' }}></span> Dot Ball
          </div>
        </div>
      </div>

      {loading ? (
        <div className="loading-spinner" style={{ position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)', zIndex: 10 }}>
          Simulating 3D Pitch Physics...
        </div>
      ) : (
        <Canvas camera={{ position: [0, 8, 16], fov: 45 }} shadows>
          <color attach="background" args={['#070B19']} />
          <ambientLight intensity={0.6} />
          <directionalLight position={[10, 10, 5]} intensity={1.2} castShadow />
          <pointLight position={[-10, 10, -10]} intensity={0.5} color={theme.accent} />
          
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

          <OrbitControls 
            enablePan={false} 
            maxPolarAngle={Math.PI / 2 - 0.1} 
            minDistance={5}
            maxDistance={35}
          />
        </Canvas>
      )}
    </div>
  )
}

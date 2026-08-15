import React, { useState, useEffect } from 'react'
import { Canvas } from '@react-three/fiber'
import { OrbitControls, Text, Html, Line } from '@react-three/drei'
import api from '../utils/api'
import { useFilters } from '../context/FilterContext'
import { getTeamTheme } from '../utils/teamColors'

function ShotTrajectory({ point }) {
  const [hovered, setHover] = useState(false)
  
  const getColor = () => {
    switch(point.runs) {
      case 6: return '#f43f5e'
      case 4: return '#d946ef'
      case 3: return '#f59e0b'
      case 2: return '#3b82f6'
      default: return '#4ade80'
    }
  }

  const color = getColor()
  
  const points = []
  const segments = 24
  const apexHeight = point.apex_y || (point.runs === 6 ? 18.0 : (point.runs === 4 ? 3.0 : 0.8))
  for (let i = 0; i <= segments; i++) {
    const t = i / segments
    const x = point.x * t
    const z = point.z * t
    const y = 4 * apexHeight * t * (1 - t)
    points.push([x, y, z])
  }

  return (
    <group>
      <Line 
        points={points} 
        color={hovered ? 'white' : color} 
        lineWidth={hovered ? 3.5 : 1.5} 
        transparent 
        opacity={0.85}
        onPointerOver={(e) => { e.stopPropagation(); setHover(true) }}
        onPointerOut={() => setHover(false)}
      />
      
      <mesh position={[point.x, point.y, point.z]}>
        <sphereGeometry args={[hovered ? 1.5 : 0.8, 16, 16]} />
        <meshStandardMaterial color={color} emissive={color} emissiveIntensity={hovered ? 2 : 0.5} />
      </mesh>
      
      {hovered && (
        <Html position={[point.x, point.y + 2, point.z]} distanceFactor={60} zIndexRange={[100, 0]}>
          <div style={{
            background: 'rgba(15, 23, 42, 0.95)',
            border: `1px solid ${color}`,
            padding: '8px 12px',
            borderRadius: '8px',
            color: 'white',
            width: '130px',
            pointerEvents: 'none',
            backdropFilter: 'blur(6px)',
            fontSize: '12px'
          }}>
            <div style={{fontWeight: 'bold', marginBottom: '2px', color: color}}>{point.runs} Runs</div>
            <div style={{color: '#94a3b8'}}>{point.batter}</div>
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
        Long Off / Long On
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

export default function WagonWheel3D() {
  const { selectedTeam, selectedPhase } = useFilters();
  const theme = getTeamTheme(selectedTeam);

  const [data, setData] = useState([])
  const [loading, setLoading] = useState(true)
  const [activeFilter, setActiveFilter] = useState(null) // null = all, or 'boundaries', 'twos', 'threes', 'singles'
  const [selectedShotType, setSelectedShotType] = useState(null) // Pop-up modal state
  const [isTabOpen, setIsTabOpen] = useState(false) // Small tab toggle state

  useEffect(() => {
    setLoading(true)
    let query = `?team=${encodeURIComponent(selectedTeam)}`
    if (selectedPhase && selectedPhase !== 'All Phases') query += `&phase=${encodeURIComponent(selectedPhase)}`

    api.get(`/wagon-wheel-data${query}`)
      .then(res => {
        setData(res.data.data || [])
        setLoading(false)
      })
      .catch(err => {
        console.error("Error fetching wagon wheel data:", err)
        setLoading(false)
      })
  }, [selectedTeam, selectedPhase])

  const counts = {
    boundaries: data.filter(d => d.runs === 4 || d.runs === 6).length,
    twos: data.filter(d => d.runs === 2).length,
    threes: data.filter(d => d.runs === 3).length,
    singles: data.filter(d => d.runs === 1).length,
  }

  const handleLegendClick = (typeKey, runsFilter, title) => {
    setIsTabOpen(false)
    if (activeFilter === typeKey) {
      setActiveFilter(null)
      setSelectedShotType(null)
    } else {
      setActiveFilter(typeKey)
      const subset = data.filter(d => runsFilter.includes(d.runs))
      const totalRuns = subset.reduce((acc, curr) => acc + (curr.runs || 0), 0)
      const avgDist = subset.length > 0 ? (subset.reduce((acc, curr) => acc + (curr.distance || 65), 0) / subset.length).toFixed(1) : 65

      setSelectedShotType({
        title,
        count: subset.length,
        percentage: data.length > 0 ? ((subset.length / data.length) * 100).toFixed(1) : 0,
        totalRuns,
        avgDist
      })
    }
  }

  const filteredData = activeFilter
    ? data.filter(d => {
        if (activeFilter === 'boundaries') return d.runs === 4 || d.runs === 6
        if (activeFilter === 'twos') return d.runs === 2
        if (activeFilter === 'threes') return d.runs === 3
        if (activeFilter === 'singles') return d.runs === 1
        return true
      })
    : data

  return (
    <div className="glass-panel" style={{ width: '100%', height: '600px', position: 'relative', borderRadius: '16px', overflow: 'hidden' }}>
      {/* Title */}
      <div style={{ position: 'absolute', top: 20, left: 20, zIndex: 10, color: 'white' }}>
        <h3 style={{ fontSize: '20px', marginBottom: '4px' }}>3D Wagon Wheel Shot Directions</h3>
        <p style={{ color: 'var(--text-secondary)', fontSize: '13px' }}>Batting Trajectories ({selectedTeam})</p>
      </div>

      {/* Small Tab Toggle Button (Top Right) */}
      <div 
        onClick={() => setIsTabOpen(!isTabOpen)}
        style={{
          position: 'absolute', top: 20, right: 20, zIndex: 110,
          background: 'rgba(15, 23, 42, 0.9)', padding: '8px 14px', borderRadius: '20px',
          color: 'white', fontSize: '12px', fontWeight: 'bold', border: '1px solid rgba(56, 189, 248, 0.5)',
          cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '8px', backdropFilter: 'blur(10px)',
          boxShadow: '0 6px 20px rgba(0,0,0,0.4)', transition: 'all 0.2s'
        }}
      >
        <span>🎯 {activeFilter ? activeFilter.toUpperCase() : 'SHOT TYPES'}</span>
        <span style={{ fontSize: '10px', color: '#38bdf8' }}>{isTabOpen ? '▲' : '▼'}</span>
      </div>
        
      {/* Popped-Open Small Tab Menu */}
      {isTabOpen && (
        <div style={{
          position: 'absolute', top: 60, right: 20, zIndex: 105,
          background: 'rgba(15, 23, 42, 0.95)', padding: '12px 14px',
          borderRadius: '14px', backdropFilter: 'blur(16px)',
          border: '1px solid rgba(255,255,255,0.2)', width: '210px',
          boxShadow: '0 10px 40px rgba(0,0,0,0.6)'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px', borderBottom: '1px solid rgba(255,255,255,0.2)', paddingBottom: '4px' }}>
            <span style={{ fontSize: '11px', fontWeight: 'bold', color: '#94a3b8', letterSpacing: '0.5px' }}>FILTER SHOTS</span>
            {activeFilter && (
              <span 
                onClick={() => { setActiveFilter(null); setSelectedShotType(null); setIsTabOpen(false); }}
                style={{ fontSize: '10px', color: '#38bdf8', cursor: 'pointer', background: 'rgba(56,189,248,0.2)', padding: '2px 6px', borderRadius: '4px' }}
              >
                Reset
              </span>
            )}
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', fontSize: '12px', color: 'white' }}>
            <div 
              onClick={() => handleLegendClick('boundaries', [4, 6], 'Boundaries (4s & 6s)')}
              style={{
                display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                padding: '5px 8px', borderRadius: '6px', cursor: 'pointer',
                background: activeFilter === 'boundaries' ? 'rgba(244, 63, 94, 0.25)' : 'transparent',
                border: activeFilter === 'boundaries' ? '1px solid #f43f5e' : '1px solid transparent',
                opacity: activeFilter && activeFilter !== 'boundaries' ? 0.4 : 1,
                transition: 'all 0.2s'
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <span style={{ width: 10, height: 10, borderRadius: '50%', background: '#f43f5e', boxShadow: '0 0 6px #f43f5e' }}></span> Boundaries (4s & 6s)
              </div>
              <span style={{ fontSize: '10px', background: 'rgba(255,255,255,0.15)', padding: '1px 5px', borderRadius: '8px' }}>{counts.boundaries}</span>
            </div>

            <div 
              onClick={() => handleLegendClick('twos', [2], 'Twos (2 runs)')}
              style={{
                display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                padding: '5px 8px', borderRadius: '6px', cursor: 'pointer',
                background: activeFilter === 'twos' ? 'rgba(59, 130, 246, 0.25)' : 'transparent',
                border: activeFilter === 'twos' ? '1px solid #3b82f6' : '1px solid transparent',
                opacity: activeFilter && activeFilter !== 'twos' ? 0.4 : 1,
                transition: 'all 0.2s'
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <span style={{ width: 10, height: 10, borderRadius: '50%', background: '#3b82f6', boxShadow: '0 0 6px #3b82f6' }}></span> Twos (2 runs)
              </div>
              <span style={{ fontSize: '10px', background: 'rgba(255,255,255,0.15)', padding: '1px 5px', borderRadius: '8px' }}>{counts.twos}</span>
            </div>

            <div 
              onClick={() => handleLegendClick('threes', [3], 'Threes (3 runs)')}
              style={{
                display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                padding: '5px 8px', borderRadius: '6px', cursor: 'pointer',
                background: activeFilter === 'threes' ? 'rgba(245, 158, 11, 0.25)' : 'transparent',
                border: activeFilter === 'threes' ? '1px solid #f59e0b' : '1px solid transparent',
                opacity: activeFilter && activeFilter !== 'threes' ? 0.4 : 1,
                transition: 'all 0.2s'
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <span style={{ width: 10, height: 10, borderRadius: '50%', background: '#f59e0b', boxShadow: '0 0 6px #f59e0b' }}></span> Threes (3 runs)
              </div>
              <span style={{ fontSize: '10px', background: 'rgba(255,255,255,0.15)', padding: '1px 5px', borderRadius: '8px' }}>{counts.threes}</span>
            </div>

            <div 
              onClick={() => handleLegendClick('singles', [1], 'Singles (1 run)')}
              style={{
                display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                padding: '5px 8px', borderRadius: '6px', cursor: 'pointer',
                background: activeFilter === 'singles' ? 'rgba(74, 222, 128, 0.25)' : 'transparent',
                border: activeFilter === 'singles' ? '1px solid #4ade80' : '1px solid transparent',
                opacity: activeFilter && activeFilter !== 'singles' ? 0.4 : 1,
                transition: 'all 0.2s'
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <span style={{ width: 10, height: 10, borderRadius: '50%', background: '#4ade80', boxShadow: '0 0 6px #4ade80' }}></span> Singles (1 run)
              </div>
              <span style={{ fontSize: '10px', background: 'rgba(255,255,255,0.15)', padding: '1px 5px', borderRadius: '8px' }}>{counts.singles}</span>
            </div>
          </div>
        </div>
      )}

      {/* Pop-Up Modal */}
      {selectedShotType && (
        <div style={{
          position: 'absolute', bottom: 20, left: 20, zIndex: 100,
          background: 'rgba(15, 23, 42, 0.95)', border: '1px solid #38bdf8',
          borderRadius: '12px', padding: '14px 18px', color: 'white',
          width: '260px', backdropFilter: 'blur(12px)', boxShadow: '0 10px 30px rgba(0,0,0,0.7)'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px', borderBottom: '1px solid rgba(255,255,255,0.15)', paddingBottom: '6px' }}>
            <span style={{ fontWeight: 'bold', fontSize: '13px' }}>💥 {selectedShotType.title}</span>
            <span onClick={() => setSelectedShotType(null)} style={{ cursor: 'pointer', color: '#94a3b8' }}>&times;</span>
          </div>
          <div style={{ fontSize: '12px', display: 'flex', flexDirection: 'column', gap: '4px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}><span style={{ color: '#94a3b8' }}>Total Shots:</span> <b>{selectedShotType.count} ({selectedShotType.percentage}%)</b></div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}><span style={{ color: '#94a3b8' }}>Total Runs:</span> <b>{selectedShotType.totalRuns} runs</b></div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}><span style={{ color: '#94a3b8' }}>Avg Distance:</span> <b>{selectedShotType.avgDist} m</b></div>
          </div>
        </div>
      )}

      {loading ? (
        <div className="loading-spinner" style={{ position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)', zIndex: 10 }}>
          Tracing Parabolic Trajectories...
        </div>
      ) : (
        <Canvas camera={{ position: [0, 60, 100], fov: 60 }} shadows>
          <color attach="background" args={['#070B19']} />
          <ambientLight intensity={0.6} />
          <directionalLight position={[50, 100, 50]} intensity={1.5} castShadow />
          
          <GroundBoundary />
          
          {filteredData.map((point, i) => (
            <ShotTrajectory key={i} point={point} />
          ))}

          <OrbitControls 
            enablePan={false} 
            maxPolarAngle={Math.PI / 2 - 0.1} 
            minDistance={20}
            maxDistance={160}
          />
        </Canvas>
      )}
    </div>
  )
}

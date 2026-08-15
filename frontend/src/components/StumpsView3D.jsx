import React, { useState, useEffect } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, Text, Html, Line } from '@react-three/drei';
import api from '../utils/api';
import { useFilters } from '../context/FilterContext';
import { getTeamTheme } from '../utils/teamColors';

function DeliveryTrajectory({ ball }) {
  const [hovered, setHover] = useState(false);
  
  // Color based on height/length
  const color = ball.y > 1.2 ? '#f43f5e' : (ball.y < 0.5 ? '#38bdf8' : '#4ade80');

  // Delivery trajectory from release point (Z=-10, Y=2) to stump target (Z=10, Y=ball.y, X=ball.x)
  const points = [
    [0, 2.1, -10],
    [ball.x * 0.5, 0.2, 5], // pitch bounce point
    [ball.x, ball.y, 10]    // stumps target point
  ];

  return (
    <group>
      <Line 
        points={points} 
        color={hovered ? '#ffffff' : color} 
        lineWidth={hovered ? 3 : 1.5}
        transparent 
        opacity={0.85}
        onPointerOver={(e) => { e.stopPropagation(); setHover(true); }}
        onPointerOut={() => setHover(false)}
      />
      <mesh position={[ball.x, ball.y, 10]}>
        <sphereGeometry args={[hovered ? 0.25 : 0.12, 16, 16]} />
        <meshStandardMaterial color={color} emissive={color} emissiveIntensity={hovered ? 2 : 0.6} />
      </mesh>

      {hovered && (
        <Html position={[ball.x, ball.y + 0.3, 10]} distanceFactor={15}>
          <div style={{
            background: 'rgba(15, 23, 42, 0.95)',
            border: `1px solid ${color}`,
            padding: '8px 12px',
            borderRadius: '6px',
            color: 'white',
            width: '140px',
            pointerEvents: 'none',
            fontSize: '12px'
          }}>
            <div style={{ fontWeight: 'bold', color: color }}>{ball.length}</div>
            <div>Bowler: {ball.bowler}</div>
            <div>Speed: {ball.speed} km/h</div>
          </div>
        </Html>
      )}
    </group>
  );
}

function StumpsTargetArea() {
  return (
    <group position={[0, 0, 10]}>
      {/* 3 Stumps */}
      {[-0.11, 0, 0.11].map((xOffset, i) => (
        <mesh key={i} position={[xOffset, 0.35, 0]}>
          <cylinderGeometry args={[0.02, 0.02, 0.71]} />
          <meshStandardMaterial color="#f59e0b" emissive="#f59e0b" emissiveIntensity={0.2} />
        </mesh>
      ))}

      {/* Bails */}
      <mesh position={[0, 0.72, 0]}>
        <boxGeometry args={[0.26, 0.03, 0.03]} />
        <meshStandardMaterial color="#f59e0b" />
      </mesh>

      {/* Target Grid Backing */}
      <mesh position={[0, 0.5, 0.05]}>
        <planeGeometry args={[1.5, 1.2]} />
        <meshBasicMaterial color="rgba(255,255,255,0.05)" side={2} transparent />
      </mesh>
    </group>
  );
}

export default function StumpsView3D() {
  const { selectedTeam, selectedPhase } = useFilters();
  const theme = getTeamTheme(selectedTeam);
  const [deliveries, setDeliveries] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    const phaseQuery = selectedPhase && selectedPhase !== 'All Phases' ? `&phase=${encodeURIComponent(selectedPhase)}` : '';
    api.get(`/stumps-view-data?team=${encodeURIComponent(selectedTeam)}${phaseQuery}`)
      .then(res => {
        setDeliveries(res.data.data || []);
        setLoading(false);
      })
      .catch(err => {
        console.error("Error fetching stumps view data:", err);
        setLoading(false);
      });
  }, [selectedTeam, selectedPhase]);

  return (
    <div className="glass-panel" style={{ width: '100%', height: '600px', position: 'relative', borderRadius: '16px', overflow: 'hidden' }}>
      <div style={{ position: 'absolute', top: 20, left: 20, zIndex: 10, color: 'white' }}>
        <h3 style={{ fontSize: '20px', marginBottom: '4px' }}>3D Stumps & Release Trajectories</h3>
        <p style={{ color: 'var(--text-secondary)', fontSize: '13px' }}>Hawk-Eye Delivery Heights for {selectedTeam}</p>
        
        <div style={{ display: 'flex', gap: '12px', marginTop: '12px', fontSize: '12px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ width: 10, height: 10, borderRadius: '50%', background: '#f43f5e' }}></span> High Bouncer
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ width: 10, height: 10, borderRadius: '50%', background: '#4ade80' }}></span> Good Height
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ width: 10, height: 10, borderRadius: '50%', background: '#38bdf8' }}></span> Yorker / Low
          </div>
        </div>
      </div>

      {loading ? (
        <div className="loading-spinner" style={{ position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)', zIndex: 10 }}>
          Processing Delivery Angles...
        </div>
      ) : (
        <Canvas camera={{ position: [0, 2, 18], fov: 50 }}>
          <color attach="background" args={['#050814']} />
          <ambientLight intensity={0.6} />
          <directionalLight position={[10, 10, 10]} intensity={1.2} />

          {/* Pitch surface */}
          <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0, 0]}>
            <planeGeometry args={[3.05, 22]} />
            <meshStandardMaterial color="#c2b280" />
          </mesh>

          <StumpsTargetArea />

          {deliveries.map((ball, idx) => (
            <DeliveryTrajectory key={idx} ball={ball} />
          ))}

          <OrbitControls maxPolarAngle={Math.PI / 2 - 0.05} minDistance={5} maxDistance={25} />
        </Canvas>
      )}
    </div>
  );
}

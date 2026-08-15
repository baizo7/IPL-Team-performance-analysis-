import React, { useState, useEffect } from 'react';
import { AuthProvider } from './context/AuthContext';
import { FilterProvider, useFilters } from './context/FilterContext';
import api from './utils/api';
import Header from './components/Header';
import Sidebar from './components/Sidebar';
import KPICards from './components/KPICards';
import PlayerStats from './components/PlayerStats';
import ChartsDashboard from './components/ChartsDashboard';
import PitchMap3D from './components/PitchMap3D';
import WagonWheel3D from './components/WagonWheel3D';
import StumpsView3D from './components/StumpsView3D';
import FuturePredictor from './components/FuturePredictor';
import LoginModal from './components/LoginModal';
import './App.css';

function MainAppContent() {
  const {
    selectedTeam,
    opponentTeam,
    selectedVenue,
    selectedPhase,
    selectedBowlerType
  } = useFilters();

  const [activeTab, setActiveTab] = useState('performance');
  const [isLoginOpen, setIsLoginOpen] = useState(false);
  const [stats, setStats] = useState([]);
  const [charts, setCharts] = useState(null);
  const [loading, setLoading] = useState(true);

  // Fetch Stats and Charts on filter changes
  useEffect(() => {
    if (!selectedTeam) return;
    setLoading(true);

    const queryParams = new URLSearchParams();
    queryParams.append('team', selectedTeam);
    if (selectedPhase && selectedPhase !== 'All Phases') queryParams.append('phase', selectedPhase);
    if (selectedVenue && selectedVenue !== 'All Venues') queryParams.append('venue', selectedVenue);
    if (opponentTeam) queryParams.append('opponent', opponentTeam);

    // Fetch Player Stats
    api.get(`/player-stats?${queryParams.toString()}`)
      .then(res => setStats(res.data.stats || []))
      .catch(err => console.error("Error fetching stats:", err));

    // Fetch Plotly Dashboard Charts
    api.get(`/charts/dashboard?${queryParams.toString()}`)
      .then(res => {
        setCharts(res.data);
        setLoading(false);
      })
      .catch(err => {
        console.error("Error fetching dashboard charts:", err);
        setLoading(false);
      });
  }, [selectedTeam, opponentTeam, selectedVenue, selectedPhase, selectedBowlerType]);

  return (
    <div className="app-layout">
      {/* Sidebar Controls */}
      <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} />

      {/* Main Content Area */}
      <main className="main-content">
        {/* Top Header */}
        <Header onOpenLogin={() => setIsLoginOpen(true)} />

        {/* Tab 1: Performance Dashboard */}
        {activeTab === 'performance' && (
          <div className="animate-fade-in">
            <KPICards stats={stats} />
            <PlayerStats stats={stats} loading={loading} />
            <ChartsDashboard charts={charts} loading={loading} />
          </div>
        )}

        {/* Tab 2: 3D Pitch Map */}
        {activeTab === 'pitch' && (
          <div className="animate-fade-in">
            <PitchMap3D />
          </div>
        )}

        {/* Tab 3: 3D Wagon Wheel */}
        {activeTab === 'wagon' && (
          <div className="animate-fade-in">
            <WagonWheel3D />
          </div>
        )}

        {/* Tab 4: 3D Stumps View */}
        {activeTab === 'stumps' && (
          <div className="animate-fade-in">
            <StumpsView3D />
          </div>
        )}

        {/* Tab 5: AI Future Predictor */}
        {activeTab === 'predictor' && (
          <div className="animate-fade-in">
            <FuturePredictor />
          </div>
        )}
      </main>

      {/* OAuth2 Login Modal */}
      <LoginModal isOpen={isLoginOpen} onClose={() => setIsLoginOpen(false)} />
    </div>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <FilterProvider>
        <MainAppContent />
      </FilterProvider>
    </AuthProvider>
  );
}

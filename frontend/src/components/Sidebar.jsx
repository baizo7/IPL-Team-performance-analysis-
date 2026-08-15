import React from 'react';
import { useFilters } from '../context/FilterContext';
import { getTeamTheme } from '../utils/teamColors';
import { Activity, Target, Map, Radio, Filter, Layers, Globe } from 'lucide-react';

export default function Sidebar({ activeTab, setActiveTab }) {
  const {
    teams, seasons, venues,
    selectedTeam, setSelectedTeam,
    opponentTeam, setOpponentTeam,
    selectedVenue, setSelectedVenue,
    selectedPhase, setSelectedPhase,
    selectedBowlerType, setSelectedBowlerType,
    useHawkeye, setUseHawkeye
  } = useFilters();

  const theme = getTeamTheme(selectedTeam);

  return (
    <aside className="app-sidebar glass-panel">
      <div className="sidebar-brand">
        <h2 style={{ fontSize: '20px', fontWeight: 'bold', color: 'white', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Activity color={theme.accent} size={22} /> IPL Analytics
        </h2>
        <span style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>React + FastAPI Engine</span>
      </div>

      {/* Navigation Tabs */}
      <div className="sidebar-section">
        <label className="section-label">NAVIGATE VIEWS</label>
        <div className="nav-tab-list">
          <button 
            className={`nav-tab-btn ${activeTab === 'performance' ? 'active' : ''}`}
            style={activeTab === 'performance' ? { borderColor: theme.accent, background: 'rgba(255,255,255,0.08)' } : {}}
            onClick={() => setActiveTab('performance')}
          >
            <Activity size={16} color={activeTab === 'performance' ? theme.accent : 'gray'} />
            <span>Dashboard & Metrics</span>
          </button>
          
          <button 
            className={`nav-tab-btn ${activeTab === 'pitch' ? 'active' : ''}`}
            style={activeTab === 'pitch' ? { borderColor: theme.accent, background: 'rgba(255,255,255,0.08)' } : {}}
            onClick={() => setActiveTab('pitch')}
          >
            <Target size={16} color={activeTab === 'pitch' ? theme.accent : 'gray'} />
            <span>3D Pitch Maps</span>
          </button>

          <button 
            className={`nav-tab-btn ${activeTab === 'wagon' ? 'active' : ''}`}
            style={activeTab === 'wagon' ? { borderColor: theme.accent, background: 'rgba(255,255,255,0.08)' } : {}}
            onClick={() => setActiveTab('wagon')}
          >
            <Map size={16} color={activeTab === 'wagon' ? theme.accent : 'gray'} />
            <span>3D Wagon Wheels</span>
          </button>

          <button 
            className={`nav-tab-btn ${activeTab === 'stumps' ? 'active' : ''}`}
            style={activeTab === 'stumps' ? { borderColor: theme.accent, background: 'rgba(255,255,255,0.08)' } : {}}
            onClick={() => setActiveTab('stumps')}
          >
            <Layers size={16} color={activeTab === 'stumps' ? theme.accent : 'gray'} />
            <span>3D Stumps & Release</span>
          </button>

          <button 
            className={`nav-tab-btn ${activeTab === 'predictor' ? 'active' : ''}`}
            style={activeTab === 'predictor' ? { borderColor: '#f59e0b', background: 'rgba(245,158,11,0.15)' } : {}}
            onClick={() => setActiveTab('predictor')}
          >
            <Radio size={16} color={activeTab === 'predictor' ? '#f59e0b' : 'gray'} />
            <span>🔮 AI Future Predictor</span>
          </button>
        </div>
      </div>

      {/* Filters Section */}
      <div className="sidebar-section">
        <label className="section-label" style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <Filter size={12} /> TEAMS & COMPARISON
        </label>
        
        <div className="filter-group">
          <label>Primary Franchise</label>
          <select value={selectedTeam} onChange={(e) => setSelectedTeam(e.target.value)}>
            {teams.map(t => <option key={t} value={t}>{t}</option>)}
          </select>
        </div>

        <div className="filter-group">
          <label>Head-to-Head Opponent</label>
          <select value={opponentTeam} onChange={(e) => setOpponentTeam(e.target.value)}>
            <option value="">None (Single Team View)</option>
            {teams.filter(t => t !== selectedTeam).map(t => (
              <option key={t} value={t}>{t}</option>
            ))}
          </select>
        </div>
      </div>

      <div className="sidebar-section">
        <label className="section-label">MATCH FILTERS</label>

        <div className="filter-group">
          <label style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <Globe size={12} /> Venue Stadium
          </label>
          <select value={selectedVenue} onChange={(e) => setSelectedVenue(e.target.value)}>
            {venues.map(v => <option key={v} value={v}>{v}</option>)}
          </select>
        </div>

        <div className="filter-group">
          <label>Match Phase</label>
          <div className="phase-pill-group">
            {['All Phases', 'Powerplay', 'Middle', 'Death'].map(p => (
              <button
                key={p}
                className={`pill-btn ${selectedPhase === p ? 'active' : ''}`}
                style={selectedPhase === p ? { background: theme.primary, borderColor: theme.accent, color: 'white' } : {}}
                onClick={() => setSelectedPhase(p)}
              >
                {p}
              </button>
            ))}
          </div>
        </div>

        <div className="filter-group">
          <label>Bowler Type</label>
          <div className="phase-pill-group">
            {['All', 'Pace', 'Spin'].map(bt => (
              <button
                key={bt}
                className={`pill-btn ${selectedBowlerType === bt ? 'active' : ''}`}
                style={selectedBowlerType === bt ? { background: theme.primary, borderColor: theme.accent, color: 'white' } : {}}
                onClick={() => setSelectedBowlerType(bt)}
              >
                {bt}
              </button>
            ))}
          </div>
        </div>

        <div className="filter-group hawkeye-toggle-group">
          <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
            <Radio size={14} color={useHawkeye ? '#38bdf8' : 'gray'} />
            <span style={{ fontSize: '13px', color: 'white' }}>Real Hawk-Eye Data</span>
          </label>

          <input 
            type="checkbox" 
            checked={useHawkeye} 
            onChange={(e) => setUseHawkeye(e.target.checked)}
            style={{ width: '16px', height: '16px', cursor: 'pointer' }}
          />
        </div>
      </div>
    </aside>
  );
}

import { useState, useEffect } from 'react'
import axios from 'axios'
import { Activity, Users, Map, Target } from 'lucide-react'
import PlotlyChart from 'react-plotly.js'
const Plot = PlotlyChart.default || PlotlyChart;
import PitchMap3D from './components/PitchMap3D'
import WagonWheel3D from './components/WagonWheel3D'

// API base URL - adjust for production
const API_BASE = 'http://localhost:8000/api'

function App() {
  const [teams, setTeams] = useState([])
  const [selectedTeam, setSelectedTeam] = useState('')
  const [opponentTeam, setOpponentTeam] = useState('')
  const [stats, setStats] = useState([])
  const [charts, setCharts] = useState(null)
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState('performance')

  // Fetch Teams on mount
  useEffect(() => {
    axios.get(`${API_BASE}/teams`)
      .then(res => {
        setTeams(res.data.teams)
        if (res.data.teams.length > 0) {
          setSelectedTeam(res.data.teams[0])
          setOpponentTeam(res.data.teams[1])
        }
      })
      .catch(err => console.error("Error fetching teams:", err))
  }, [])

  // Fetch Stats and Charts when team changes
  useEffect(() => {
    if (!selectedTeam) return;
    setLoading(true)
    
    // Fetch Basic Stats
    axios.get(`${API_BASE}/player-stats?team=${encodeURIComponent(selectedTeam)}`)
      .then(res => setStats(res.data.stats))
      .catch(err => console.error("Error fetching stats:", err))
      
    // Fetch Advanced Plotly Charts
    const oppQuery = opponentTeam ? `&opponent=${encodeURIComponent(opponentTeam)}` : ''
    axios.get(`${API_BASE}/charts/dashboard?team=${encodeURIComponent(selectedTeam)}${oppQuery}`)
      .then(res => {
        setCharts(res.data)
        setLoading(false)
      })
      .catch(err => {
        console.error("Error fetching charts:", err)
        setLoading(false)
      })
  }, [selectedTeam, opponentTeam])

  return (
    <div className="app-container">
      {/* Sidebar */}
      <aside className="sidebar">
        <h1 className="gradient-text" style={{ fontSize: '24px', marginBottom: '32px' }}>
          IPL Advanced Analysis
        </h1>
        
        <div style={{ marginBottom: '24px' }}>
          <label style={{ display: 'block', marginBottom: '8px', color: 'var(--text-secondary)' }}>
            Primary Team
          </label>
          <select 
            value={selectedTeam} 
            onChange={(e) => setSelectedTeam(e.target.value)}
          >
            {teams.map(t => (
              <option key={t} value={t}>{t}</option>
            ))}
          </select>
        </div>
        
        <div style={{ marginBottom: '32px' }}>
          <label style={{ display: 'block', marginBottom: '8px', color: 'var(--text-secondary)' }}>
            Compare With
          </label>
          <select 
            value={opponentTeam} 
            onChange={(e) => setOpponentTeam(e.target.value)}
          >
            <option value="">None</option>
            {teams.map(t => (
              <option key={t} value={t}>{t}</option>
            ))}
          </select>
        </div>

        <nav style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          <button 
            className="glass-panel" 
            style={{ padding: '12px', display: 'flex', alignItems: 'center', gap: '12px', color: activeTab === 'performance' ? 'white' : 'var(--text-secondary)', border: activeTab === 'performance' ? '1px solid var(--accent-neon)' : '1px solid transparent', background: activeTab === 'performance' ? 'var(--bg-glass-hover)' : 'transparent' }}
            onClick={() => setActiveTab('performance')}
          >
            <Activity size={18} /> Statistical Analysis
          </button>
          <button 
            className="glass-panel" 
            style={{ padding: '12px', display: 'flex', alignItems: 'center', gap: '12px', color: activeTab === 'pitch' ? 'white' : 'var(--text-secondary)', border: activeTab === 'pitch' ? '1px solid var(--accent-neon)' : '1px solid transparent', background: activeTab === 'pitch' ? 'var(--bg-glass-hover)' : 'transparent' }}
            onClick={() => setActiveTab('pitch')}
          >
            <Target size={18} /> 3D Pitch Maps
          </button>
          <button 
            className="glass-panel" 
            style={{ padding: '12px', display: 'flex', alignItems: 'center', gap: '12px', color: activeTab === 'wagon' ? 'white' : 'var(--text-secondary)', border: activeTab === 'wagon' ? '1px solid var(--accent-neon)' : '1px solid transparent', background: activeTab === 'wagon' ? 'var(--bg-glass-hover)' : 'transparent' }}
            onClick={() => setActiveTab('wagon')}
          >
            <Map size={18} /> 3D Wagon Wheels
          </button>
        </nav>
      </aside>

      {/* Main Content */}
      <main className="main-content">
        <header style={{ marginBottom: '32px' }}>
          <h2 style={{ fontSize: '28px', color: 'white' }}>{selectedTeam || 'Loading...'} Overview</h2>
          <p style={{ color: 'var(--text-secondary)' }}>Advanced Data Analytics & 3D Visualization</p>
        </header>

        {activeTab === 'performance' && (
          <div className="animate-fade-in">
            {/* Top Performers Section */}
            <section style={{ marginBottom: '40px' }}>
              <h3 style={{ marginBottom: '16px', color: 'var(--accent-neon)' }}>Top Run Scorers</h3>
              {loading ? (
                <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-secondary)' }}>Loading stats...</div>
              ) : (
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '20px' }}>
                  {stats.map((player, idx) => (
                    <div key={idx} className="glass-card">
                      <h4 style={{ fontSize: '16px', color: 'white', marginBottom: '12px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{player.batter}</h4>
                      <div style={{ fontSize: '28px', fontWeight: 'bold', color: 'var(--accent-neon)', marginBottom: '8px' }}>{player.runs_off_bat}</div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', color: 'var(--text-secondary)' }}>
                        <span>SR: {player.strike_rate}</span>
                        <span>4s/6s: {player.boundaries}</span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </section>

            {/* Advanced Charts Section */}
            <section>
              <h3 style={{ marginBottom: '16px', color: 'var(--accent-neon)' }}>Advanced Analysis</h3>
              {loading || !charts ? (
                <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-secondary)' }}>Loading charts...</div>
              ) : (
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>
                  
                  {/* Chart 1 */}
                  {charts.runs_distribution && (
                    <div className="glass-panel" style={{ padding: '8px', overflow: 'hidden' }}>
                      <Plot 
                        data={charts.runs_distribution.data} 
                        layout={{...charts.runs_distribution.layout, width: undefined, height: 400}} 
                        useResizeHandler={true}
                        style={{ width: '100%', height: '100%' }}
                        config={{ displayModeBar: false }}
                      />
                    </div>
                  )}

                  {/* Chart 2 */}
                  {charts.strike_rate && (
                    <div className="glass-panel" style={{ padding: '8px', overflow: 'hidden' }}>
                      <Plot 
                        data={charts.strike_rate.data} 
                        layout={{...charts.strike_rate.layout, width: undefined, height: 400}} 
                        useResizeHandler={true}
                        style={{ width: '100%', height: '100%' }}
                        config={{ displayModeBar: false }}
                      />
                    </div>
                  )}

                  {/* Chart 3 */}
                  {charts.runs_progression && (
                    <div className="glass-panel" style={{ padding: '8px', overflow: 'hidden' }}>
                      <Plot 
                        data={charts.runs_progression.data} 
                        layout={{...charts.runs_progression.layout, width: undefined, height: 400}} 
                        useResizeHandler={true}
                        style={{ width: '100%', height: '100%' }}
                        config={{ displayModeBar: false }}
                      />
                    </div>
                  )}

                  {/* Chart 4 */}
                  {charts.wickets && (
                    <div className="glass-panel" style={{ padding: '8px', overflow: 'hidden' }}>
                      <Plot 
                        data={charts.wickets.data} 
                        layout={{...charts.wickets.layout, width: undefined, height: 400}} 
                        useResizeHandler={true}
                        style={{ width: '100%', height: '100%' }}
                        config={{ displayModeBar: false }}
                      />
                    </div>
                  )}
                  
                  {/* Compare Chart */}
                  {charts.boundaries && opponentTeam && (
                    <div className="glass-panel" style={{ padding: '8px', overflow: 'hidden', gridColumn: '1 / -1' }}>
                      <Plot 
                        data={charts.boundaries.data} 
                        layout={{...charts.boundaries.layout, width: undefined, height: 400}} 
                        useResizeHandler={true}
                        style={{ width: '100%', height: '100%' }}
                        config={{ displayModeBar: false }}
                      />
                    </div>
                  )}

                </div>
              )}
            </section>
          </div>
        )}

        {activeTab === 'pitch' && (
          <div className="animate-fade-in">
            <PitchMap3D team={selectedTeam} />
          </div>
        )}

        {activeTab === 'wagon' && (
          <div className="animate-fade-in">
            <WagonWheel3D team={selectedTeam} />
          </div>
        )}

      </main>
    </div>
  )
}

export default App

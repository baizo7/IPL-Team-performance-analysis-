import React from 'react';
import { useFilters } from '../context/FilterContext';
import { getTeamTheme } from '../utils/teamColors';
import { Zap, Award, Flame, Target } from 'lucide-react';

export default function KPICards({ stats }) {
  const { selectedTeam, opponentTeam } = useFilters();
  const theme = getTeamTheme(selectedTeam);

  const totalRuns = stats.reduce((acc, curr) => acc + (curr.runs_off_bat || 0), 0);
  const totalBoundaries = stats.reduce((acc, curr) => acc + (curr.boundaries || 0), 0);
  const topBatter = stats[0] ? stats[0].batter : 'N/A';
  const topSR = stats[0] ? stats[0].strike_rate : '0';

  return (
    <div className="kpi-grid">
      <div className="glass-card kpi-card" style={{ borderLeft: `4px solid ${theme.accent}` }}>
        <div className="kpi-icon" style={{ background: theme.glow }}><Zap color={theme.accent} size={20} /></div>
        <div className="kpi-content">
          <span className="kpi-label">Top Batter Runs</span>
          <span className="kpi-value" style={{ color: theme.accent }}>{totalRuns}</span>
        </div>
      </div>

      <div className="glass-card kpi-card" style={{ borderLeft: `4px solid #38bdf8` }}>
        <div className="kpi-icon" style={{ background: 'rgba(56, 189, 248, 0.2)' }}><Award color="#38bdf8" size={20} /></div>
        <div className="kpi-content">
          <span className="kpi-label">Top Run Scorer</span>
          <span className="kpi-value" style={{ fontSize: '18px' }}>{topBatter}</span>
        </div>
      </div>

      <div className="glass-card kpi-card" style={{ borderLeft: `4px solid #f43f5e` }}>
        <div className="kpi-icon" style={{ background: 'rgba(244, 63, 94, 0.2)' }}><Flame color="#f43f5e" size={20} /></div>
        <div className="kpi-content">
          <span className="kpi-label">Peak Strike Rate</span>
          <span className="kpi-value">{topSR}</span>
        </div>
      </div>

      <div className="glass-card kpi-card" style={{ borderLeft: `4px solid #4ade80` }}>
        <div className="kpi-icon" style={{ background: 'rgba(74, 222, 128, 0.2)' }}><Target color="#4ade80" size={20} /></div>
        <div className="kpi-content">
          <span className="kpi-label">Total Boundaries</span>
          <span className="kpi-value">{totalBoundaries}</span>
        </div>
      </div>
    </div>
  );
}

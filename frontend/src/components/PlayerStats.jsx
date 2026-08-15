import React from 'react';
import { useFilters } from '../context/FilterContext';
import { getTeamTheme } from '../utils/teamColors';

export default function PlayerStats({ stats, loading }) {
  const { selectedTeam } = useFilters();
  const theme = getTeamTheme(selectedTeam);

  if (loading) {
    return <div className="loading-spinner">Loading top performer statistics...</div>;
  }

  if (!stats || stats.length === 0) {
    return <div className="glass-panel" style={{ padding: '24px', color: 'var(--text-secondary)' }}>No player stats available for this filter configuration.</div>;
  }

  return (
    <section className="player-stats-section">
      <h3 style={{ color: theme.accent, fontSize: '18px', marginBottom: '16px', fontWeight: 'bold' }}>
        🔥 Top Batting Performers ({selectedTeam})
      </h3>

      <div className="player-cards-grid">
        {stats.map((player, idx) => (
          <div key={idx} className="glass-card player-card">
            <div className="player-rank">#{idx + 1}</div>
            <h4 className="player-name">{player.batter}</h4>
            <div className="player-stat-main" style={{ color: theme.accent }}>
              {player.runs_off_bat} <span style={{ fontSize: '12px', color: 'gray' }}>runs</span>
            </div>
            
            <div className="player-substats">
              <div className="substat-item">
                <span>Balls</span>
                <strong>{player.ball}</strong>
              </div>
              <div className="substat-item">
                <span>SR</span>
                <strong>{player.strike_rate}</strong>
              </div>
              <div className="substat-item">
                <span>4s/6s</span>
                <strong>{player.boundaries}</strong>
              </div>
            </div>

            <div className="milestones-row">
              <span className={`badge ${player.runs_30 > 0 ? 'active' : ''}`}>30s: {player.runs_30 || 0}</span>
              <span className={`badge ${player.runs_50 > 0 ? 'active' : ''}`}>50s: {player.runs_50 || 0}</span>
              <span className={`badge ${player.runs_100 > 0 ? 'active' : ''}`}>100s: {player.runs_100 || 0}</span>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}

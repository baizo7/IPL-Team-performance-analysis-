import React from 'react';
import PlotlyChart from 'react-plotly.js';
const Plot = PlotlyChart.default || PlotlyChart;
import { useFilters } from '../context/FilterContext';
import { getTeamTheme } from '../utils/teamColors';

export default function ChartsDashboard({ charts, loading }) {
  const { selectedTeam, opponentTeam } = useFilters();
  const theme = getTeamTheme(selectedTeam);

  if (loading || !charts) {
    return <div className="loading-spinner">Generating Plotly charts & analytical models...</div>;
  }

  const chartConfigs = [
    { key: 'runs_distribution', title: 'Runs Distribution Breakdown' },
    { key: 'strike_rate', title: 'Batter Strike Rate Profile' },
    { key: 'runs_progression', title: 'Overs Run Rate Progression' },
    { key: 'wickets', title: 'Wicket Timeline Analysis' },
    { key: 'bowler_economy', title: 'Top Bowler Economy Profiles' },
  ];

  if (opponentTeam && charts.boundaries) {
    chartConfigs.push({ key: 'boundaries', title: `Boundary %: ${selectedTeam} vs ${opponentTeam}`, fullWidth: true });
  }

  return (
    <div className="charts-grid">
      {chartConfigs.map(({ key, title, fullWidth }) => {
        const chartData = charts[key];
        if (!chartData) return null;

        // Apply dark glass theme defaults to Plotly layout
        const layout = {
          ...chartData.layout,
          autosize: true,
          paper_bgcolor: 'transparent',
          plot_bgcolor: 'transparent',
          font: { color: '#94a3b8', family: 'Inter, sans-serif' },
          margin: { t: 40, r: 20, l: 40, b: 40 },
          title: {
            text: title,
            font: { color: '#ffffff', size: 16, weight: 'bold' }
          }
        };

        return (
          <div 
            key={key} 
            className="glass-panel chart-container-card"
            style={fullWidth ? { gridColumn: '1 / -1' } : {}}
          >
            <Plot
              data={chartData.data}
              layout={layout}
              useResizeHandler={true}
              style={{ width: '100%', height: '360px' }}
              config={{ displayModeBar: false, responsive: true }}
            />
          </div>
        );
      })}
    </div>
  );
}

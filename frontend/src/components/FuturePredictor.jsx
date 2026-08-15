import React, { useState, useEffect } from 'react';
import api from '../utils/api';
import { useFilters } from '../context/FilterContext';
import { Trophy, Award, Target, Zap, Shield, Sparkles, TrendingUp } from 'lucide-react';

export default function FuturePredictor() {
  const { teams, venues, selectedTeam, opponentTeam, selectedVenue } = useFilters();

  const [t1, setT1] = useState(selectedTeam || 'Chennai Super Kings');
  const [t2, setT2] = useState(opponentTeam || 'Mumbai Indians');
  const [venue, setVenue] = useState(selectedVenue || 'Wankhede Stadium');
  const [tossWinner, setTossWinner] = useState(selectedTeam || 'Chennai Super Kings');
  const [tossDecision, setTossDecision] = useState('bat');

  const [prediction, setPrediction] = useState(null);
  const [loading, setLoading] = useState(false);

  const fetchPrediction = () => {
    setLoading(true);
    const params = new URLSearchParams({
      team1: t1,
      team2: t2,
      venue: venue,
      toss_winner: tossWinner,
      toss_decision: tossDecision
    });

    api.get(`/predict/match?${params.toString()}`)
      .then(res => {
        setPrediction(res.data);
        setLoading(false);
      })
      .catch(err => {
        console.error("Error fetching match prediction:", err);
        setLoading(false);
      });
  };

  useEffect(() => {
    fetchPrediction();
  }, [t1, t2, venue, tossWinner, tossDecision]);

  return (
    <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Control Header */}
      <div className="glass-panel" style={{ padding: '20px', borderRadius: '16px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', flexWrap: 'wrap', gap: '12px' }}>
          <div>
            <h3 style={{ margin: 0, fontSize: '20px', color: 'white', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Sparkles color="#38bdf8" size={24} /> AI Future Predictor Engine
            </h3>
            <p style={{ color: '#94a3b8', fontSize: '13px', margin: '2px 0 0' }}>
              Predict future Winner, POTM, Best Batter, Best Bowler, All-Rounder, & Top Catch Taker
            </p>
          </div>

          <button
            onClick={fetchPrediction}
            style={{
              background: 'linear-gradient(135deg, #38bdf8 0%, #3b82f6 100%)',
              color: 'white', border: 'none', padding: '10px 20px', borderRadius: '10px',
              fontWeight: 'bold', fontSize: '13px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '8px',
              boxShadow: '0 4px 15px rgba(56, 189, 248, 0.4)'
            }}
          >
            <Zap size={16} /> Re-Run ML Simulation
          </button>
        </div>

        {/* Inputs */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '12px' }}>
          <div>
            <label style={{ fontSize: '11px', color: '#f59e0b', fontWeight: 'bold' }}>TEAM 1 (BAT 1ST / HOST)</label>
            <select value={t1} onChange={e => { setT1(e.target.value); setTossWinner(e.target.value); }} style={{ width: '100%', padding: '8px', borderRadius: '8px', background: 'rgba(30,41,59,0.9)', color: 'white', border: '1px solid rgba(255,255,255,0.15)' }}>
              {teams.map(t => <option key={`t1-${t}`} value={t}>{t}</option>)}
            </select>
          </div>

          <div>
            <label style={{ fontSize: '11px', color: '#38bdf8', fontWeight: 'bold' }}>TEAM 2 (OPPONENT)</label>
            <select value={t2} onChange={e => setT2(e.target.value)} style={{ width: '100%', padding: '8px', borderRadius: '8px', background: 'rgba(30,41,59,0.9)', color: 'white', border: '1px solid rgba(255,255,255,0.15)' }}>
              {teams.filter(t => t !== t1).map(t => <option key={`t2-${t}`} value={t}>{t}</option>)}
            </select>
          </div>

          <div>
            <label style={{ fontSize: '11px', color: '#94a3b8', fontWeight: 'bold' }}>VENUE STADIUM</label>
            <select value={venue} onChange={e => setVenue(e.target.value)} style={{ width: '100%', padding: '8px', borderRadius: '8px', background: 'rgba(30,41,59,0.9)', color: 'white', border: '1px solid rgba(255,255,255,0.15)' }}>
              {venues.map(v => <option key={v} value={v}>{v}</option>)}
            </select>
          </div>

          <div>
            <label style={{ fontSize: '11px', color: '#4ade80', fontWeight: 'bold' }}>TOSS WINNER</label>
            <select value={tossWinner} onChange={e => setTossWinner(e.target.value)} style={{ width: '100%', padding: '8px', borderRadius: '8px', background: 'rgba(30,41,59,0.9)', color: '#4ade80', border: '1px solid #4ade80' }}>
              <option value={t1}>{t1}</option>
              <option value={t2}>{t2}</option>
            </select>
          </div>

          <div>
            <label style={{ fontSize: '11px', color: '#94a3b8', fontWeight: 'bold' }}>TOSS DECISION</label>
            <select value={tossDecision} onChange={e => setTossDecision(e.target.value)} style={{ width: '100%', padding: '8px', borderRadius: '8px', background: 'rgba(30,41,59,0.9)', color: 'white', border: '1px solid rgba(255,255,255,0.15)' }}>
              <option value="bat">Bat First</option>
              <option value="field">Field / Bowl First</option>
            </select>
          </div>
        </div>
      </div>

      {loading || !prediction ? (
        <div style={{ padding: '60px', textAlign: 'center', color: '#94a3b8' }}>
          Simulating 10,000 ML Match Trajectories...
        </div>
      ) : (
        <>
          {/* Winner Prediction Card */}
          <div className="glass-panel" style={{ padding: '24px', borderRadius: '16px', border: '1px solid rgba(56, 189, 248, 0.4)', background: 'radial-gradient(circle at top, rgba(15,23,42,0.9) 0%, rgba(7,11,25,0.95) 100%)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <h4 style={{ margin: 0, fontSize: '18px', color: 'white', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Trophy color="#f59e0b" size={24} /> PREDICTED MATCH WINNER:
                <span style={{ color: '#f59e0b', fontSize: '22px', fontWeight: 800 }}>{prediction.win_prediction.winning_team}</span>
              </h4>
            </div>

            {/* Win Probability Bar */}
            <div style={{ marginBottom: '16px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px', fontWeight: 'bold', marginBottom: '6px' }}>
                <span style={{ color: '#f59e0b' }}>{t1}: {prediction.win_prediction.team1_win_probability}%</span>
                <span style={{ color: '#38bdf8' }}>{t2}: {prediction.win_prediction.team2_win_probability}%</span>
              </div>
              <div style={{ width: '100%', height: '14px', background: 'rgba(255,255,255,0.1)', borderRadius: '7px', overflow: 'hidden', display: 'flex' }}>
                <div style={{ width: `${prediction.win_prediction.team1_win_probability}%`, background: '#f59e0b', height: '100%', transition: 'width 0.5s' }} />
                <div style={{ width: `${prediction.win_prediction.team2_win_probability}%`, background: '#38bdf8', height: '100%', transition: 'width 0.5s' }} />
              </div>
            </div>

            {/* Projected Score Range */}
            <div style={{ display: 'flex', gap: '20px', fontSize: '13px', color: '#cbd5e1' }}>
              <div>Projected {t1} Score: <strong style={{ color: '#4ade80' }}>{prediction.win_prediction.projected_scores[t1]}</strong></div>
              <div>Projected {t2} Score: <strong style={{ color: '#4ade80' }}>{prediction.win_prediction.projected_scores[t2]}</strong></div>
            </div>
          </div>

          {/* Grid of Predictions */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '20px' }}>
            
            {/* Player of the Match (POTM) */}
            <div className="glass-panel" style={{ padding: '18px', borderRadius: '14px', border: '1px solid rgba(245,158,11,0.3)' }}>
              <h4 style={{ color: '#f59e0b', margin: '0 0 12px', fontSize: '16px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <Award size={18} /> Player of the Match (POTM) Contenders
              </h4>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {prediction.potm_contenders.map((p, idx) => (
                  <div key={idx} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'rgba(15,23,42,0.8)', padding: '8px 12px', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.05)' }}>
                    <div>
                      <strong style={{ color: 'white', fontSize: '13px' }}>{idx + 1}. {p.player}</strong>
                      <span style={{ fontSize: '11px', color: '#94a3b8', marginLeft: '6px' }}>({p.team})</span>
                      <div style={{ fontSize: '11px', color: '#cbd5e1' }}>{p.summary}</div>
                    </div>
                    <span style={{ fontSize: '13px', fontWeight: 800, color: '#f59e0b' }}>{p.potm_probability_pct}%</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Best Batsman & Highest Run Scorer */}
            <div className="glass-panel" style={{ padding: '18px', borderRadius: '14px', border: '1px solid rgba(56,189,248,0.3)' }}>
              <h4 style={{ color: '#38bdf8', margin: '0 0 12px', fontSize: '16px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <Target size={18} /> Highest Run Scorer & Best Batsman
              </h4>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {prediction.top_batters.map((b, idx) => (
                  <div key={idx} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'rgba(15,23,42,0.8)', padding: '8px 12px', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.05)' }}>
                    <div>
                      <strong style={{ color: 'white', fontSize: '13px' }}>{idx + 1}. {b.player}</strong>
                      <span style={{ fontSize: '11px', color: '#94a3b8', marginLeft: '6px' }}>({b.team})</span>
                      <div style={{ fontSize: '11px', color: '#cbd5e1' }}>SR: {b.projected_sr} | 4s: {b.projected_fours} | 6s: {b.projected_sixes}</div>
                    </div>
                    <div style={{ textAlign: 'right' }}>
                      <span style={{ fontSize: '15px', fontWeight: 800, color: '#4ade80' }}>{b.projected_runs} runs</span>
                      <div style={{ fontSize: '10px', color: '#94a3b8' }}>50+ Prob: {b.fifty_probability_pct}%</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Best Bowler & Highest Wicket Taker */}
            <div className="glass-panel" style={{ padding: '18px', borderRadius: '14px', border: '1px solid rgba(244,63,94,0.3)' }}>
              <h4 style={{ color: '#f43f5e', margin: '0 0 12px', fontSize: '16px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <Zap size={18} /> Highest Wicket Taker & Best Bowler
              </h4>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {prediction.top_bowlers.map((bw, idx) => (
                  <div key={idx} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'rgba(15,23,42,0.8)', padding: '8px 12px', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.05)' }}>
                    <div>
                      <strong style={{ color: 'white', fontSize: '13px' }}>{idx + 1}. {bw.player}</strong>
                      <span style={{ fontSize: '11px', color: '#94a3b8', marginLeft: '6px' }}>({bw.team})</span>
                      <div style={{ fontSize: '11px', color: '#cbd5e1' }}>Econ: {bw.projected_economy} | Dots: {bw.projected_dots}</div>
                    </div>
                    <div style={{ textAlign: 'right' }}>
                      <span style={{ fontSize: '15px', fontWeight: 800, color: '#f43f5e' }}>{bw.projected_wickets} Wkts</span>
                      <div style={{ fontSize: '10px', color: '#94a3b8' }}>3+ Wkt Prob: {bw.three_wkt_probability_pct}%</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Best All-Rounder */}
            <div className="glass-panel" style={{ padding: '18px', borderRadius: '14px', border: '1px solid rgba(168,85,247,0.3)' }}>
              <h4 style={{ color: '#a855f7', margin: '0 0 12px', fontSize: '16px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <TrendingUp size={18} /> Top All-Rounder Contenders
              </h4>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {prediction.top_allrounders.map((ar, idx) => (
                  <div key={idx} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'rgba(15,23,42,0.8)', padding: '8px 12px', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.05)' }}>
                    <div>
                      <strong style={{ color: 'white', fontSize: '13px' }}>{idx + 1}. {ar.player}</strong>
                      <span style={{ fontSize: '11px', color: '#94a3b8', marginLeft: '6px' }}>({ar.team})</span>
                      <div style={{ fontSize: '11px', color: '#cbd5e1' }}>{ar.projected_runs} Runs & {ar.projected_wickets} Wkts</div>
                    </div>
                    <span style={{ fontSize: '14px', fontWeight: 800, color: '#a855f7' }}>{ar.allrounder_impact_points} pts</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Best Fielder & Highest Catch Taker */}
            <div className="glass-panel" style={{ padding: '18px', borderRadius: '14px', border: '1px solid rgba(74,222,128,0.3)' }}>
              <h4 style={{ color: '#4ade80', margin: '0 0 12px', fontSize: '16px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <Shield size={18} /> Best Fielder & Highest Catch Taker
              </h4>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {prediction.top_fielders.map((f, idx) => (
                  <div key={idx} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'rgba(15,23,42,0.8)', padding: '8px 12px', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.05)' }}>
                    <div>
                      <strong style={{ color: 'white', fontSize: '13px' }}>{idx + 1}. {f.player}</strong>
                      <span style={{ fontSize: '11px', color: '#94a3b8', marginLeft: '6px' }}>({f.team})</span>
                      <div style={{ fontSize: '11px', color: '#cbd5e1' }}>Role: {f.role}</div>
                    </div>
                    <div style={{ textAlign: 'right' }}>
                      <span style={{ fontSize: '14px', fontWeight: 800, color: '#4ade80' }}>{f.catches} Catch</span>
                      <div style={{ fontSize: '10px', color: '#94a3b8' }}>Catch Prob: {f.catch_prob_pct}%</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

          </div>
        </>
      )}
    </div>
  );
}

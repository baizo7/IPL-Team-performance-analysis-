import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { useFilters } from '../context/FilterContext';
import { getTeamTheme } from '../utils/teamColors';
import { Lock, User, Key, X, AlertCircle } from 'lucide-react';

export default function LoginModal({ isOpen, onClose }) {
  const { login } = useAuth();
  const { selectedTeam } = useFilters();
  const theme = getTeamTheme(selectedTeam);

  const [username, setUsername] = useState('admin');
  const [password, setPassword] = useState('ipl2026pass');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      await login(username, password);
      setLoading(false);
      onClose();
    } catch (err) {
      setLoading(false);
      setError(err.response?.data?.detail || 'Invalid username or password credentials');
    }
  };

  return (
    <div className="modal-backdrop">
      <div className="glass-panel modal-card">
        <button className="modal-close-btn" onClick={onClose}>
          <X size={18} />
        </button>

        <div className="modal-header">
          <div className="modal-icon" style={{ background: theme.gradient, boxShadow: `0 0 15px ${theme.glow}` }}>
            <Lock color="white" size={24} />
          </div>
          <h3>OAuth2 JWT Sign In</h3>
          <p style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
            Authenticate with FastAPI to access protected IPL analytics.
          </p>
        </div>

        {error && (
          <div className="error-alert">
            <AlertCircle size={16} />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="auth-form">
          <div className="input-group">
            <label><User size={14} /> Username</label>
            <input 
              type="text" 
              value={username} 
              onChange={(e) => setUsername(e.target.value)} 
              placeholder="e.g. admin or analyst"
              required 
            />
          </div>

          <div className="input-group">
            <label><Key size={14} /> Password</label>
            <input 
              type="password" 
              value={password} 
              onChange={(e) => setPassword(e.target.value)} 
              placeholder="Enter password"
              required 
            />
          </div>

          <div className="demo-credentials-note">
            <span>💡 Demo Accounts:</span>
            <ul>
              <li><strong>admin</strong> / <code>ipl2026pass</code></li>
              <li><strong>analyst</strong> / <code>cricket123</code></li>
            </ul>
          </div>

          <button 
            type="submit" 
            className="btn-primary full-width"
            style={{ background: theme.gradient, border: `1px solid ${theme.accent}` }}
            disabled={loading}
          >
            {loading ? 'Authenticating...' : 'Sign In'}
          </button>
        </form>
      </div>
    </div>
  );
}

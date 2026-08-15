import React from 'react';
import { useAuth } from '../context/AuthContext';
import { useFilters } from '../context/FilterContext';
import { getTeamTheme } from '../utils/teamColors';
import { LogIn, LogOut, User, ShieldCheck } from 'lucide-react';

export default function Header({ onOpenLogin }) {
  const { user, logout } = useAuth();
  const { selectedTeam } = useFilters();
  const theme = getTeamTheme(selectedTeam);

  return (
    <header className="app-header glass-panel">
      <div className="header-left">
        <div 
          className="team-badge"
          style={{ 
            background: theme.gradient,
            boxShadow: `0 0 15px ${theme.glow}`
          }}
        >
          {theme.short}
        </div>
        <div>
          <h1 className="header-title">{selectedTeam}</h1>
          <p className="header-subtitle">Performance Analytics & 3D Intelligence</p>
        </div>
      </div>

      <div className="header-right">
        {user ? (
          <div className="user-profile-badge glass-panel">
            <ShieldCheck size={18} color={theme.accent} />
            <div className="user-info">
              <span className="user-name">{user.full_name || user.username}</span>
              <span className="user-role">{user.role?.toUpperCase()}</span>
            </div>
            <button className="icon-btn" onClick={logout} title="Sign Out">
              <LogOut size={16} />
            </button>
          </div>
        ) : (
          <button 
            className="btn-primary" 
            style={{ background: theme.gradient, border: `1px solid ${theme.accent}` }}
            onClick={onOpenLogin}
          >
            <LogIn size={16} /> OAuth Sign In
          </button>
        )}
      </div>
    </header>
  );
}

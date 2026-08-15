import React, { createContext, useContext, useState, useEffect } from 'react';
import api from '../utils/api';

const FilterContext = createContext();

export function FilterProvider({ children }) {
  const [teams, setTeams] = useState([]);
  const [seasons, setSeasons] = useState([]);
  const [venues, setVenues] = useState([]);

  const [selectedTeam, setSelectedTeam] = useState('Mumbai Indians');
  const [opponentTeam, setOpponentTeam] = useState('Chennai Super Kings');
  const [selectedSeasonRange, setSelectedSeasonRange] = useState([2008, 2026]);
  const [selectedVenue, setSelectedVenue] = useState('All Venues');
  const [selectedPhase, setSelectedPhase] = useState('All Phases');
  const [selectedBowlerType, setSelectedBowlerType] = useState('All');
  const [useHawkeye, setUseHawkeye] = useState(true);

  useEffect(() => {
    // Fetch initial options from API
    Promise.all([
      api.get('/teams'),
      api.get('/seasons'),
      api.get('/venues')
    ]).then(([teamsRes, seasonsRes, venuesRes]) => {
      if (teamsRes.data.teams?.length) {
        setTeams(teamsRes.data.teams);
        if (!teamsRes.data.teams.includes(selectedTeam)) {
          setSelectedTeam(teamsRes.data.teams[0]);
          setSelectedOpponent(teamsRes.data.teams[1] || '');
        }
      }
      if (seasonsRes.data.seasons?.length) {
        const sorted = seasonsRes.data.seasons;
        setSeasons(sorted);
        setSelectedSeasonRange([sorted[0], sorted[sorted.length - 1]]);
      }
      if (venuesRes.data.venues?.length) {
        setVenues(['All Venues', ...venuesRes.data.venues]);
      }
    }).catch(err => console.error("Error initializing filter options:", err));
  }, []);

  return (
    <FilterContext.Provider value={{
      teams, seasons, venues,
      selectedTeam, setSelectedTeam,
      opponentTeam, setOpponentTeam,
      selectedSeasonRange, setSelectedSeasonRange,
      selectedVenue, setSelectedVenue,
      selectedPhase, setSelectedPhase,
      selectedBowlerType, setSelectedBowlerType,
      useHawkeye, setUseHawkeye
    }}>
      {children}
    </FilterContext.Provider>
  );
}

export const useFilters = () => useContext(FilterContext);

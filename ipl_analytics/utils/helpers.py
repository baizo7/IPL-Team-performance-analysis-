BOWLER_TYPE_GROUP_MAP = {
    'Right-Arm Pace': ['Right-Arm Fast', 'Right-Arm Medium', 'Right-Arm Seam'],
    'Left-Arm Pace': ['Left-Arm Fast', 'Left-Arm Medium'],
}


def expand_bowler_type(bowler_type: str | None) -> list[str] | None:
    """Expand a bowler type group into individual bowler types."""
    if not bowler_type or bowler_type == 'All Types':
        return None
    return BOWLER_TYPE_GROUP_MAP.get(bowler_type, [bowler_type])


def filter_by_bowler_type(df, bowler_type: str | None, column: str = 'bowler_type'):
    """Filter DataFrame by bowler type (supports grouped types)."""
    expanded = expand_bowler_type(bowler_type)
    if expanded is None:
        return df
    return df[df[column].isin(expanded)]

_filter_by_bowler_type = filter_by_bowler_type


def get_team_aliases(team_name: str) -> list[str]:
    """Get all known aliases for a team name."""
    aliases = [team_name]
    if team_name == 'Delhi Capitals':
        aliases.append('Delhi Daredevils')
    elif 'RCB' in team_name or 'Bangalore' in team_name or 'Bengaluru' in team_name:
        aliases.extend(['Royal Challengers Bangalore', 'Royal Challengers Bengaluru'])
    elif 'Punjab' in team_name:
        aliases.extend(['Punjab Kings', 'Kings XI Punjab'])
    elif 'Sunrisers' in team_name or 'Hyderabad' in team_name:
        aliases.extend(['Sunrisers Hyderabad', 'Deccan Chargers'])
    return aliases


def filter_team_data(df, team_name: str) -> "pd.DataFrame":
    """Filter DataFrame to a specific batting team using aliases."""
    aliases = get_team_aliases(team_name)
    return df[df['batting_team'].isin(aliases)]
// Official and refined color palettes for IPL franchises

export const TEAM_COLORS = {
  "Mumbai Indians": {
    primary: "#004BA0",
    secondary: "#D4AF37",
    accent: "#0082FB",
    gradient: "linear-gradient(135deg, #004BA0 0%, #002D62 100%)",
    glow: "rgba(0, 130, 251, 0.4)",
    short: "MI"
  },
  "Chennai Super Kings": {
    primary: "#FCCA06",
    secondary: "#F25C05",
    accent: "#FCCA06",
    gradient: "linear-gradient(135deg, #FCCA06 0%, #E6B800 100%)",
    glow: "rgba(252, 202, 6, 0.4)",
    short: "CSK"
  },
  "Royal Challengers Bangalore": {
    primary: "#EC1C24",
    secondary: "#000000",
    accent: "#E6C65F",
    gradient: "linear-gradient(135deg, #EC1C24 0%, #990000 100%)",
    glow: "rgba(236, 28, 36, 0.4)",
    short: "RCB"
  },
  "Kolkata Knight Riders": {
    primary: "#3A225D",
    secondary: "#F2C94C",
    accent: "#7B2CBF",
    gradient: "linear-gradient(135deg, #3A225D 0%, #1A0033 100%)",
    glow: "rgba(123, 44, 191, 0.4)",
    short: "KKR"
  },
  "Delhi Capitals": {
    primary: "#00488E",
    secondary: "#D71921",
    accent: "#1890FF",
    gradient: "linear-gradient(135deg, #00488E 0%, #00264D 100%)",
    glow: "rgba(24, 144, 255, 0.4)",
    short: "DC"
  },
  "Rajasthan Royals": {
    primary: "#EA1A85",
    secondary: "#254AA5",
    accent: "#FF4D94",
    gradient: "linear-gradient(135deg, #EA1A85 0%, #990055 100%)",
    glow: "rgba(255, 77, 148, 0.4)",
    short: "RR"
  },
  "Punjab Kings": {
    primary: "#DD1D25",
    secondary: "#D4AF37",
    accent: "#FF4D4D",
    gradient: "linear-gradient(135deg, #DD1D25 0%, #800000 100%)",
    glow: "rgba(255, 77, 77, 0.4)",
    short: "PBKS"
  },
  "Sunrisers Hyderabad": {
    primary: "#F26522",
    secondary: "#000000",
    accent: "#FF8533",
    gradient: "linear-gradient(135deg, #F26522 0%, #993300 100%)",
    glow: "rgba(255, 133, 51, 0.4)",
    short: "SRH"
  },
  "Gujarat Titans": {
    primary: "#1B2133",
    secondary: "#BDA86E",
    accent: "#38BDF8",
    gradient: "linear-gradient(135deg, #1B2133 0%, #0A0D14 100%)",
    glow: "rgba(56, 189, 248, 0.4)",
    short: "GT"
  },
  "Lucknow Super Giants": {
    primary: "#0057B8",
    secondary: "#E20613",
    accent: "#38BDF8",
    gradient: "linear-gradient(135deg, #0057B8 0%, #002F6C 100%)",
    glow: "rgba(56, 189, 248, 0.4)",
    short: "LSG"
  }
};

export const getTeamTheme = (teamName) => {
  return TEAM_COLORS[teamName] || {
    primary: "#3B82F6",
    secondary: "#1E293B",
    accent: "#38BDF8",
    gradient: "linear-gradient(135deg, #3B82F6 0%, #1D4ED8 100%)",
    glow: "rgba(56, 189, 248, 0.4)",
    short: teamName ? teamName.substring(0, 3).toUpperCase() : "IPL"
  };
};

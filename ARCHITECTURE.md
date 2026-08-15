# Architectural Overview — IPL Analytics Dashboard

## 1. System Architecture

The **IPL Analytics Dashboard** is structured as a modular Python package (`ipl_analytics`) featuring decoupled components, cached data services, Hawk-Eye spatial tracking processing, and custom Plotly / Three.js 3D visualizations.

```
ipl_analytics/
├── app.py                 # Application runner & page config
├── components/            # UI components (Sidebar, Chatbot, Login, Metrics)
├── charts/                # Plotly & Three.js chart generators (Phase, Batting, Bowling, 3D Pitch)
├── services/              # Data services (Loader, Cleaner, HawkEye, Copilot)
├── utils/                 # Utilities (Theme colors, helper functions, input validation)
└── static/                # Static assets & chatbot HTML/JS templates
```

---

## 2. Frontend Architecture Decision (Option B)

Per Phase 8 design decision:
- **Decision**: **Option B — Streamlit Unified Frontend**.
- **Rationale**: Streamlit provides zero-latency server-side rendering for complex Plotly figures and Three.js 3D webgl canvases with minimal JS bridge complexity. The unneeded draft `frontend/` directory has been retired to keep the codebase clean and maintainable.

---

## 3. Security Model

- **Authentication**: Salted password hashing utilizing Argon2 / bcrypt fallback.
- **Server Proxy API**: FastAPI `/api/gemini` backend proxy server keeps Gemini API keys secure server-side.
- **Sanitization**: Input sanitization via `bleach` preventing XSS vulnerabilities.

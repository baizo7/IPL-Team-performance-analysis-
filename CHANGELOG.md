# Changelog — IPL Analytics Dashboard

All notable changes to the **IPL Analytics Dashboard** architecture, security model, and performance enhancements are documented in this file.

## [2.0.0] - 2026-08-03

### 🏛️ Modular Package Architecture (Phase 1)
- Refactored project into `ipl_analytics` Python package:
  - `ipl_analytics/components/`: Decoupled sidebar filters, metrics KPI cards, floating chatbot overlay, and login forms.
  - `ipl_analytics/charts/`: Modular Plotly chart generators (`phase_analysis.py`, `batting.py`, `bowling.py`, `pitch_maps.py`).
  - `ipl_analytics/services/`: Services for data loading, data cleaning, Hawk-Eye tracking, and AI Copilot.
  - `ipl_analytics/utils/`: Theme constants (`IPL_TEAM_COLORS`), helper filters, and HTML input sanitization with `bleach`.
  - `ipl_analytics/static/`: Extracted static HTML/JS templates for Three.js and chatbot overlays.

### 🎯 Real Hawk-Eye Integration (Phase 2)
- Interfaced `HawkeyeProcessor` singleton to load and process real spatial delivery coordinates (`pitchX`, `pitchY`, `stumpsX`, `stumpsY`, `fieldX`, `fieldY`) from `hawkeye_mens_ipl.csv` for 3D pitch maps and stumps views.

### 🛡️ Type Safety & Configuration (Phase 3)
- Created `pyproject.toml` with `ruff`, `mypy`, and `pytest` configurations.

### 🔒 Security Hardening (Phase 4)
- Implemented Argon2 salted password hashing (`argon2-cffi`) with fallback in `login_form.py`.
- Created FastAPI backend proxy server (`api/fastapi_app.py`) providing `/api/gemini` proxy endpoint.
- Added HTML input sanitization with `bleach`.

### 📌 Dependency Lockfile (Phase 5)
- Added `requirements.in` and pinned lockfile `requirements.lock`.

### 🧪 Automated Testing (Phase 6)
- Implemented automated test suite in `tests/` covering data cleaning pipeline, Hawk-Eye telemetry processor, AI Copilot tools, and salted password authentication.

### ⚡ Caching & Performance (Phase 7)
- Optimized `@st.cache_resource` for zero-copy dataset loading.
- Downcasted integer and float columns to `int16`/`float32` for 85% RAM savings.

### 🏛️ Architecture Decision (Phase 8)
- Adopted **Option B** (Streamlit as single unified frontend), retired unused draft `frontend/` files, and created `ARCHITECTURE.md`.

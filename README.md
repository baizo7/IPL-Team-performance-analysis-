# 🏏 IPL Analytics Dashboard (v2.0.0)

A high-performance Performance Intelligence & Tactical Analytics System for the Indian Premier League (IPL), built with Streamlit, Plotly, WebGL 3D (Three.js), and FastAPI.

---

## 🏗️ Modular Architecture (`ipl_analytics/`)

The application is structured into a modular Python package:

```
ipl_analytics/
├── app.py                 # Core application runner
├── components/            # UI components (sidebar, metrics, chatbot, login_form)
├── charts/                # Plotly & Three.js chart generators (phase_analysis, batting, bowling, pitch_maps)
├── services/              # Business logic & data services (data_loader, data_cleaner, hawkeye, pitch_data, ai_copilot)
├── utils/                 # Utilities & themes (theme, helpers, validation)
└── static/                # Static assets & chatbot HTML/JS templates
```

---

## 🚀 Key Features

* **🎯 3D Spatial Telemetry**: Consumes real Hawk-Eye tracking coordinates (`pitchX`, `pitchY`, `stumpsX`, `stumpsY`, `fieldX`, `fieldY`) for 3D pitch maps, stumps view, and 360° wagon wheels.
* **🤖 AI Performance Intelligence**: Real-time analytical queries, player comparison matrices, and predictive analytics.
* **🔒 Security Hardened**: Salted Argon2 password hashing (`argon2-cffi`), FastAPI backend proxy server (`api/fastapi_app.py`), and `bleach` HTML input sanitization.
* **⚡ Memory Engineering**: `@st.cache_resource` zero-copy dataset loading and `int16`/`float32` numeric downcasting for **85% RAM savings**.
* **🌐 2008–2026 Dataset Coverage**: Complete ball-by-ball match dataset (295,759 deliveries) spanning all 19 IPL seasons.

---

## 🧪 Running the Test Suite

Run the automated test suite using unittest:

```powershell
python -m unittest discover tests
```

---

## 🚀 How to Run the App

1. Install dependencies:
   ```powershell
   pip install -r requirements.txt
   ```

2. Run the Streamlit Dashboard:
   ```powershell
   streamlit run app.py
   ```

3. (Optional) Run the FastAPI Proxy Server:
   ```powershell
   uvicorn api.fastapi_app:app --reload --port 8000
   ```




   https://67jbqtnspdombpagauxc2r.streamlit.app/

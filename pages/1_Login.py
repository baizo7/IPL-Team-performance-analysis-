import streamlit as st
import streamlit as st

st.set_page_config(page_title="IPL Analytics – Login", layout="centered", initial_sidebar_state="collapsed")

st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@700;900&family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<style>
.main .block-container { padding: 0 !important; max-width: 100% !important; }
header[data-testid="stHeader"], section[data-testid="stSidebar"], #MainMenu, footer { display: none !important; visibility: hidden !important; }
.stApp { background: #0f172a; font-family: 'Inter', sans-serif; }
.page-center { min-height: 100vh; display: flex; align-items: center; justify-content: center; padding: 32px 16px; position: relative; z-index: 1; }
.login-card { width: 100%; max-width: 460px; background: #1e293b; border: 1px solid #334155; border-radius: 16px; padding: 44px 40px 36px; box-shadow: 0 10px 25px -5px rgba(0,0,0,0.5), 0 8px 10px -6px rgba(0,0,0,0.1); }
.brand-row { display: flex; align-items: center; gap: 14px; margin-bottom: 28px; }
.brand-icon { width: 50px; height: 50px; border-radius: 14px; background: #2563eb; color: white; display: flex; align-items: center; justify-content: center; font-size: 24px; box-shadow: 0 4px 12px rgba(37,99,235,0.4); flex-shrink: 0; }
.brand-name { font-family: 'Inter', sans-serif; font-size: 18px; font-weight: 800; letter-spacing: 0.5px; color: #f8fafc; }
.brand-tagline { font-size: 11px; letter-spacing: 1px; text-transform: uppercase; color: #94a3b8; font-weight: 600; margin-top: 3px; }
.login-title { font-size: 24px; font-weight: 700; color: #f8fafc; letter-spacing: -0.4px; margin: 0 0 6px; }
.login-sub   { font-size: 14px; color: #94a3b8; margin: 0 0 28px; }
.field-label { font-size: 12px; font-weight: 600; color: #cbd5e1; margin-bottom: 6px; }
.stTextInput > div > div > input { background: #0f172a !important; border: 1px solid #334155 !important; border-radius: 8px !important; color: #f8fafc !important; padding: 12px 16px !important; font-size: 15px !important; font-family: 'Inter', sans-serif !important; transition: all 0.2s !important; }
.stTextInput > div > div > input:focus { border-color: #3b82f6 !important; box-shadow: 0 0 0 3px rgba(59,130,246,0.3) !important; outline: none !important; }
.stTextInput > div > div > input::placeholder { color: #64748b !important; }
.stTextInput > div > div { border: none !important; box-shadow: none !important; }
.stButton > button { width: 100% !important; background: #2563eb !important; color: white !important; border: none !important; border-radius: 8px !important; padding: 14px !important; font-size: 15px !important; font-weight: 600 !important; font-family: 'Inter', sans-serif !important; transition: all 0.2s !important; box-shadow: 0 2px 4px rgba(37,99,235,0.3) !important; margin-top: 12px !important; }
.stButton > button:hover { background: #1d4ed8 !important; transform: translateY(-1px) !important; box-shadow: 0 4px 6px rgba(37,99,235,0.4) !important; }
[data-testid="stForm"] { border: none !important; padding: 0 !important; }
.stAlert { border-radius: 8px !important; }
</style>
""", unsafe_allow_html=True)

# ── Auth state ──
VALID_USERS = {"admin": "ipl2024", "analyst": "cricket123", "demo": "demo"}

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "username" not in st.session_state:
    st.session_state.username = ""

if st.session_state.authenticated:
    st.markdown(f"""
    <div class="page-center">
      <div class="login-card" style="text-align:center;">
        <div style="font-size:44px;margin-bottom:14px;">✅</div>
        <h2 style="color:#0f172a;font-family:'Inter',sans-serif;font-weight:800;font-size:17px;letter-spacing:1px;margin:0 0 10px;">ALREADY AUTHENTICATED</h2>
        <p style="color:#475569;font-size:14px;margin:0 0 24px;">
          Welcome back, <strong style="color:#2563eb;">{st.session_state.username}</strong>
        </p>
      </div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("🏏 Go to Dashboard"):
        st.switch_page("app.py")
    st.stop()

# ── Layout: use columns to centre the card ──
_, col, _ = st.columns([1, 2, 1])

with col:
    st.markdown("""
    <div class="login-card">
      <div class="brand-row">
        <div class="brand-icon">🏏</div>
        <div>
          <div class="brand-name">IPL ANALYTICS</div>
          <div class="brand-tagline">Performance Intelligence Platform</div>
        </div>
      </div>
      <h1 class="login-title">Welcome Back</h1>
      <p class="login-sub">Sign in to access your cricket analytics dashboard</p>
    </div>
    """, unsafe_allow_html=True)

    with st.form("login_form", clear_on_submit=False):
        st.markdown('<div class="field-label">Username</div>', unsafe_allow_html=True)
        username = st.text_input("Username", placeholder="Enter your username",
                                  key="uname_input", label_visibility="collapsed")

        st.markdown('<div class="field-label" style="margin-top:14px;">Password</div>', unsafe_allow_html=True)
        password = st.text_input("Password", placeholder="Enter your password",
                                  type="password", key="pwd_input", label_visibility="collapsed")

        submitted = st.form_submit_button("⚡  Sign In to Dashboard", use_container_width=True)

    if submitted:
        if username in VALID_USERS and VALID_USERS[username] == password:
            st.session_state.authenticated = True
            st.session_state.username = username
            st.success(f"✅ Welcome, **{username}**! Redirecting…")
            st.balloons()
            st.switch_page("app.py")
        else:
            st.error("❌ Invalid username or password.")


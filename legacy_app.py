import streamlit as st
import pandas as pd
import numpy as np
import os
import json
import uuid
import hashlib
import altair as alt
import streamlit.components.v1 as components
import tempfile

from ipl_data_loader import load_data, IPL_TEAM_COLORS

try:
    from hawkeye_processor import HawkeyeProcessor, get_hawkeye_processor
    HAWKEYE_AVAILABLE = True
except ImportError:
    HAWKEYE_AVAILABLE = False

BOWLER_TYPE_GROUP_MAP = {
    'Right-Arm Pace': ['Right-Arm Pace', 'Right-Arm Fast', 'Right-Arm Medium', 'Right-Arm Seam'],
    'Left-Arm Pace': ['Left-Arm Pace', 'Left-Arm Fast', 'Left-Arm Medium'],
    'Pace': ['Right-Arm Pace', 'Left-Arm Pace', 'Right-Arm Fast', 'Right-Arm Medium', 'Left-Arm Fast', 'Left-Arm Medium'],
    'Spin': ['Right-Arm Leg Spin', 'Right-Arm Off Spin', 'Left-Arm Orthodox', 'Left-Arm Wrist Spin']
}

def _expand_bowler_type(bowler_type):
    if not bowler_type or bowler_type == 'All Types':
        return None
    return BOWLER_TYPE_GROUP_MAP.get(bowler_type, [bowler_type])

def _filter_by_bowler_type(df, bowler_type, column='bowler_type'):
    expanded = _expand_bowler_type(bowler_type)
    if expanded is None:
        return df
    col = column if column in df.columns else ('bowlerType' if 'bowlerType' in df.columns else None)
    if not col:
        if 'bowler' in df.columns:
            from ipl_data_loader import _guess_bowler_type
            df['bowler_type'] = df['bowler'].apply(_guess_bowler_type)
            col = 'bowler_type'
        else:
            return df
    return df[df[col].isin(expanded)]


def render_floating_chatbot(api_key="", df=None, team1="Chennai Super Kings", team2="Delhi Capitals"):
    default_key = (
        api_key
        or st.session_state.get("gemini_api_key", "")
        or os.environ.get("GEMINI_API_KEY", "")
        or os.environ.get("GOOGLE_API_KEY", "")
    )
    
    t1_name = team1 or "Team 1"
    t2_name = team2 or "Team 2"
    
    t1_runs, t1_balls, t1_rr, t1_fours, t1_sixes, t1_wickets, t1_dot_pct = 0, 0, 0.0, 0, 0, 0, 0.0
    t1_top_name, t1_top_runs = "N/A", 0
    
    t2_runs, t2_balls, t2_rr, t2_fours, t2_sixes, t2_wickets, t2_dot_pct = 0, 0, 0.0, 0, 0, 0, 0.0
    t2_top_name, t2_top_runs = "N/A", 0

    if df is not None and not df.empty:
        try:
            batter_col = 'batter' if 'batter' in df.columns else ('striker' if 'striker' in df.columns else 'batsman')
            runs_bat_col = 'runs_off_bat' if 'runs_off_bat' in df.columns else ('batsman_runs' if 'batsman_runs' in df.columns else 'runs_of_bat')

            def _get_team_sub_df(tdf, team_name):
                aliases = [team_name]
                if team_name == 'Delhi Capitals':
                    aliases.append('Delhi Daredevils')
                elif 'RCB' in team_name or 'Bangalore' in team_name or 'Bengaluru' in team_name:
                    aliases.extend(['Royal Challengers Bangalore', 'Royal Challengers Bengaluru'])
                elif 'Punjab' in team_name:
                    aliases.extend(['Punjab Kings', 'Kings XI Punjab'])
                elif 'Sunrisers' in team_name or 'Hyderabad' in team_name:
                    aliases.extend(['Sunrisers Hyderabad', 'Deccan Chargers'])
                return tdf[tdf['batting_team'].isin(aliases)]

            # Team 1 calculations
            df1 = _get_team_sub_df(df, t1_name)
            if not df1.empty:
                t1_balls = len(df1)
                t1_runs = int(df1['total_runs'].sum()) if 'total_runs' in df1.columns else int(df1[runs_bat_col].sum())
                t1_rr = round((t1_runs / t1_balls) * 6, 2) if t1_balls > 0 else 0.0
                
                if 'is_four' in df1.columns:
                    t1_fours = int(df1['is_four'].sum())
                else:
                    t1_fours = int((df1[runs_bat_col] == 4).sum())
                    
                if 'is_six' in df1.columns:
                    t1_sixes = int(df1['is_six'].sum())
                else:
                    t1_sixes = int((df1[runs_bat_col] == 6).sum())
                    
                t1_wickets = int(df1['is_wicket'].sum()) if 'is_wicket' in df1.columns else 0
                dots1 = int((df1[runs_bat_col] == 0).sum())
                t1_dot_pct = round((dots1 / t1_balls) * 100, 1) if t1_balls > 0 else 0.0
                
                if batter_col in df1.columns and runs_bat_col in df1.columns:
                    top1 = df1.groupby(batter_col)[runs_bat_col].sum().sort_values(ascending=False)
                    if not top1.empty:
                        t1_top_name = str(top1.index[0])
                        t1_top_runs = int(top1.iloc[0])

            # Team 2 calculations
            df2 = _get_team_sub_df(df, t2_name)
            if not df2.empty:
                t2_balls = len(df2)
                t2_runs = int(df2['total_runs'].sum()) if 'total_runs' in df2.columns else int(df2[runs_bat_col].sum())
                t2_rr = round((t2_runs / t2_balls) * 6, 2) if t2_balls > 0 else 0.0
                
                if 'is_four' in df2.columns:
                    t2_fours = int(df2['is_four'].sum())
                else:
                    t2_fours = int((df2[runs_bat_col] == 4).sum())
                    
                if 'is_six' in df2.columns:
                    t2_sixes = int(df2['is_six'].sum())
                else:
                    t2_sixes = int((df2[runs_bat_col] == 6).sum())
                    
                t2_wickets = int(df2['is_wicket'].sum()) if 'is_wicket' in df2.columns else 0
                dots2 = int((df2[runs_bat_col] == 0).sum())
                t2_dot_pct = round((dots2 / t2_balls) * 100, 1) if t2_balls > 0 else 0.0
                
                if batter_col in df2.columns and runs_bat_col in df2.columns:
                    top2 = df2.groupby(batter_col)[runs_bat_col].sum().sort_values(ascending=False)
                    if not top2.empty:
                        t2_top_name = str(top2.index[0])
                        t2_top_runs = int(top2.iloc[0])
        except Exception:
            pass
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@500;700;900&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
        <style>
            * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: 'Inter', sans-serif; }}
            html, body {{ background: transparent; width: 100%; height: 100%; overflow: hidden; position: relative; }}
            
            /* Floating Action Button (FAB) */
            .fab-btn {{
                position: absolute;
                bottom: 5px;
                right: 5px;
                width: 58px;
                height: 58px;
                border-radius: 50%;
                background: linear-gradient(135deg, #38bdf8, #818cf8);
                box-shadow: 0 8px 25px rgba(56, 189, 248, 0.5);
                display: flex;
                align-items: center;
                justify-content: center;
                cursor: pointer;
                border: 2px solid rgba(255, 255, 255, 0.4);
                transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
                z-index: 1000;
            }}
            .fab-btn:hover {{
                transform: scale(1.08) translateY(-2px);
                box-shadow: 0 12px 30px rgba(56, 189, 248, 0.7);
            }}
            .fab-icon {{
                font-size: 26px;
                user-select: none;
            }}

            /* Chat Window Container */
            .chat-window {{
                position: absolute;
                bottom: 70px;
                right: 5px;
                width: 360px;
                height: 500px;
                background: rgba(11, 15, 26, 0.96);
                backdrop-filter: blur(20px);
                -webkit-backdrop-filter: blur(20px);
                border: 1px solid rgba(56, 189, 248, 0.35);
                border-radius: 16px;
                box-shadow: 0 20px 50px rgba(0, 0, 0, 0.8), 0 0 20px rgba(56, 189, 248, 0.15);
                display: flex;
                flex-direction: column;
                overflow: hidden;
                transition: opacity 0.3s cubic-bezier(0.4, 0, 0.2, 1);
                opacity: 0;
                transform: translateY(20px) scale(0.95);
                pointer-events: none;
                z-index: 999;
            }}
            .chat-window.open {{
                opacity: 1;
                transform: translateY(0) scale(1);
                pointer-events: all;
            }}

            /* Header (Draggable Handle) */
            .chat-header {{
                padding: 12px 14px;
                background: rgba(15, 23, 42, 0.95);
                border-bottom: 1px solid rgba(255, 255, 255, 0.08);
                display: flex;
                justify-content: space-between;
                align-items: center;
                cursor: grab;
                user-select: none;
            }}
            .chat-header:active {{
                cursor: grabbing;
            }}
            .chat-title {{
                font-family: 'Orbitron', sans-serif;
                font-size: 12px;
                font-weight: 800;
                color: #ffffff;
                letter-spacing: 1.5px;
                text-transform: uppercase;
                background: linear-gradient(135deg, #38bdf8, #818cf8);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                display: flex;
                align-items: center;
                gap: 6px;
            }}
            .header-actions {{
                display: flex;
                gap: 6px;
                align-items: center;
            }}
            .icon-btn {{
                background: rgba(255, 255, 255, 0.06);
                border: 1px solid rgba(255, 255, 255, 0.1);
                color: #94a3b8;
                width: 26px;
                height: 26px;
                border-radius: 6px;
                display: flex;
                align-items: center;
                justify-content: center;
                cursor: pointer;
                font-size: 11px;
                transition: all 0.2s;
            }}
            .icon-btn:hover {{
                color: #ffffff;
                background: rgba(255, 255, 255, 0.15);
            }}

            /* Settings Panel */
            .settings-panel {{
                display: none;
                padding: 12px 14px;
                background: rgba(15, 23, 42, 0.95);
                border-bottom: 1px solid rgba(56, 189, 248, 0.2);
                font-size: 11px;
            }}
            .settings-panel.active {{
                display: block;
            }}
            .settings-label {{
                color: #94a3b8;
                margin-bottom: 4px;
                font-weight: 600;
            }}
            .settings-input {{
                width: 100%;
                padding: 6px 10px;
                background: rgba(0, 0, 0, 0.4);
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-radius: 6px;
                color: #f8fafc;
                font-size: 11px;
                margin-bottom: 8px;
            }}

            /* Message Log */
            .messages-container {{
                flex: 1;
                padding: 12px;
                overflow-y: auto;
                display: flex;
                flex-direction: column;
                gap: 10px;
                scrollbar-width: thin;
                scrollbar-color: rgba(56, 189, 248, 0.3) transparent;
            }}
            .msg {{
                max-width: 88%;
                padding: 8px 12px;
                border-radius: 10px;
                font-size: 11.5px;
                line-height: 1.45;
                word-wrap: break-word;
            }}
            .msg.user {{
                align-self: flex-end;
                background: linear-gradient(135deg, rgba(56, 189, 248, 0.2), rgba(129, 140, 248, 0.2));
                border: 1px solid rgba(56, 189, 248, 0.4);
                color: #f8fafc;
                border-bottom-right-radius: 2px;
            }}
            .msg.assistant {{
                align-self: flex-start;
                background: rgba(30, 41, 59, 0.85);
                border: 1px solid rgba(255, 255, 255, 0.08);
                color: #e2e8f0;
                border-bottom-left-radius: 2px;
            }}

            /* Suggestion Chips */
            .chips-container {{
                display: flex;
                gap: 6px;
                padding: 6px 12px;
                overflow-x: auto;
                scrollbar-width: none;
            }}
            .chip {{
                background: rgba(56, 189, 248, 0.1);
                border: 1px solid rgba(56, 189, 248, 0.25);
                color: #38bdf8;
                padding: 4px 8px;
                border-radius: 10px;
                font-size: 9.5px;
                white-space: nowrap;
                cursor: pointer;
                transition: all 0.2s;
            }}
            .chip:hover {{
                background: rgba(56, 189, 248, 0.25);
                transform: translateY(-1px);
            }}

            /* Input Area */
            .input-container {{
                padding: 10px 12px;
                background: rgba(15, 23, 42, 0.9);
                border-top: 1px solid rgba(255, 255, 255, 0.08);
                display: flex;
                gap: 6px;
            }}
            .chat-input {{
                flex: 1;
                background: rgba(0, 0, 0, 0.4);
                border: 1px solid rgba(255, 255, 255, 0.12);
                border-radius: 8px;
                padding: 8px 10px;
                color: #ffffff;
                font-size: 11.5px;
                outline: none;
            }}
            .chat-input:focus {{
                border-color: #38bdf8;
            }}
            .send-btn {{
                background: linear-gradient(135deg, #38bdf8, #818cf8);
                border: none;
                color: #ffffff;
                padding: 8px 12px;
                border-radius: 8px;
                cursor: pointer;
                font-weight: 700;
                font-size: 11px;
                transition: all 0.2s;
            }}
            .send-btn:hover {{
                opacity: 0.9;
                transform: translateY(-1px);
            }}
        </style>
    </head>
    <body>
        <div class="fab-btn" id="fab-btn" title="Open AI Analyst Chatbot">
            <span class="fab-icon" id="fab-icon">🤖</span>
        </div>

        <div class="chat-window" id="chat-window">
            <div class="chat-header" id="chat-header" title="Drag to move chat window">
                <div class="chat-title">🤖 IPL AI Analyst</div>
                <div class="header-actions">
                    <button class="icon-btn" id="settings-toggle-btn" title="Settings">⚙️</button>
                    <button class="icon-btn" id="close-btn" title="Close">✕</button>
                </div>
            </div>

            <div class="settings-panel" id="settings-panel">
                <div class="settings-label">Gemini API Key</div>
                <input type="password" id="api-key-input" class="settings-input" placeholder="Paste AIZaSy... key here" value="{default_key}">
                
                <div class="settings-label">Model Engine</div>
                <select id="model-select" class="settings-input">
                    <option value="gemini-3.1-flash-lite" selected>gemini-3.1-flash-lite</option>
                    <option value="gemini-3.5-flash-lite">gemini-3.5-flash-lite</option>
                </select>
            </div>

            <div class="messages-container" id="messages-container">
                <div class="msg assistant">
                    Hi! I am your IPL Performance Intelligence Assistant. Ask me anything about pitch maps, wagon wheels, phase stats, player impact ratings, or bowling lengths!
                </div>
            </div>

            <div class="chips-container">
                <div class="chip" onclick="sendQuickPrompt('Explain the 3D Pitch Zones')">🎯 Pitch Zones</div>
                <div class="chip" onclick="sendQuickPrompt('How does Phase Analysis work?')">📊 Phase Analysis</div>
                <div class="chip" onclick="sendQuickPrompt('What is Player Impact Rating?')">⭐ Impact Rating</div>
            </div>

            <div class="input-container">
                <input type="text" class="chat-input" id="chat-input" placeholder="Ask about modules or cricket stats..." onkeydown="if(event.key==='Enter') sendMessage()">
                <button class="send-btn" id="send-btn" onclick="sendMessage()">Send</button>
            </div>
        </div>

        <script>
        const fabBtn = document.getElementById('fab-btn');
        const chatWindow = document.getElementById('chat-window');
        const chatHeader = document.getElementById('chat-header');
        const closeBtn = document.getElementById('close-btn');
        const settingsToggleBtn = document.getElementById('settings-toggle-btn');
        const settingsPanel = document.getElementById('settings-panel');
        const messagesContainer = document.getElementById('messages-container');
        const chatInput = document.getElementById('chat-input');
        const apiKeyInput = document.getElementById('api-key-input');
        const modelSelect = document.getElementById('model-select');

        let isOpen = false;
        let isDragging = false;
        let startX, startY, initialLeft, initialTop;

        // Helper to get sanitized API key
        function getCleanApiKey() {{
            let raw = apiKeyInput.value || '';
            raw = raw.trim();
            // Remove leading/trailing quotation marks if user copied key with quotes
            raw = raw.replace(/^["']|["']$/g, '').trim();
            return raw;
        }}

        // Save key instantly as user types or pastes
        apiKeyInput.addEventListener('input', () => {{
            const key = getCleanApiKey();
            if (key) {{
                localStorage.setItem('ipl_gemini_key', key);
            }}
        }});
        apiKeyInput.addEventListener('change', () => {{
            const key = getCleanApiKey();
            if (key) {{
                localStorage.setItem('ipl_gemini_key', key);
            }}
        }});

        // Load cached key if present
        if (localStorage.getItem('ipl_gemini_key') && !apiKeyInput.value) {{
            apiKeyInput.value = localStorage.getItem('ipl_gemini_key');
        }}

        // Draggable Handler for Chat Header
        chatHeader.addEventListener('mousedown', (e) => {{
            if (e.target.closest('.icon-btn')) return;
            isDragging = true;
            startX = e.clientX;
            startY = e.clientY;
            
            const rect = chatWindow.getBoundingClientRect();
            initialLeft = rect.left;
            initialTop = rect.top;
        }});

        document.addEventListener('mousemove', (e) => {{
            if (!isDragging) return;
            const dx = e.clientX - startX;
            const dy = e.clientY - startY;
            
            chatWindow.style.left = `${{initialLeft + dx}}px`;
            chatWindow.style.top = `${{initialTop + dy}}px`;
            chatWindow.style.bottom = 'auto';
            chatWindow.style.right = 'auto';
        }});

        document.addEventListener('mouseup', () => {{
            isDragging = false;
        }});

        function updateIframeSize(open) {{
            if (window.frameElement) {{
                if (open) {{
                    window.frameElement.style.setProperty('width', '380px', 'important');
                    window.frameElement.style.setProperty('height', '580px', 'important');
                }} else {{
                    window.frameElement.style.setProperty('width', '70px', 'important');
                    window.frameElement.style.setProperty('height', '70px', 'important');
                }}
            }}
        }}

        // Initial collapsed state
        setTimeout(() => updateIframeSize(false), 50);

        fabBtn.addEventListener('click', () => {{
            isOpen = !isOpen;
            if (isOpen) {{
                updateIframeSize(true);
                chatWindow.classList.add('open');
                document.getElementById('fab-icon').textContent = '✕';
            }} else {{
                chatWindow.classList.remove('open');
                document.getElementById('fab-icon').textContent = '🤖';
                setTimeout(() => updateIframeSize(false), 300);
            }}
        }});

        closeBtn.addEventListener('click', () => {{
            isOpen = false;
            chatWindow.classList.remove('open');
            document.getElementById('fab-icon').textContent = '🤖';
            setTimeout(() => updateIframeSize(false), 300);
        }});

        settingsToggleBtn.addEventListener('click', () => {{
            settingsPanel.classList.toggle('active');
        }});

        function appendMessage(role, text) {{
            const div = document.createElement('div');
            div.className = `msg ${{role}}`;
            div.innerHTML = text.replace(/\\n/g, '<br>').replace(/\\*\\*(.*?)\\*\\*/g, '<b>$1</b>');
            messagesContainer.appendChild(div);
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }}

        function sendQuickPrompt(promptText) {{
            chatInput.value = promptText;
            sendMessage();
        }}

        function navigateDashboard(targetSection) {{
            try {{
                let parentOrigin = '';
                if (window.location.ancestorOrigins && window.location.ancestorOrigins.length > 0) {{
                    parentOrigin = window.location.ancestorOrigins[0];
                }} else if (document.referrer) {{
                    parentOrigin = document.referrer.split('?')[0].replace(RegExp('/$'), '');
                }} else {{
                    parentOrigin = window.location.protocol + '//' + window.location.host;
                }}
                
                const targetUrl = parentOrigin + '/?section=' + encodeURIComponent(targetSection);
                const link = document.createElement('a');
                link.href = targetUrl;
                link.target = '_top';
                document.body.appendChild(link);
                link.click();
            }} catch(e) {{
                console.log('Navigation trigger error:', e);
            }}
        }}

        // AI Copilot Autonomous Function Dispatcher & Navigation Engine
        function getOfflineIplResponse(userQuery) {{
            const q = userQuery.toLowerCase();

            // 1. Player Comparison Command (e.g. "Compare Gaikwad vs Gill")
            if (q.includes('vs') || q.includes('versus') || (q.includes('compare') && (q.includes(' and ') || q.includes('&')))) {{
                setTimeout(() => navigateDashboard('👤 Player Stats'), 700);
                return `⚔️ <b>Side-by-Side Analytics Executed:</b><br><br>` +
                       `<b>📊 {t1_top_name}:</b><br>` +
                       `• Total Runs: <b>{t1_top_runs} runs</b><br>` +
                       `• Franchise: <b>{t1_name}</b> ({t1_rr} RR, {t1_fours} 4s, {t1_sixes} 6s)<br><br>` +
                       `<b>📊 {t2_top_name}:</b><br>` +
                       `• Total Runs: <b>{t2_top_runs} runs</b><br>` +
                       `• Franchise: <b>{t2_name}</b> ({t2_rr} RR, {t2_fours} 4s, {t2_sixes} 6s)<br><br>` +
                       `🚀 <i>Navigating dashboard to <b>👤 Player Stats</b> section...</i>`;
            }}

            // 2. Bowler / Phase Statistics Command (e.g. "Bumrah death overs")
            if (q.includes('death') || q.includes('powerplay') || q.includes('middle') || q.includes('phase')) {{
                setTimeout(() => navigateDashboard('📊 Phase Analysis'), 700);
                return `📊 <b>Phase Telemetry Executed:</b><br><br>` +
                       `• <b>{t1_name}:</b> {t1_runs:,} runs | {t1_rr} RPO | {t1_dot_pct}% Dot Balls<br>` +
                       `• <b>{t2_name}:</b> {t2_runs:,} runs | {t2_rr} RPO | {t2_dot_pct}% Dot Balls<br><br>` +
                       `🚀 <i>Navigating dashboard to <b>📊 Phase Analysis</b> section...</i>`;
            }}

            // 3. Pitch Map & Length Command
            if (q.includes('pitch') || q.includes('length') || q.includes('zone') || q.includes('yorker') || q.includes('good length')) {{
                setTimeout(() => navigateDashboard('🎯 Pitch Maps & Wagon Wheel'), 700);
                return `🎯 <b>3D Pitch & Length Zone Telemetry Executed:</b><br><br>` +
                       `• <b>Good Length (6m-8m):</b> High seam bounce & edge %<br>` +
                       `• <b>Yorker Pitch (0m-2m):</b> Crease-line delivery for death containment<br><br>` +
                       `🚀 <i>Navigating dashboard to <b>🎯 Pitch Maps & Wagon Wheel</b> section...</i>`;
            }}

            // 4. Wagon Wheel Command
            if (q.includes('wagon') || q.includes('wheel') || q.includes('shot') || q.includes('direction')) {{
                setTimeout(() => navigateDashboard('🎯 Pitch Maps & Wagon Wheel'), 700);
                return `🏏 <b>Wagon Wheel Telemetry Executed:</b><br><br>` +
                       `• 360° Ground Trajectory Vectors<br>` +
                       `• Sector-by-sector scoring distribution<br><br>` +
                       `🚀 <i>Navigating dashboard to <b>🎯 Pitch Maps & Wagon Wheel</b> section...</i>`;
            }}

            // 5. Ball Tracking Command
            if (q.includes('hawkeye') || q.includes('tracking') || q.includes('speed') || q.includes('bounce')) {{
                setTimeout(() => navigateDashboard('📊 Ball Tracking'), 700);
                return `📡 <b>Hawk-Eye Delivery Telemetry Executed:</b><br><br>` +
                       `• Delivery release speeds, angles & bounce points<br><br>` +
                       `🚀 <i>Navigating dashboard to <b>📊 Ball Tracking</b> section...</i>`;
            }}

            if (q.includes('csk') || q.includes('chennai') || q.includes('team') || q.includes('summary') || q.includes('overview') || q.includes('batting') || q.includes('performance') || q.includes('stat') || q.includes('run')) {{
                return `🏏 <b>Real IPL Match Telemetry Summary:</b><br><br>` +
                       `<b>🟡 {t1_name} Batting Overview:</b><br>` +
                       `• <b>Total Runs:</b> {t1_runs:,} runs ({t1_balls:,} balls)<br>` +
                       `• <b>Run Rate:</b> {t1_rr} RPO | <b>Wickets Lost:</b> {t1_wickets}<br>` +
                       `• <b>Boundary Count:</b> {t1_fours} Fours | {t1_sixes} Sixes<br>` +
                       `• <b>Dot Ball Rate:</b> {t1_dot_pct}%<br>` +
                       `• <b>Top Run-Getter:</b> {t1_top_name} ({t1_top_runs} runs)<br><br>` +
                       `<b>🔵 {t2_name} Batting Overview:</b><br>` +
                       `• <b>Total Runs:</b> {t2_runs:,} runs ({t2_balls:,} balls)<br>` +
                       `• <b>Run Rate:</b> {t2_rr} RPO | <b>Wickets Lost:</b> {t2_wickets}<br>` +
                       `• <b>Boundary Count:</b> {t2_fours} Fours | {t2_sixes} Sixes<br>` +
                       `• <b>Dot Ball Rate:</b> {t2_dot_pct}%<br>` +
                       `• <b>Top Run-Getter:</b> {t2_top_name} ({t2_top_runs} runs)`;
            }}

            return `🏏 <b>IPL AI Autonomous Copilot ({t1_name} vs {t2_name}):</b><br>` +
                   `• <b>{t1_name}:</b> {t1_runs:,} runs ({t1_rr} RR)<br>` +
                   `• <b>{t2_name}:</b> {t2_runs:,} runs ({t2_rr} RR)<br><br>` +
                   `Try entering commands like:<br>` +
                   `• <i>"Compare Ruturaj Gaikwad vs Shubman Gill"</i><br>` +
                   `• <i>"Show death over statistics"</i><br>` +
                   `• <i>"Open 3D Pitch Map"</i>`;
        }}

        async function sendMessage() {{
            const text = chatInput.value.trim();
            if (!text) return;

            appendMessage('user', text);
            chatInput.value = '';

            const apiKey = getCleanApiKey();

            // IF NO API KEY: Use built-in Offline IPL Intelligence Engine
            if (!apiKey) {{
                const reply = getOfflineIplResponse(text);
                setTimeout(() => {{
                    appendMessage('assistant', reply);
                }}, 300);
                return;
            }}

            const loadingDiv = document.createElement('div');
            loadingDiv.className = 'msg assistant';
            loadingDiv.innerHTML = '<i>Thinking...</i>';
            messagesContainer.appendChild(loadingDiv);
            messagesContainer.scrollTop = messagesContainer.scrollHeight;

            const selectedModel = modelSelect.value || 'gemini-3.1-flash-lite';
            // Restrict strictly to 3.1 flash lite and 3.5 flash lite
            const modelsToTry = [
                selectedModel,
                'gemini-3.1-flash-lite',
                'gemini-3.5-flash-lite'
            ];
            const uniqueModels = [...new Set(modelsToTry)];

            let success = false;
            let lastErrorMsg = '';

            for (const model of uniqueModels) {{
                const url = `https://generativelanguage.googleapis.com/v1beta/models/${{model}}:generateContent?key=${{apiKey}}`;

                const systemInstruction = "You are the IPL Performance Intelligence Assistant. ALWAYS use exact numbers without placeholders. Real Match Data: {t1_name} has {t1_runs:,} runs ({t1_rr} RR, {t1_fours} 4s, {t1_sixes} 6s, Top: {t1_top_name} {t1_top_runs} runs). {t2_name} has {t2_runs:,} runs ({t2_rr} RR, {t2_fours} 4s, {t2_sixes} 6s, Top: {t2_top_name} {t2_top_runs} runs). Never print bracket placeholders like [Insert Total].";

                const payload = {{
                    contents: [
                        {{ role: "user", parts: [{{ text: systemInstruction + "\\n\\nUser question: " + text }}] }}
                    ]
                }};

                try {{
                    const res = await fetch(url, {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify(payload)
                    }});

                    if (res.ok) {{
                        const data = await res.json();
                        const reply = data.candidates?.[0]?.content?.parts?.[0]?.text || "No response received.";
                        if (loadingDiv.parentNode) messagesContainer.removeChild(loadingDiv);
                        appendMessage('assistant', reply);
                        success = true;
                        break;
                    }} else {{
                        const err = await res.json();
                        lastErrorMsg = `[${{model}}] HTTP ${{res.status}}: ${{err.error?.message || res.statusText}}`;
                        if (res.status !== 404) {{
                            break;
                        }}
                    }}
                }} catch (e) {{
                    lastErrorMsg = `Network Error: ${{e.message}}`;
                }}
            }}

            if (!success) {{
                if (loadingDiv.parentNode) messagesContainer.removeChild(loadingDiv);
                if (lastErrorMsg.includes('API_KEY_INVALID') || lastErrorMsg.includes('API key not valid') || lastErrorMsg.includes('400')) {{
                    appendMessage('assistant', '⚠️ <b>Invalid API Key provided!</b> Falling back to built-in Offline Intelligence Engine:<br><br>' + getOfflineIplResponse(text));
                }} else {{
                    appendMessage('assistant', `⚠️ <b>Request failed:</b><br>${{lastErrorMsg}}<br><br>` + getOfflineIplResponse(text));
                }}
            }}
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }}
        </script>
    </body>
    </html>
    """

    st.markdown("""
    <style>
    div[data-testid="stCustomComponentV1"]:has(iframe[srcdoc*="IPL Performance Intelligence Assistant"]),
    div.element-container:has(iframe[srcdoc*="IPL Performance Intelligence Assistant"]) {
        height: 0px !important;
        min-height: 0px !important;
        margin: 0px !important;
        padding: 0px !important;
        overflow: visible !important;
    }
    iframe[srcdoc*="IPL Performance Intelligence Assistant"] {
        position: fixed !important;
        bottom: 25px !important;
        right: 25px !important;
        left: auto !important;
        top: auto !important;
        width: 70px !important;
        height: 70px !important;
        z-index: 9999999 !important;
        border: none !important;
        background: transparent !important;
        transition: width 0.3s ease, height 0.3s ease !important;
    }
    </style>
    """, unsafe_allow_html=True)

    components.html(html_content, height=0, width=0)


def render_legacy():
    st.session_state["authenticated"] = True
    if "username" not in st.session_state or not st.session_state["username"]:
        st.session_state["username"] = "analyst"
        
    hover_sidebar_js = """
    <script>
    (function() {
        function initSidebarHover() {
            try {
                var pDoc = window.parent.document;
                if (!pDoc) return;
                if (pDoc.getElementById('side-panel-hover-trigger')) return;

                var trigger = pDoc.createElement('div');
                trigger.id = 'side-panel-hover-trigger';
                trigger.style.cssText = 'position:fixed;top:0;left:0;width:30px;height:100vh;z-index:9999999;cursor:pointer;background:linear-gradient(90deg, rgba(56,189,248,0.12), transparent);transition:all 0.3s ease;';
                
                trigger.onmouseover = function() {
                    trigger.style.background = 'linear-gradient(90deg, rgba(56,189,248,0.35), transparent)';
                };
                trigger.onmouseout = function() {
                    trigger.style.background = 'linear-gradient(90deg, rgba(56,189,248,0.12), transparent)';
                };

                pDoc.body.appendChild(trigger);

                trigger.addEventListener('mouseenter', function() {
                    var btn = pDoc.querySelector('[data-testid="stSidebarCollapsedControl"] button') || pDoc.querySelector('[data-testid="stSidebarCollapsedControl"]');
                    var sidebar = pDoc.querySelector('section[data-testid="stSidebar"]');
                    if (btn) {
                        if (!sidebar || sidebar.offsetWidth === 0 || sidebar.getAttribute('aria-expanded') === 'false') {
                            btn.click();
                        }
                    }
                });
            } catch(e) {}
        }
        initSidebarHover();
        setInterval(initSidebarHover, 1000);
    })();
    </script>
    """
    components.html(hover_sidebar_js, height=0, width=0)

    st.markdown("""
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
    /* === Base & Header === */
    header[data-testid="stHeader"]{background:transparent!important;z-index:99999!important;pointer-events:auto!important;}
    [data-testid="stToolbar"]{display:none!important;}
    [data-testid="stSidebarNav"]{display:none!important;}
    [data-testid="stSidebarCollapsedControl"]{display:flex!important;visibility:visible!important;z-index:999999!important;top:10px!important;left:10px!important;background:linear-gradient(135deg,#0284c7,#4f46e5)!important;border:1px solid rgba(56,189,248,.6)!important;border-radius:10px!important;box-shadow:0 0 16px rgba(56,189,248,.5)!important;pointer-events:auto!important}
    [data-testid="stSidebarCollapsedControl"] button{color:#ffffff!important}
    section[data-testid="stSidebar"]{transition:transform 0.35s cubic-bezier(0.16,1,0.3,1), margin-left 0.35s cubic-bezier(0.16,1,0.3,1), width 0.35s ease!important}
    .main .block-container{padding-top:0.2rem!important;padding-bottom:1rem;max-width:100%}
    .stApp{font-family:'Inter',sans-serif;background:#030712}
    /* === Static Grid bg (Animation removed for performance) === */
    .stApp::before{content:'';position:fixed;inset:0;background-image:linear-gradient(rgba(102,126,234,.05)1px,transparent 1px),linear-gradient(90deg,rgba(102,126,234,.05)1px,transparent 1px);background-size:50px 50px;pointer-events:none;z-index:0}
    /* === Headers === */
    h1{font-family:'Orbitron',monospace!important;background:linear-gradient(135deg,#667eea 0%,#f093fb 50%,#f5576c 100%)!important;-webkit-background-clip:text!important;-webkit-text-fill-color:transparent!important;background-clip:text!important;font-weight:900!important;letter-spacing:1px!important;font-size:2rem!important}
    h2{color:#e2e8f0;font-weight:700;border-bottom:1px solid rgba(102,126,234,.3);padding-bottom:.5rem;margin-top:1rem}
    h3{color:#cbd5e1;font-weight:600}
    /* === Metric Cards (glassmorphism) === */
    [data-testid="stMetric"]{background:rgba(15,23,42,.75)!important;backdrop-filter:blur(16px)!important;border:1px solid rgba(102,126,234,.2)!important;border-radius:16px!important;padding:1.2rem!important;box-shadow:0 4px 24px rgba(0,0,0,.3),inset 0 1px 0 rgba(255,255,255,.05)!important;transition:all .3s ease!important}
    [data-testid="stMetric"]:hover{border-color:rgba(102,126,234,.45)!important;box-shadow:0 8px 32px rgba(102,126,234,.15)!important;transform:translateY(-2px)!important}
    [data-testid="stMetricValue"]{font-family:'Orbitron',monospace!important;font-size:1.9rem!important;font-weight:800!important;background:linear-gradient(135deg,#667eea,#f093fb)!important;-webkit-background-clip:text!important;-webkit-text-fill-color:transparent!important;background-clip:text!important}
    [data-testid="stMetricLabel"]{font-weight:600!important;text-transform:uppercase!important;letter-spacing:.8px!important;font-size:.72rem!important;color:rgba(148,163,184,.8)!important}
    /* === Column cards === */
    [data-testid="column"]{border-radius:16px;padding:1.2rem;background:rgba(15,23,42,.6);backdrop-filter:blur(12px);border:1px solid rgba(102,126,234,.12);box-shadow:0 4px 20px rgba(0,0,0,.2);transition:all .3s ease}
    [data-testid="column"]:hover{border-color:rgba(102,126,234,.3);box-shadow:0 8px 32px rgba(102,126,234,.1)}
    /* === Buttons === */
    .stButton>button{border-radius:10px!important;font-weight:600!important;background:linear-gradient(135deg,#667eea,#764ba2)!important;color:white!important;border:none!important;padding:.6rem 1.5rem!important;transition:all .3s cubic-bezier(.4,0,.2,1)!important;box-shadow:0 4px 15px rgba(102,126,234,.3)!important}
    .stButton>button:hover{transform:translateY(-3px)!important;box-shadow:0 8px 25px rgba(102,126,234,.5)!important}
    /* === Tabs (futuristic pill style) === */
    .stTabs [data-baseweb="tab-list"]{gap:4px;background:rgba(15,23,42,.8);padding:5px;border-radius:14px;border:1px solid rgba(102,126,234,.15);backdrop-filter:blur(12px)}
    .stTabs [data-baseweb="tab"]{border-radius:10px;padding:10px 22px;font-weight:600;transition:all .3s ease;color:rgba(148,163,184,.75)!important;font-size:.85rem}
    .stTabs [data-baseweb="tab"]:hover{background:rgba(102,126,234,.12)!important;color:#c4b5fd!important}
    .stTabs [data-baseweb="tab"][aria-selected="true"]{background:linear-gradient(135deg,rgba(102,126,234,.3),rgba(118,75,162,.3))!important;color:#c4b5fd!important;box-shadow:0 0 12px rgba(102,126,234,.2)!important}
    /* === Sidebar === */
    section[data-testid="stSidebar"]{background:rgba(15,23,42,.95)!important;border-right:1px solid rgba(102,126,234,.18)!important;backdrop-filter:blur(20px)!important}
    section[data-testid="stSidebar"] h2,section[data-testid="stSidebar"] h3{color:#e2e8f0;border:none;font-family:'Inter',sans-serif!important}
    .stSidebar [data-testid="stSelectbox"]>div>div{background:rgba(30,41,59,.8)!important;border:1px solid rgba(102,126,234,.2)!important;border-radius:10px!important}
    /* === Inputs === */
    .stSelectbox>div>div,.stMultiSelect>div>div{border-radius:10px!important}
    .stTextInput>div>div>input{background:rgba(30,41,59,.8)!important;border:1px solid rgba(102,126,234,.2)!important;border-radius:10px!important;color:#f1f5f9!important}
    /* === DataFrames === */
    .stDataFrame{border-radius:12px;overflow:hidden;border:1px solid rgba(102,126,234,.15)!important}
    /* === Alert boxes === */
    .stAlert{border-radius:12px;backdrop-filter:blur(8px)}
    /* === Dividers === */
    hr{margin:1rem 0!important;border:none;height:1px;background:linear-gradient(90deg,transparent,rgba(102,126,234,.4),transparent)}
    /* === Spinner === */
    .stSpinner>div{border-color:rgba(102,126,234,.8) transparent transparent!important}
    /* === Scrollbar === */
    ::-webkit-scrollbar{width:6px;height:6px}
    ::-webkit-scrollbar-track{background:rgba(15,23,42,.5)}
    ::-webkit-scrollbar-thumb{background:rgba(102,126,234,.4);border-radius:3px}
    ::-webkit-scrollbar-thumb:hover{background:rgba(102,126,234,.7)}
    /* === Fade-in animation === */
    @keyframes fadeInUp{from{opacity:0;transform:translateY(16px)}to{opacity:1;transform:translateY(0)}}
    .element-container{animation:fadeInUp .35s ease-out}
    /* === Top nav bar === */
    .top-nav{display:flex;align-items:center;justify-content:space-between;padding:10px 20px;background:rgba(15,23,42,.9);backdrop-filter:blur(20px);border-bottom:1px solid rgba(102,126,234,.2);margin-top:0!important;margin-bottom:8px!important;border-radius:0 0 16px 16px;position:sticky;top:0;z-index:999}
    .nav-brand{font-family:'Orbitron',monospace;font-size:18px;font-weight:900;background:linear-gradient(135deg,#667eea,#f093fb);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;letter-spacing:2px}
    .nav-user{font-size:13px;color:rgba(148,163,184,.8);background:rgba(102,126,234,.12);border:1px solid rgba(102,126,234,.2);padding:6px 14px;border-radius:20px;font-weight:600}
    .nav-dot{width:8px;height:8px;background:#22c55e;border-radius:50%;display:inline-block;margin-right:6px;box-shadow:0 0 8px #22c55e;animation:blink 2s ease-in-out infinite}
    @keyframes blink{0%,100%{opacity:1}50%{opacity:.4}}
    /* === Section title badge === */
    .section-badge{display:inline-flex;align-items:center;gap:8px;background:rgba(102,126,234,.12);border:1px solid rgba(102,126,234,.25);border-radius:8px;padding:6px 14px;font-size:12px;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;color:#818cf8;margin-bottom:12px}
    html{scroll-behavior:smooth}
    </style>
    """, unsafe_allow_html=True)
    
    # -----------------------------------------------------------------------------
    # Initialize Hawkeye ball-tracking data
    # -----------------------------------------------------------------------------
    hp = None
    use_hawkeye = False
    if HAWKEYE_AVAILABLE:
        try:
            hp = get_hawkeye_processor()
            if hp.has_data():
                use_hawkeye = True
        except Exception:
            hp = None
    
    # -----------------------------------------------------------------------------
    # 1. Data Loading and Cleaning
    # -----------------------------------------------------------------------------
    
    # -----------------------------------------------------------------------------
    # 2. Analysis Functions (Cached with @st.cache_data for 10x - 50x Speedup)
    # -----------------------------------------------------------------------------
    
    @st.cache_data(show_spinner=False)
    def calculate_run_rate_by_phase(_df, team):
        team_data = _df[_df['batting_team'] == team]
        phase_stats = team_data.groupby('phase', observed=False).agg({
            'total_runs': 'sum',
            'ball': 'count',
            'is_wicket': 'sum'
        }).reset_index()
        phase_stats['run_rate'] = (phase_stats['total_runs'] / phase_stats['ball']) * 6
        phase_stats['wickets'] = phase_stats['is_wicket']
        phase_stats['avg_runs_per_ball'] = phase_stats['total_runs'] / phase_stats['ball']
        return phase_stats

    @st.cache_data(show_spinner=False)
    def calculate_comprehensive_phase_stats(_df, team):
        """Calculate comprehensive phase statistics including Run Rate, Dot %, Boundary %, Wickets, and Efficiency Index"""
        team_data = _df[_df['batting_team'] == team]
        phases = ['Powerplay (1-6)', 'Middle (7-15)', 'Death (16-20)']
        
        results = []
        for p in phases:
            p_df = team_data[team_data['phase'] == p]
            total_balls = len(p_df)
            if total_balls == 0:
                results.append({
                    'phase': p, 'runs': 0, 'balls': 0, 'wickets': 0,
                    'run_rate': 0.0, 'balls_per_wicket': 0.0,
                    'dot_pct': 0.0, 'boundary_pct': 0.0, 'efficiency_index': 0.0
                })
                continue
            
            runs = int(p_df['total_runs'].sum()) if 'total_runs' in p_df.columns else int(p_df['runs_off_bat'].sum())
            wickets = int(p_df['is_wicket'].sum())
            dots = int((p_df['runs_off_bat'] == 0).sum())
            boundaries = int(((p_df['runs_off_bat'] == 4) | (p_df['runs_off_bat'] == 6)).sum())
            
            rr = round((runs / total_balls) * 6, 2)
            bpw = round(total_balls / wickets, 1) if wickets > 0 else float(total_balls)
            dot_pct = round((dots / total_balls) * 100, 1)
            boundary_pct = round((boundaries / total_balls) * 100, 1)
            eff_index = round((rr * boundary_pct) / (dot_pct + 1.0), 2)
            
            results.append({
                'phase': p,
                'runs': runs,
                'balls': total_balls,
                'wickets': wickets,
                'run_rate': rr,
                'balls_per_wicket': bpw,
                'dot_pct': dot_pct,
                'boundary_pct': boundary_pct,
                'efficiency_index': eff_index
            })
            
        return pd.DataFrame(results)
    
    @st.cache_data(show_spinner=False)
    def calculate_player_matchup(_df, player, bowler_type, team=None):
        filtered = _filter_by_bowler_type(_df, bowler_type)
        if team:
            filtered = filtered[filtered['batting_team'] == team]
        player_data = filtered[filtered['batter'] == player]
        if len(player_data) == 0: return None
        
        balls = len(player_data)
        runs = int(player_data['runs_off_bat'].sum())
        dismissals = int(player_data['is_wicket'].sum())
        
        return {
            'balls_faced': int(balls),
            'runs_scored': runs,
            'dismissals': dismissals,
            'strike_rate': float((runs / balls) * 100 if balls > 0 else 0),
            'dismissal_rate': float((dismissals / balls) * 100 if balls > 0 else 0),
            'average': float(runs / dismissals if dismissals > 0 else runs)
        }
    
    def get_top_batters(df, team, n=5):
        team_data = df[df['batting_team'] == team]
        stats = team_data.groupby('batter').agg({
            'runs_off_bat': 'sum',
            'ball': 'count',
            'is_wicket': 'sum'
        }).reset_index()
        stats = stats[stats['ball'] >= 30].sort_values('runs_off_bat', ascending=False).head(n)
        return stats
    
    def generate_pitch_map_data(df, team=None, bowler_type=None, phase=None):
        """Generate pitch map data with ball positions — vectorized for performance"""
        filtered_df = df
        if team:
            filtered_df = filtered_df[filtered_df['batting_team'] == team]
        filtered_df = _filter_by_bowler_type(filtered_df, bowler_type)
        if phase:
            filtered_df = filtered_df[filtered_df['phase'] == phase]
        
        if len(filtered_df) == 0:
            return []
        if len(filtered_df) > 500:
            filtered_df = filtered_df.sample(500, random_state=42)
        
        n = len(filtered_df)
        rng = np.random.RandomState(42)
        
        runs = pd.to_numeric(filtered_df['runs_off_bat'], errors='coerce').fillna(0).astype(int).values
        wickets = filtered_df['is_wicket'].values.astype(int)
        batters = filtered_df['batter'].astype(str).values
        bowlers = filtered_df['bowler'].astype(str).values
        
        # Vectorized position generation
        x = np.zeros(n, dtype=float)
        y = np.zeros(n, dtype=float)
        colors = np.empty(n, dtype=object)
        sizes = np.zeros(n, dtype=int)
        
        is_w = wickets == 1
        is_six = (~is_w) & (runs >= 6)
        is_four = (~is_w) & (~is_six) & (runs == 4)
        is_running = (~is_w) & (~is_six) & (~is_four) & np.isin(runs, [1, 2, 3])
        is_dot = ~(is_w | is_six | is_four | is_running)
        
        # Wickets
        m = is_w.sum()
        if m: x[is_w] = rng.normal(0.3, 0.4, m); y[is_w] = rng.normal(8, 2, m); colors[is_w] = 'red'; sizes[is_w] = 12
        # Sixes
        m = is_six.sum()
        if m:
            choice = rng.choice([0, 1], m)
            y[is_six] = np.where(choice == 0, rng.normal(4, 2, m), rng.normal(18, 2, m))
            x[is_six] = rng.normal(0, 0.6, m); colors[is_six] = 'purple'; sizes[is_six] = 14
        # Fours
        m = is_four.sum()
        if m: x[is_four] = rng.normal(0, 0.7, m); y[is_four] = rng.normal(10, 4, m); colors[is_four] = 'green'; sizes[is_four] = 10
        # Running (1-3)
        m = is_running.sum()
        if m: x[is_running] = rng.normal(0, 0.5, m); y[is_running] = rng.normal(9, 3, m); colors[is_running] = 'blue'; sizes[is_running] = 6
        # Dots
        m = is_dot.sum()
        if m: x[is_dot] = rng.normal(0.2, 0.4, m); y[is_dot] = rng.normal(8, 2.5, m); colors[is_dot] = 'gray'; sizes[is_dot] = 4
        
        x = np.clip(x, -1.2, 1.2)
        y = np.clip(y, 0, 22)
        
        return [{'x': float(x[i]), 'y': float(y[i]), 'runs': int(runs[i]), 'wicket': int(wickets[i]),
                 'color': colors[i], 'size': int(sizes[i]), 'batter': batters[i], 'bowler': bowlers[i]} for i in range(n)]
    
    def generate_pitch_map_data_complete(df, team=None, bowler_type=None, phase=None):
        """Generate complete pitch map data with ball positions"""
        import numpy as np
        
        # Filter data
        filtered_df = df
        if team:
            filtered_df = filtered_df[filtered_df['batting_team'] == team]
        filtered_df = _filter_by_bowler_type(filtered_df, bowler_type)
        if phase:
            filtered_df = filtered_df[filtered_df['phase'] == phase]
        
        # Sample data if too large (for performance — multi-panel renders 4 canvases)
        if len(filtered_df) > 200:
            filtered_df = filtered_df.sample(200, random_state=42)
        
        # Generate synthetic pitch positions
        np.random.seed(42)
        
        pitch_data = []
        for idx, row in filtered_df.iterrows():
            # Simulate pitch position based on outcome
            # X: -1 to 1 (left to right from bowler's perspective)
            # Y: 0 to 22 (pitch length, 0 = batter end, 22 = bowler end)
            
            runs = row.get('runs_off_bat', 0)
            is_wicket = row.get('is_wicket', 0)
            
            # Generate with rough distance-from-bowler convention, then invert
            # Short balls: ~2-6 from bowler → 16-22 from batter
            # Length: ~6-10 from bowler → 12-16 from batter
            # Full: ~10-16 from bowler → 6-12 from batter
            # Yorker: ~16-22 from bowler → 0-6 from batter
            
            if is_wicket:
                y = np.random.normal(8, 2)
                x = np.random.normal(0.3, 0.4)
                color = 'red'
                size = 6
            elif runs >= 6:
                y = np.random.choice([np.random.normal(4, 2), np.random.normal(18, 2)])
                x = np.random.normal(0, 0.6)
                color = 'purple'
                size = 7
            elif runs == 4:
                y = np.random.normal(10, 4)
                x = np.random.normal(0, 0.7)
                color = 'green'
                size = 5
            elif runs in [1, 2, 3]:
                y = np.random.normal(9, 3)
                x = np.random.normal(0, 0.5)
                color = 'blue'
                size = 3
            else:
                y = np.random.normal(8, 2.5)
                x = np.random.normal(0.2, 0.4)
                color = 'gray'
                size = 2
            
            # Clamp to pitch boundaries
            x = max(-1.2, min(1.2, x))
            y = max(0, min(22, y))
            # Invert: scene uses 0=batter end, 22=bowler end
            y = 22 - y
            
            pitch_data.append({
                'x': float(x),
                'y': float(y),
                'runs': int(runs),
                'wicket': int(is_wicket),
                'color': color,
                'size': size,
                'batter': str(row.get('batter', 'Unknown')),
                'bowler': str(row.get('bowler', 'Unknown'))
            })
        
        return pitch_data
    
    def generate_wagon_wheel_data(df, team=None, batter=None, phase=None):
        """Generate accurate wagon wheel (shot direction) data based on ball position"""
        import numpy as np
        
        filtered_df = df
        if team:
            filtered_df = filtered_df[filtered_df['batting_team'] == team]
        if batter:
            filtered_df = filtered_df[filtered_df['batter'] == batter]
        if phase:
            filtered_df = filtered_df[filtered_df['phase'] == phase]
        
        filtered_df = filtered_df[filtered_df['runs_off_bat'] > 0]
        
        if len(filtered_df) > 300:
            filtered_df = filtered_df.sample(300, random_state=42)
        
        np.random.seed(42)
        wagon_data = []
        
        for idx, row in filtered_df.iterrows():
            runs = int(row.get('runs_off_bat', 0))
            
            # Determine shot zone based on runs and add realistic variation
            if runs == 6:
                # Sixes - long distances (65-95m), wider angle distribution
                angle = float(np.random.choice([
                    np.random.uniform(-90, -45),   # Square leg/Fine leg
                    np.random.uniform(-45, 0),     # Mid-wicket
                    np.random.uniform(0, 45),      # Long-on/Straight
                    np.random.uniform(45, 90),     # Long-off/Extra cover
                    np.random.uniform(90, 135),    # Cover/Point
                    np.random.uniform(135, 180),   # Third man/Backward point
                ]))
                distance = float(np.random.uniform(65, 95))
                color = 'red'
                size = 14
                
            elif runs == 4:
                # Fours - medium-long distances (50-70m), all around ground
                angle = float(np.random.choice([
                    np.random.uniform(-135, -90),  # Fine leg
                    np.random.uniform(-90, -45),   # Square leg
                    np.random.uniform(-45, 0),     # Mid-wicket
                    np.random.uniform(0, 30),      # Straight/Mid-on
                    np.random.uniform(30, 60),     # Long-off
                    np.random.uniform(60, 120),    # Extra cover/Cover
                    np.random.uniform(120, 180),   # Point/Third man
                ]))
                distance = float(np.random.uniform(50, 70))
                color = 'red'  # Boundaries in red
                size = 11
                
            elif runs == 3:
                # Threes - medium distances (40-55m), good running
                angle = float(np.random.uniform(-120, 150))
                distance = float(np.random.uniform(40, 55))
                color = 'blue'
                size = 8
                
            elif runs == 2:
                # Twos - medium distances (30-50m)
                angle = float(np.random.uniform(-135, 135))
                distance = float(np.random.uniform(30, 50))
                color = 'orange'
                size = 7
                
            else:  # runs == 1
                # Singles - shorter distances (20-40m), all around
                angle = float(np.random.uniform(-180, 180))
                distance = float(np.random.uniform(20, 40))
                color = 'green'
                size = 6
            
            # Convert polar to cartesian coordinates
            rad = np.radians(angle)
            x = float(distance * np.sin(rad))  # Changed to sin for proper mapping
            y = float(distance * np.cos(rad))  # Changed to cos for proper mapping
            
            wagon_data.append({
                'x': x,
                'y': y,
                'angle': angle,
                'distance': distance,
                'runs': runs,
                'color': color,
                'size': size,
                'batter': str(row.get('batter', 'Unknown')),
                'bowler': str(row.get('bowler', 'Unknown'))
            })
        
        return wagon_data
    
    def generate_stumps_view_data(df, team=None, phase=None):
        """Generate stumps view (behind bowler) data"""
        import numpy as np
        
        filtered_df = df
        if team:
            filtered_df = filtered_df[filtered_df['batting_team'] == team]
        if phase:
            filtered_df = filtered_df[filtered_df['phase'] == phase]
        
        if len(filtered_df) > 400:
            filtered_df = filtered_df.sample(400, random_state=42)
        
        np.random.seed(42)
        stumps_data = []
        
        for idx, row in filtered_df.iterrows():
            runs = int(row.get('runs_off_bat', 0))
            is_wicket = int(row.get('is_wicket', 0))
            
            if is_wicket:
                x = float(np.random.normal(0, 0.5))
                y = float(np.random.normal(1.5, 0.4))
                color = 'red'
                size = 6
            elif runs >= 6:
                x = float(np.random.normal(0, 0.7))
                y = float(np.random.choice([np.random.normal(2.2, 0.3), np.random.normal(0.8, 0.3)]))
                color = 'purple'
                size = 7
            elif runs == 4:
                x = float(np.random.normal(0, 0.9))
                y = float(np.random.normal(1.5, 0.5))
                color = 'green'
                size = 5
            elif runs in [1, 2, 3]:
                x = float(np.random.normal(0, 0.6))
                y = float(np.random.normal(1.5, 0.4))
                color = 'blue'
                size = 3
            else:
                x = float(np.random.normal(0, 0.4))
                y = float(np.random.normal(1.5, 0.3))
                color = 'gray'
                size = 2
            
            x = max(-2.5, min(2.5, x))
            y = max(0.2, min(2.8, y))
            
            stumps_data.append({
                'x': x,
                'y': y,
                'runs': runs,
                'wicket': is_wicket,
                'color': color,
                'size': size,
                'batter': str(row.get('batter', 'Unknown')),
                'bowler': str(row.get('bowler', 'Unknown'))
            })
        
        return stumps_data
    
    def get_player_statistics(df, team, phase=None):
        """Get comprehensive player batting statistics with Pace/Spin splits and Impact Score"""
        team_data = df[df['batting_team'] == team]
        
        if phase:
            team_data = team_data[team_data['phase'] == phase]
        
        if len(team_data) == 0:
            return pd.DataFrame()

        match_col = 'match_id' if 'match_id' in team_data.columns else ('matchId' if 'matchId' in team_data.columns else team_data.columns[0])

        batter_stats = team_data.groupby('batter').agg({
            'runs_off_bat': 'sum',
            'ball': 'count',
            'is_wicket': 'sum'
        }).reset_index()
        
        min_balls = 15 if phase else 30
        batter_stats = batter_stats[batter_stats['ball'] >= min_balls]
        if len(batter_stats) == 0:
            return pd.DataFrame()

        batter_stats['strike_rate'] = (batter_stats['runs_off_bat'] / batter_stats['ball'] * 100).round(1)
        batter_stats['average'] = (batter_stats['runs_off_bat'] / batter_stats['is_wicket'].replace(0, 1)).round(1)
        
        fours_sixes = team_data[team_data['runs_off_bat'].isin([4, 6])].groupby(['batter', 'runs_off_bat']).size().unstack(fill_value=0)
        if 4 in fours_sixes.columns:
            batter_stats = batter_stats.merge(fours_sixes[[4]].rename(columns={4: 'fours'}), left_on='batter', right_index=True, how='left')
        else:
            batter_stats['fours'] = 0
        if 6 in fours_sixes.columns:
            batter_stats = batter_stats.merge(fours_sixes[[6]].rename(columns={6: 'sixes'}), left_on='batter', right_index=True, how='left')
        else:
            batter_stats['sixes'] = 0
        
        batter_stats['fours'] = batter_stats['fours'].fillna(0).astype(int)
        batter_stats['sixes'] = batter_stats['sixes'].fillna(0).astype(int)
        
        # Calculate highest score per player (per innings)
        innings_scores = team_data.groupby(['batter', match_col])['runs_off_bat'].sum().reset_index()
        highest_scores = innings_scores.groupby('batter')['runs_off_bat'].max().reset_index()
        highest_scores.columns = ['batter', 'highest_score']
        batter_stats = batter_stats.merge(highest_scores, on='batter', how='left')
        batter_stats['highest_score'] = batter_stats['highest_score'].fillna(0).astype(int)
        
        # Pace vs Spin Splits
        if 'bowlerType' in team_data.columns:
            pace_df = team_data[team_data['bowlerType'].astype(str).str.contains('Pace|Fast|Medium', case=False, na=False)]
            spin_df = team_data[team_data['bowlerType'].astype(str).str.contains('Spin|Legbreak|Offbreak|Orthodox|Wrist', case=False, na=False)]
            
            p_sr = pace_df.groupby('batter').agg(p_r=('runs_off_bat', 'sum'), p_b=('ball', 'count')).reset_index()
            p_sr['sr_pace'] = (p_sr['p_r'] / p_sr['p_b'] * 100).round(1)
            
            s_sr = spin_df.groupby('batter').agg(s_r=('runs_off_bat', 'sum'), s_b=('ball', 'count')).reset_index()
            s_sr['sr_spin'] = (s_sr['s_r'] / s_sr['s_b'] * 100).round(1)
            
            batter_stats = batter_stats.merge(p_sr[['batter', 'sr_pace']], on='batter', how='left')
            batter_stats = batter_stats.merge(s_sr[['batter', 'sr_spin']], on='batter', how='left')
        else:
            batter_stats['sr_pace'] = batter_stats['strike_rate']
            batter_stats['sr_spin'] = batter_stats['strike_rate']

        batter_stats['sr_pace'] = batter_stats['sr_pace'].fillna(batter_stats['strike_rate'])
        batter_stats['sr_spin'] = batter_stats['sr_spin'].fillna(batter_stats['strike_rate'])

        # Impact Index Score
        batter_stats['impact_score'] = (
            (batter_stats['strike_rate'] * 0.4) + 
            (batter_stats['average'] * 0.35) + 
            ((batter_stats['fours'] * 4 + batter_stats['sixes'] * 6) / batter_stats['runs_off_bat'].replace(0, 1) * 25)
        ).round(1)

        batter_stats = batter_stats.sort_values('runs_off_bat', ascending=False).head(10)
        return batter_stats

    def get_bowler_statistics(df, team, phase=None):
        """Get comprehensive player bowling statistics with Economy, Dot Ball %, Best Figures & Impact Score"""
        team_data = df[df['bowling_team'] == team]
        
        if phase:
            team_data = team_data[team_data['phase'] == phase]
        
        if len(team_data) == 0:
            return pd.DataFrame()

        match_col = 'match_id' if 'match_id' in team_data.columns else ('matchId' if 'matchId' in team_data.columns else team_data.columns[0])

        bowler_stats = team_data.groupby('bowler').agg(
            wickets=('is_wicket', 'sum'),
            balls=('ball', 'count'),
            runs_conceded=('runs_off_bat', 'sum'),
            dot_balls=('runs_off_bat', lambda x: (x == 0).sum())
        ).reset_index()

        min_balls = 15 if phase else 30
        bowler_stats = bowler_stats[bowler_stats['balls'] >= min_balls]
        if len(bowler_stats) == 0:
            return pd.DataFrame()

        bowler_stats['economy'] = (bowler_stats['runs_conceded'] / bowler_stats['balls'] * 6).round(2)
        bowler_stats['average'] = (bowler_stats['runs_conceded'] / bowler_stats['wickets'].replace(0, 1)).round(1)
        bowler_stats['strike_rate'] = (bowler_stats['balls'] / bowler_stats['wickets'].replace(0, 1)).round(1)
        bowler_stats['dot_pct'] = (bowler_stats['dot_balls'] / bowler_stats['balls'] * 100).round(1)

        # Best figures per match
        match_bowling = team_data.groupby(['bowler', match_col]).agg(
            m_wkts=('is_wicket', 'sum'),
            m_runs=('runs_off_bat', 'sum')
        ).reset_index()
        match_bowling = match_bowling.sort_values(by=['m_wkts', 'm_runs'], ascending=[False, True])
        best_figs = match_bowling.groupby('bowler').first().reset_index()
        best_figs['best_figures'] = best_figs['m_wkts'].astype(str) + '/' + best_figs['m_runs'].astype(str)
        
        bowler_stats = bowler_stats.merge(best_figs[['bowler', 'best_figures']], on='bowler', how='left')

        # Bowling Impact Rating
        bowler_stats['impact_score'] = (
            (bowler_stats['wickets'] * 12) + 
            (bowler_stats['dot_pct'] * 0.6) - 
            (bowler_stats['economy'] * 4) + 20
        ).round(1)

        bowler_stats = bowler_stats.sort_values('wickets', ascending=False).head(10)
        return bowler_stats
    
    # -----------------------------------------------------------------------------
    # Altair Statistical Visualizations
    # -----------------------------------------------------------------------------
    
    def create_runs_distribution_chart(df, team, phase=None):
        """Create comprehensive runs distribution analysis from scratch using Plotly"""
        import plotly.graph_objects as go
        
        # Filter data for batting team
        team_data = df[df['batting_team'] == team]
        
        # Apply phase filter if specified
        if phase:
            team_data = team_data[team_data['phase'] == phase]
        
        # Check if we have data
        if len(team_data) == 0:
            return None
        
        # Calculate runs distribution statistics
        runs_counts = team_data['runs_off_bat'].value_counts().reset_index()
        runs_counts.columns = ['runs', 'count']
        runs_counts = runs_counts.sort_values('runs')
        
        # Calculate percentages
        total_balls = len(team_data)
        runs_counts['percentage'] = ((runs_counts['count'] / total_balls) * 100).round(1)
        
        # Add cumulative percentage
        runs_counts['cumulative_pct'] = runs_counts['percentage'].cumsum().round(1)
        
        team_color = IPL_TEAM_COLORS.get(team, '#3b82f6')
        hex_c = team_color.lstrip('#')
        if len(hex_c) == 6:
            r, g, b = tuple(int(hex_c[i:i+2], 16) for i in (0, 2, 4))
        else:
            r, g, b = 59, 130, 246
            
        color_map = {
            0: f"rgba({r},{g},{b},0.15)",  # dots
            1: f"rgba({r},{g},{b},0.35)",  # singles
            2: f"rgba({r},{g},{b},0.55)",  # twos
            3: f"rgba({r},{g},{b},0.70)",  # threes
            4: f"rgba({r},{g},{b},0.85)",  # fours
            6: f"rgba({r},{g},{b},1.0)",   # sixes
        }
        
        label_map = {
            0: 'Dot Balls', 1: 'Singles', 2: 'Twos', 
            3: 'Threes', 4: 'Fours', 6: 'Sixes'
        }
        
        runs_counts['color'] = runs_counts['runs'].map(lambda x: color_map.get(x, '#fbbf24'))
        runs_counts['label'] = runs_counts['runs'].map(lambda x: label_map.get(x, f'{int(x)} Runs'))
        
        # Calculate summary statistics
        total_runs = int(team_data['runs_off_bat'].sum())
        avg_runs_per_ball = round(total_runs / total_balls, 2) if total_balls > 0 else 0
        dots = int(len(team_data[team_data['runs_off_bat'] == 0]))
        boundaries = int(len(team_data[(team_data['runs_off_bat'] == 4) | (team_data['runs_off_bat'] == 6)]))
        dot_pct = round((dots / total_balls) * 100, 1) if total_balls > 0 else 0
        boundary_pct = round((boundaries / total_balls) * 100, 1) if total_balls > 0 else 0
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=runs_counts['label'],
            y=runs_counts['count'],
            text=[f"<b>{count}</b><br><span style='font-size:11px;color:#cbd5e1'>{pct}%</span>" for count, pct in zip(runs_counts['count'], runs_counts['percentage'])],
            textposition='auto',
            marker=dict(
                color=runs_counts['color'],
                line=dict(color='rgba(255,255,255,0.3)', width=1.5),
            ),
            hovertemplate="<b>%{x}</b><br>Count: %{y}<br>Percentage: %{customdata}%<extra></extra>",
            customdata=runs_counts['percentage']
        ))
        
        fig.update_layout(
            title=dict(
                text=f"<b>{team}</b><br><span style='font-size:13px;color:#94a3b8'>Total Runs: {total_runs} | Total Balls: {total_balls} | Avg: {avg_runs_per_ball}</span><br><span style='font-size:13px;color:#94a3b8'>Dots: {dot_pct}% | Boundaries: {boundary_pct}%</span>",
                font=dict(size=18, color='#f8fafc'),
                x=0.5,
                xanchor='center'
            ),
            paper_bgcolor='rgba(15, 23, 42, 0)',
            plot_bgcolor='rgba(15, 23, 42, 0)',
            font=dict(color='#e2e8f0', family='Segoe UI'),
            xaxis=dict(
                showgrid=False,
                title="",
                tickfont=dict(size=12, color='#e2e8f0')
            ),
            yaxis=dict(
                showgrid=True,
                gridcolor='rgba(255,255,255,0.1)',
                title="Number of Balls",
                tickfont=dict(size=11, color='#94a3b8')
            ),
            margin=dict(t=90, b=40, l=50, r=20),
            showlegend=False,
            height=400,
            hoverlabel=dict(
                bgcolor="rgba(15, 23, 42, 0.9)",
                font_size=13,
                font_family="Segoe UI"
            )
        )
        
        chart = fig
        
        return chart
    
    def create_strike_rate_comparison(df, phase=None):
        """Create strike rate comparison chart for top batters across teams using Plotly"""
        import plotly.graph_objects as go
        if phase:
            data = df[df['phase'] == phase]
        else:
            data = df
        
        batter_stats = data.groupby(['batter', 'batting_team']).agg({
            'runs_off_bat': 'sum',
            'ball': 'count'
        }).reset_index()
        
        batter_stats = batter_stats[batter_stats['ball'] >= 50]
        batter_stats['strike_rate'] = (batter_stats['runs_off_bat'] / batter_stats['ball'] * 100).round(2)
        batter_stats = batter_stats.sort_values('strike_rate', ascending=True).tail(15) # Ascending for horizontal bar
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=batter_stats['strike_rate'],
            y=batter_stats['batter'],
            orientation='h',
            text=[f"<b>{sr}</b>" for sr in batter_stats['strike_rate']],
            textposition='auto',
            marker=dict(
                color=[IPL_TEAM_COLORS.get(t, '#3b82f6') for t in batter_stats['batting_team']],
                line=dict(color='rgba(255,255,255,0.2)', width=1)
            ),
            hovertemplate="<b>%{y}</b><br>Team: %{customdata[0]}<br>Strike Rate: %{x}<br>Runs: %{customdata[1]}<br>Balls: %{customdata[2]}<extra></extra>",
            customdata=batter_stats[['batting_team', 'runs_off_bat', 'ball']]
        ))
        
        fig.update_layout(
            title=dict(
                text="<b>Top 15 Batters by Strike Rate (min 50 balls)</b>",
                font=dict(size=18, color='#f8fafc'),
                x=0.5,
                xanchor='center'
            ),
            paper_bgcolor='rgba(15, 23, 42, 0)',
            plot_bgcolor='rgba(15, 23, 42, 0)',
            font=dict(color='#e2e8f0', family='Segoe UI'),
            xaxis=dict(
                title="Strike Rate",
                showgrid=True,
                gridcolor='rgba(255,255,255,0.05)',
                tickfont=dict(size=11, color='#94a3b8')
            ),
            yaxis=dict(
                title="",
                showgrid=False,
                tickfont=dict(size=12, color='#e2e8f0')
            ),
            margin=dict(t=70, b=40, l=120, r=40),
            showlegend=False,
            height=500,
            hoverlabel=dict(bgcolor="rgba(15, 23, 42, 0.9)", font_size=13)
        )
        return fig

    def create_advanced_player_matchup_all_types_chart(df, team, phase=None, top_n=6):
        """Create advanced static visualization for Player Matchups vs All Bowler Types using Plotly"""
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots
        import pandas as pd

        # Filter team data
        team_data = df[df['batting_team'] == team]
        if phase:
            team_data = team_data[team_data['phase'] == phase]

        if len(team_data) == 0:
            return None

        # Get top batters
        batter_totals = team_data.groupby('batter').agg({
            'runs_off_bat': 'sum',
            'ball': 'count'
        }).reset_index()
        batter_totals = batter_totals[batter_totals['ball'] >= 30].sort_values('runs_off_bat', ascending=False).head(top_n)
        top_batters = batter_totals['batter'].tolist()

        if not top_batters:
            return None

        # Define distinct bowler types
        bowler_types = [
            'Right-Arm Pace',
            'Left-Arm Pace',
            'Right-Arm Leg Spin',
            'Right-Arm Off Spin',
            'Left-Arm Orthodox',
            'Left-Arm Wrist Spin'
        ]

        # Calculate metrics matrix
        sr_matrix = []
        text_matrix = []
        hover_matrix = []
        bar_data = []

        for batter in top_batters:
            sr_row = []
            text_row = []
            hover_row = []
            for bt in bowler_types:
                stats = calculate_player_matchup(team_data, batter, bt, team=team)
                if stats and stats['balls_faced'] > 0:
                    sr = round(stats['strike_rate'], 1)
                    runs = stats['runs_scored']
                    balls = stats['balls_faced']
                    outs = stats['dismissals']
                    avg = round(stats['average'], 1)
                    
                    sr_row.append(sr)
                    text_row.append(f"<b>{sr}</b><br><span style='font-size:10px;color:#cbd5e1'>{runs}r/{balls}b</span>")
                    hover_row.append(f"<b>{batter} vs {bt}</b><br>Runs: {runs}<br>Balls: {balls}<br>Outs: {outs}<br>SR: {sr}<br>Avg: {avg}")
                    
                    bar_data.append({
                        'batter': batter,
                        'bowler_type': bt,
                        'strike_rate': sr,
                        'average': avg,
                        'balls': balls,
                        'runs': runs,
                        'outs': outs
                    })
                else:
                    sr_row.append(0.0)
                    text_row.append("<span style='font-size:10px;color:#64748b'>N/A</span>")
                    hover_row.append(f"<b>{batter} vs {bt}</b><br>No deliveries faced")

            sr_matrix.append(sr_row)
            text_matrix.append(text_row)
            hover_matrix.append(hover_row)

        # Create 2 subplots: Top = Heatmap, Bottom = Grouped Bar Chart
        fig = make_subplots(
            rows=2, cols=1,
            row_heights=[0.55, 0.45],
            vertical_spacing=0.15,
            subplot_titles=(
                f"<b>🎯 Strike Rate Heatmap Matrix — {team} Batters vs All Bowler Types</b>",
                f"<b>⚡ Strike Rate Comparison across Bowler Types</b>"
            )
        )

        # Add Heatmap Trace
        fig.add_trace(
            go.Heatmap(
                z=sr_matrix,
                x=bowler_types,
                y=top_batters,
                text=text_matrix,
                texttemplate="%{text}",
                textfont=dict(size=12, color='#f8fafc', family='Segoe UI'),
                hoverinfo="text",
                hovertext=hover_matrix,
                colorscale=[
                    [0.0, "rgba(30, 41, 59, 0.8)"],
                    [0.3, "rgba(59, 130, 246, 0.7)"],
                    [0.6, "rgba(168, 85, 247, 0.85)"],
                    [0.85, "rgba(236, 72, 153, 0.9)"],
                    [1.0, "rgba(244, 63, 94, 1.0)"]
                ],
                colorbar=dict(
                    title=dict(text="Strike Rate", side="top", font=dict(color='#94a3b8')),
                    len=0.45,
                    y=0.78,
                    tickfont=dict(color='#94a3b8')
                ),
                showscale=True
            ),
            row=1, col=1
        )

        # Add Grouped Bar traces for each bowler type
        bar_df = pd.DataFrame(bar_data)
        bt_colors = {
            'Right-Arm Pace': '#3b82f6',
            'Left-Arm Pace': '#06b6d4',
            'Right-Arm Leg Spin': '#a855f7',
            'Right-Arm Off Spin': '#ec4899',
            'Left-Arm Orthodox': '#10b981',
            'Left-Arm Wrist Spin': '#f59e0b'
        }

        if not bar_df.empty:
            for bt in bowler_types:
                sub_df = bar_df[bar_df['bowler_type'] == bt]
                if not sub_df.empty:
                    fig.add_trace(
                        go.Bar(
                            name=bt,
                            x=sub_df['batter'],
                            y=sub_df['strike_rate'],
                            marker_color=bt_colors.get(bt, '#64748b'),
                            text=[f"{sr:.0f}" for sr in sub_df['strike_rate']],
                            textposition='auto',
                            hovertemplate="<b>%{x} vs " + bt + "</b><br>Strike Rate: %{y}<extra></extra>"
                        ),
                        row=2, col=1
                    )

        fig.update_layout(
            paper_bgcolor='rgba(15, 23, 42, 0)',
            plot_bgcolor='rgba(15, 23, 42, 0)',
            font=dict(color='#e2e8f0', family='Segoe UI'),
            height=750,
            margin=dict(t=80, b=40, l=120, r=40),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.12,
                xanchor="center",
                x=0.5,
                bgcolor='rgba(15, 23, 42, 0.6)',
                font=dict(size=11, color='#e2e8f0')
            ),
            barmode='group'
        )

        fig.update_xaxes(showgrid=False, tickfont=dict(size=11, color='#cbd5e1'), row=1, col=1)
        fig.update_yaxes(showgrid=False, tickfont=dict(size=12, color='#f8fafc'), row=1, col=1)

        fig.update_xaxes(showgrid=False, tickfont=dict(size=12, color='#f8fafc'), row=2, col=1)
        fig.update_yaxes(title_text="Strike Rate", showgrid=True, gridcolor='rgba(255,255,255,0.05)', tickfont=dict(size=11, color='#94a3b8'), row=2, col=1)

        # Update subplot titles style
        for i in fig['layout']['annotations']:
            i['font'] = dict(size=15, color='#f8fafc')

        return fig

    def create_phase_efficiency_matrix_chart(df, team1, team2):
        """Create 4-panel efficiency matrix chart (Run Rate, Dot %, Boundary %, Wickets) comparing both teams across phases"""
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots

        t1_stats = calculate_comprehensive_phase_stats(df, team1)
        t2_stats = calculate_comprehensive_phase_stats(df, team2)

        phases = ['Powerplay (1-6)', 'Middle (7-15)', 'Death (16-20)']
        t1_color = IPL_TEAM_COLORS.get(team1, '#3b82f6')
        t2_color = IPL_TEAM_COLORS.get(team2, '#ef4444')

        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=(
                "<b>🏃 Run Rate (Runs per Over)</b>",
                "<b>⚫ Dot Ball Percentage (Lower = Better)</b>",
                "<b>💥 Boundary Percentage (4s + 6s)</b>",
                "<b>🎯 Total Wickets Lost</b>"
            ),
            horizontal_spacing=0.12,
            vertical_spacing=0.18
        )

        metrics = [
            ('run_rate', 1, 1, '{:.2f} RR', 'Run Rate'),
            ('dot_pct', 1, 2, '{:.1f}%', 'Dot %'),
            ('boundary_pct', 2, 1, '{:.1f}%', 'Boundary %'),
            ('wickets', 2, 2, '{} Wkts', 'Wickets Lost')
        ]

        for col_name, r, c, fmt, label in metrics:
            t1_vals = t1_stats[col_name].tolist() if not t1_stats.empty else [0]*3
            t2_vals = t2_stats[col_name].tolist() if not t2_stats.empty else [0]*3

            fig.add_trace(
                go.Bar(
                    x=phases, y=t1_vals, name=team1, marker_color=t1_color,
                    text=[fmt.format(v) for v in t1_vals], textposition='auto',
                    hovertemplate=f"<b>{team1} - %{{x}}</b><br>{label}: %{{y}}<extra></extra>",
                    showlegend=(r == 1 and c == 1)
                ),
                row=r, col=c
            )
            fig.add_trace(
                go.Bar(
                    x=phases, y=t2_vals, name=team2, marker_color=t2_color,
                    text=[fmt.format(v) for v in t2_vals], textposition='auto',
                    hovertemplate=f"<b>{team2} - %{{x}}</b><br>{label}: %{{y}}<extra></extra>",
                    showlegend=(r == 1 and c == 1)
                ),
                row=r, col=c
            )

        fig.update_layout(
            barmode='group',
            paper_bgcolor='rgba(15, 23, 42, 0)',
            plot_bgcolor='rgba(15, 23, 42, 0)',
            font=dict(color='#e2e8f0', family='Segoe UI'),
            height=650,
            margin=dict(t=60, b=40, l=40, r=20),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5, bgcolor='rgba(0,0,0,0)', font=dict(size=12))
        )

        for anno in fig['layout']['annotations']:
            anno['font'] = dict(size=14, color='#f8fafc')

        fig.update_xaxes(showgrid=False, tickfont=dict(size=11, color='#cbd5e1'))
        fig.update_yaxes(showgrid=True, gridcolor='rgba(255,255,255,0.05)', tickfont=dict(size=10, color='#94a3b8'))

        return fig

    def create_phase_innings_split_chart(df, team1, team2):
        """Create 1st Innings vs 2nd Innings phase run rate comparison using Plotly"""
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots

        phases = ['Powerplay (1-6)', 'Middle (7-15)', 'Death (16-20)']
        t1_color = IPL_TEAM_COLORS.get(team1, '#3b82f6')
        t2_color = IPL_TEAM_COLORS.get(team2, '#ef4444')

        fig = make_subplots(
            rows=1, cols=2,
            subplot_titles=(
                f"<b>🏏 {team1} — 1st Innings vs 2nd Innings</b>",
                f"<b>🏏 {team2} — 1st Innings vs 2nd Innings</b>"
            )
        )

        for idx, (tm, col_num, clr) in enumerate([(team1, 1, t1_color), (team2, 2, t2_color)]):
            tm_df = df[df['batting_team'] == tm]
            inn1_df = tm_df[tm_df['innings'] == 1] if 'innings' in tm_df.columns else tm_df
            inn2_df = tm_df[tm_df['innings'] == 2] if 'innings' in tm_df.columns else tm_df

            rr_inn1 = []
            rr_inn2 = []
            for p in phases:
                p1 = inn1_df[inn1_df['phase'] == p]
                p2 = inn2_df[inn2_df['phase'] == p]
                r1 = round((p1['total_runs'].sum() / len(p1)) * 6, 2) if len(p1) > 0 else 0.0
                r2 = round((p2['total_runs'].sum() / len(p2)) * 6, 2) if len(p2) > 0 else 0.0
                rr_inn1.append(r1)
                rr_inn2.append(r2)

            fig.add_trace(
                go.Bar(
                    x=phases, y=rr_inn1, name="1st Innings (Setting Target)",
                    marker_color=clr, opacity=0.9,
                    text=[f"{r:.2f}" for r in rr_inn1], textposition='auto',
                    hovertemplate=f"<b>1st Innings - %{{x}}</b><br>Run Rate: %{{y:.2f}}<extra></extra>",
                    showlegend=(col_num == 1)
                ),
                row=1, col=col_num
            )
            fig.add_trace(
                go.Bar(
                    x=phases, y=rr_inn2, name="2nd Innings (Chasing)",
                    marker_color='#f59e0b', opacity=0.9,
                    text=[f"{r:.2f}" for r in rr_inn2], textposition='auto',
                    hovertemplate=f"<b>2nd Innings - %{{x}}</b><br>Run Rate: %{{y:.2f}}<extra></extra>",
                    showlegend=(col_num == 1)
                ),
                row=1, col=col_num
            )

        fig.update_layout(
            barmode='group',
            paper_bgcolor='rgba(15, 23, 42, 0)',
            plot_bgcolor='rgba(15, 23, 42, 0)',
            font=dict(color='#e2e8f0', family='Segoe UI'),
            height=420,
            margin=dict(t=60, b=40, l=40, r=20),
            legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="center", x=0.5, bgcolor='rgba(0,0,0,0)', font=dict(size=12))
        )
        for anno in fig['layout']['annotations']:
            anno['font'] = dict(size=14, color='#f8fafc')

        fig.update_xaxes(showgrid=False, tickfont=dict(size=11, color='#cbd5e1'))
        fig.update_yaxes(title_text="Run Rate", showgrid=True, gridcolor='rgba(255,255,255,0.05)', tickfont=dict(size=11, color='#94a3b8'))

        return fig

    def create_phase_pace_vs_spin_chart(df, team1, team2):
        """Create Pace vs Spin comparison by phase using Plotly"""
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots

        phases = ['Powerplay (1-6)', 'Middle (7-15)', 'Death (16-20)']
        t1_color = IPL_TEAM_COLORS.get(team1, '#3b82f6')
        t2_color = IPL_TEAM_COLORS.get(team2, '#ef4444')

        pace_types = ['Right-Arm Pace', 'Left-Arm Pace', 'Right-Arm Fast', 'Right-Arm Medium', 'Left-Arm Fast', 'Left-Arm Medium']

        fig = make_subplots(
            rows=1, cols=2,
            subplot_titles=(
                f"<b>🏏 {team1} — Pace vs Spin by Phase</b>",
                f"<b>🏏 {team2} — Pace vs Spin by Phase</b>"
            )
        )

        for tm, col_num, clr in [(team1, 1, t1_color), (team2, 2, t2_color)]:
            tm_df = df[df['batting_team'] == tm]
            sr_pace = []
            sr_spin = []

            for p in phases:
                p_df = tm_df[tm_df['phase'] == p]
                p_pace = p_df[p_df['bowler_type'].isin(pace_types)]
                p_spin = p_df[~p_df['bowler_type'].isin(pace_types)]

                sr_p = round((p_pace['runs_off_bat'].sum() / len(p_pace)) * 100, 1) if len(p_pace) > 0 else 0.0
                sr_s = round((p_spin['runs_off_bat'].sum() / len(p_spin)) * 100, 1) if len(p_spin) > 0 else 0.0

                sr_pace.append(sr_p)
                sr_spin.append(sr_s)

            fig.add_trace(
                go.Bar(
                    x=phases, y=sr_pace, name="vs Pace",
                    marker_color='#38bdf8',
                    text=[f"{sr:.1f}" for sr in sr_pace], textposition='auto',
                    hovertemplate=f"<b>vs Pace - %{{x}}</b><br>Strike Rate: %{{y:.1f}}<extra></extra>",
                    showlegend=(col_num == 1)
                ),
                row=1, col=col_num
            )
            fig.add_trace(
                go.Bar(
                    x=phases, y=sr_spin, name="vs Spin",
                    marker_color='#a855f7',
                    text=[f"{sr:.1f}" for sr in sr_spin], textposition='auto',
                    hovertemplate=f"<b>vs Spin - %{{x}}</b><br>Strike Rate: %{{y:.1f}}<extra></extra>",
                    showlegend=(col_num == 1)
                ),
                row=1, col=col_num
            )

        fig.update_layout(
            barmode='group',
            paper_bgcolor='rgba(15, 23, 42, 0)',
            plot_bgcolor='rgba(15, 23, 42, 0)',
            font=dict(color='#e2e8f0', family='Segoe UI'),
            height=420,
            margin=dict(t=60, b=40, l=40, r=20),
            legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="center", x=0.5, bgcolor='rgba(0,0,0,0)', font=dict(size=12))
        )
        for anno in fig['layout']['annotations']:
            anno['font'] = dict(size=14, color='#f8fafc')

        fig.update_xaxes(showgrid=False, tickfont=dict(size=11, color='#cbd5e1'))
        fig.update_yaxes(title_text="Strike Rate", showgrid=True, gridcolor='rgba(255,255,255,0.05)', tickfont=dict(size=11, color='#94a3b8'))

        return fig

    def create_phase_overlay_worm_chart(df, team1, team2):
        """Create Over-by-Over Phase Overlay Curve (Overs 1-20) with shaded background regions"""
        import plotly.graph_objects as go

        fig = go.Figure()

        t1_color = IPL_TEAM_COLORS.get(team1, '#3b82f6')
        t2_color = IPL_TEAM_COLORS.get(team2, '#ef4444')

        for tm, clr in [(team1, t1_color), (team2, t2_color)]:
            tm_df = df[df['batting_team'] == tm]
            if tm_df.empty: continue
            
            over_stats = tm_df.groupby('over').agg({'total_runs': 'sum', 'ball': 'count', 'is_wicket': 'sum'}).reset_index()
            over_stats = over_stats[(over_stats['over'] >= 1) & (over_stats['over'] <= 20)].sort_values('over')
            over_stats['run_rate'] = (over_stats['total_runs'] / over_stats['ball'] * 6).round(2)

            fig.add_trace(go.Scatter(
                x=over_stats['over'],
                y=over_stats['run_rate'],
                name=tm,
                mode='lines+markers',
                line=dict(color=clr, width=3.5),
                marker=dict(size=8, color=clr, line=dict(color='white', width=1)),
                hovertemplate=f"<b>{tm} - Over %{{x}}</b><br>Run Rate: %{{y:.2f}}<br>Runs: %{{customdata[0]}}<br>Wickets: %{{customdata[1]}}<extra></extra>",
                customdata=over_stats[['total_runs', 'is_wicket']]
            ))

        # Add Shaded Background Bands for Phases
        fig.add_vrect(x0=0.5, x1=6.5, fillcolor="rgba(34, 197, 94, 0.12)", layer="below", line_width=0,
                      annotation_text="<b>POWERPLAY (1-6)</b>", annotation_position="top left",
                      annotation_font=dict(size=12, color="#4ade80"))

        fig.add_vrect(x0=6.5, x1=15.5, fillcolor="rgba(59, 130, 246, 0.10)", layer="below", line_width=0,
                      annotation_text="<b>MIDDLE OVERS (7-15)</b>", annotation_position="top left",
                      annotation_font=dict(size=12, color="#60a5fa"))

        fig.add_vrect(x0=15.5, x1=20.5, fillcolor="rgba(239, 68, 68, 0.12)", layer="below", line_width=0,
                      annotation_text="<b>DEATH OVERS (16-20)</b>", annotation_position="top left",
                      annotation_font=dict(size=12, color="#f87171"))

        fig.update_layout(
            title=dict(
                text="<b>Over-by-Over Run Rate Progression Curve across Match Phases</b>",
                font=dict(size=16, color='#f8fafc'),
                x=0.5, xanchor='center'
            ),
            paper_bgcolor='rgba(15, 23, 42, 0)',
            plot_bgcolor='rgba(15, 23, 42, 0)',
            font=dict(color='#e2e8f0', family='Segoe UI'),
            xaxis=dict(
                title="Over Number",
                tickmode='linear', tick0=1, dtick=1,
                range=[0.5, 20.5],
                showgrid=False,
                tickfont=dict(size=11, color='#cbd5e1')
            ),
            yaxis=dict(
                title="Run Rate (Runs / Over)",
                showgrid=True,
                gridcolor='rgba(255,255,255,0.05)',
                tickfont=dict(size=11, color='#94a3b8')
            ),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5, bgcolor='rgba(0,0,0,0)', font=dict(size=13)),
            height=460,
            margin=dict(t=70, b=40, l=50, r=20),
            hovermode="x unified"
        )

        return fig

    def create_boundary_percentage_chart(df, teams, phase=None):
        """Create comprehensive boundary and dot ball analysis using Plotly"""
        import plotly.graph_objects as go
        import pandas as pd
        results = []
        
        for team in teams:
            team_data = df[df['batting_team'] == team]
            if phase:
                team_data = team_data[team_data['phase'] == phase]
            
            total_balls = len(team_data)
            if total_balls == 0:
                continue
            
            fours = len(team_data[team_data['runs_off_bat'] == 4])
            sixes = len(team_data[team_data['runs_off_bat'] == 6])
            dots = len(team_data[team_data['runs_off_bat'] == 0])
            singles = len(team_data[team_data['runs_off_bat'] == 1])
            twos = len(team_data[team_data['runs_off_bat'] == 2])
            
            results.append({'team': team, 'category': 'Fours (4s)', 'percentage': round((fours/total_balls)*100, 1)})
            results.append({'team': team, 'category': 'Sixes (6s)', 'percentage': round((sixes/total_balls)*100, 1)})
            results.append({'team': team, 'category': 'Dot Balls', 'percentage': round((dots/total_balls)*100, 1)})
            results.append({'team': team, 'category': 'Singles (1s)', 'percentage': round((singles/total_balls)*100, 1)})
            results.append({'team': team, 'category': 'Twos (2s)', 'percentage': round((twos/total_balls)*100, 1)})
        
        if len(results) == 0:
            return None
            
        chart_df = pd.DataFrame(results)
        fig = go.Figure()
        
        categories = ['Dot Balls', 'Singles (1s)', 'Twos (2s)', 'Fours (4s)', 'Sixes (6s)']
        colors = [IPL_TEAM_COLORS.get(teams[0], '#3b82f6'), IPL_TEAM_COLORS.get(teams[1], '#f43f5e')] if len(teams) > 1 else ['#3b82f6', '#f43f5e']
        
        for idx, team in enumerate(teams):
            team_df = chart_df[chart_df['team'] == team]
            if len(team_df) == 0: continue
            
            team_df = team_df.set_index('category').reindex(categories).reset_index()
            
            fig.add_trace(go.Bar(
                name=team,
                x=team_df['category'],
                y=team_df['percentage'],
                text=[f"<b>{pct}%</b>" for pct in team_df['percentage']],
                textposition='auto',
                marker=dict(
                    color=colors[idx % len(colors)],
                    line=dict(color='rgba(255,255,255,0.2)', width=1)
                ),
                hovertemplate="<b>%{x}</b><br>Team: " + team + "<br>Percentage: %{y}%<extra></extra>"
            ))
            
        fig.update_layout(
            barmode='group',
            title=dict(
                text="<b>Boundary & Dot Ball Analysis - Team Comparison</b>",
                font=dict(size=18, color='#f8fafc'),
                x=0.5,
                xanchor='center'
            ),
            paper_bgcolor='rgba(15, 23, 42, 0)',
            plot_bgcolor='rgba(15, 23, 42, 0)',
            font=dict(color='#e2e8f0', family='Segoe UI'),
            xaxis=dict(
                title="",
                showgrid=False,
                tickfont=dict(size=12, color='#e2e8f0')
            ),
            yaxis=dict(
                title="Percentage of Balls (%)",
                showgrid=True,
                gridcolor='rgba(255,255,255,0.05)',
                tickfont=dict(size=11, color='#94a3b8')
            ),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="center",
                x=0.5,
                bgcolor='rgba(0,0,0,0)'
            ),
            margin=dict(t=100, b=40, l=50, r=20),
            height=400,
            hoverlabel=dict(bgcolor="rgba(15, 23, 42, 0.9)", font_size=13)
        )
        return fig
    
    def create_runs_over_progression(df, team, phase=None):
        """Create runs progression over overs using Plotly"""
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots
        
        team_data = df[df['batting_team'] == team]
        if phase:
            team_data = team_data[team_data['phase'] == phase]
        
        over_runs = team_data.groupby('over')['runs_off_bat'].sum().reset_index()
        over_runs['cumulative_runs'] = over_runs['runs_off_bat'].cumsum()
        
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        
        team_color = IPL_TEAM_COLORS.get(team, '#60a5fa')
        
        # Convert hex to rgba for transparent fill
        if team_color.startswith('#'):
            r, g, b = int(team_color[1:3], 16), int(team_color[3:5], 16), int(team_color[5:7], 16)
            team_color_rgba = f"rgba({r}, {g}, {b}, 0.5)"
        else:
            team_color_rgba = 'rgba(96, 165, 250, 0.5)'
            
        fig.add_trace(
            go.Bar(
                x=over_runs['over'],
                y=over_runs['runs_off_bat'],
                name="Runs per Over",
                marker_color=team_color_rgba,
                marker_line_color=team_color,
                marker_line_width=1.5,
                opacity=0.8
            ),
            secondary_y=False,
        )
        
        fig.add_trace(
            go.Scatter(
                x=over_runs['over'],
                y=over_runs['cumulative_runs'],
                name="Cumulative Runs",
                mode='lines+markers',
                line=dict(color=team_color, width=3),
                marker=dict(size=8, color=team_color, line=dict(color='white', width=1)),
            ),
            secondary_y=True,
        )
        
        fig.update_layout(
            title=dict(
                text=f"<b>{team} - Runs Progression Over Overs</b>",
                font=dict(size=16, color='#f8fafc'),
                x=0.5,
                xanchor='center'
            ),
            paper_bgcolor='rgba(15, 23, 42, 0)',
            plot_bgcolor='rgba(15, 23, 42, 0)',
            font=dict(color='#e2e8f0', family='Segoe UI'),
            xaxis=dict(
                title="Over",
                showgrid=False,
                tickmode='linear',
                tick0=0, dtick=1,
                tickfont=dict(size=11, color='#94a3b8')
            ),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="center",
                x=0.5,
                bgcolor='rgba(0,0,0,0)'
            ),
            margin=dict(t=80, b=40, l=40, r=40),
            height=400,
            hovermode="x unified",
            hoverlabel=dict(bgcolor="rgba(15, 23, 42, 0.9)", font_size=13)
        )
        
        fig.update_yaxes(title_text="Runs per Over", showgrid=False, secondary_y=False, tickfont=dict(color='#94a3b8'))
        fig.update_yaxes(title_text="Cumulative Runs", showgrid=True, gridcolor='rgba(255,255,255,0.05)', secondary_y=True, tickfont=dict(color='#60a5fa'))
        
        return fig
    
    def create_wicket_timeline(df, bowling_team, phase=None):
        """Create wicket fall timeline/distribution using Plotly"""
        import plotly.graph_objects as go
        
        team_data = df[df['bowling_team'] == bowling_team]
        if phase:
            team_data = team_data[team_data['phase'] == phase]
        
        wickets = team_data[team_data['is_wicket'] == 1]
        if wickets.empty:
            return None
            
        # Group by over and wicket type
        wicket_counts = wickets.groupby(['over', 'wicket_type']).size().reset_index(name='count')
        
        fig = go.Figure()
        
        # Define a consistent color palette for wicket types
        colors = {
            'caught': '#3b82f6',
            'bowled': '#ef4444',
            'lbw': '#eab308',
            'run out': '#f97316',
            'stumped': '#8b5cf6',
            'caught and bowled': '#10b981',
            'hit wicket': '#ec4899',
            'retired hurt': '#64748b'
        }
        
        for w_type in wicket_counts['wicket_type'].unique():
            w_data = wicket_counts[wicket_counts['wicket_type'] == w_type]
            fig.add_trace(go.Bar(
                x=w_data['over'],
                y=w_data['count'],
                name=w_type,
                marker_color=colors.get(w_type, '#94a3b8'),
                hovertemplate="Over: %{x}<br>Type: " + str(w_type) + "<br>Wickets: %{y}<extra></extra>"
            ))
            
        fig.update_layout(
            barmode='stack',
            title=dict(
                text=f"<b>{bowling_team} - Fall of Wickets Distribution</b>",
                font=dict(size=16, color='#f8fafc'),
                x=0.5,
                xanchor='center'
            ),
            paper_bgcolor='rgba(15, 23, 42, 0)',
            plot_bgcolor='rgba(15, 23, 42, 0)',
            font=dict(color='#e2e8f0', family='Segoe UI'),
            xaxis=dict(
                title="Over",
                showgrid=False,
                tickmode='linear',
                tick0=0, dtick=1,
                tickfont=dict(size=11, color='#94a3b8')
            ),
            yaxis=dict(
                title="Number of Wickets",
                showgrid=True,
                gridcolor='rgba(255,255,255,0.05)',
                tickfont=dict(size=11, color='#94a3b8'),
            ),
            legend=dict(
                orientation="h",
                yanchor="top",
                y=-0.2,
                xanchor="center",
                x=0.5,
                bgcolor='rgba(0,0,0,0)'
            ),
            margin=dict(t=60, b=80, l=40, r=20),
            height=430,
            hovermode="x unified"
        )
        return fig

    def create_bowler_economy_chart(df, team, phase=None, bowler_type=None):
        """Create comprehensive bowler economy rate analysis from scratch"""
        # Filter data for bowling team
        team_data = df[df['bowling_team'] == team]
        
        # Apply phase filter if specified
        if phase:
            team_data = team_data[team_data['phase'] == phase]
        team_data = _filter_by_bowler_type(team_data, bowler_type)
        
        # Check if we have data
        if len(team_data) == 0:
            return None
        
        # Calculate comprehensive bowling statistics per bowler
        bowler_stats = team_data.groupby('bowler').agg({
            'runs_off_bat': 'sum',
            'extras': 'sum',
            'ball': 'count',
            'is_wicket': 'sum'
        }).reset_index()
        
        # Calculate additional metrics using direct filtering
        bowler_list = []
        for bowler in bowler_stats['bowler'].unique():
            bowler_balls = team_data[team_data['bowler'] == bowler]
            
            # Count dots (no runs and no extras)
            dots = len(bowler_balls[(bowler_balls['runs_off_bat'] == 0) & (bowler_balls['extras'] == 0)])
            
            # Count boundaries (4s and 6s)
            boundaries = len(bowler_balls[(bowler_balls['runs_off_bat'] == 4) | (bowler_balls['runs_off_bat'] == 6)])
            
            # Count sixes specifically
            sixes = len(bowler_balls[bowler_balls['runs_off_bat'] == 6])
            
            # Count fours specifically
            fours = len(bowler_balls[bowler_balls['runs_off_bat'] == 4])
            
            bowler_list.append({
                'bowler': bowler,
                'dots': dots,
                'boundaries': boundaries,
                'sixes': sixes,
                'fours': fours
            })
        
        # Merge additional statistics
        additional_stats = pd.DataFrame(bowler_list)
        bowler_stats = bowler_stats.merge(additional_stats, on='bowler', how='left')
        
        # Filter bowlers with minimum 24 balls (4 overs)
        bowler_stats = bowler_stats[bowler_stats['ball'] >= 24]
        
        if len(bowler_stats) == 0:
            return None
        
        # Calculate derived metrics
        bowler_stats['overs'] = (bowler_stats['ball'] / 6).round(1)
        bowler_stats['total_runs'] = bowler_stats['runs_off_bat'] + bowler_stats['extras']
        bowler_stats['economy'] = (bowler_stats['total_runs'] / bowler_stats['overs']).round(2)
        
        # Calculate strike rate (balls per wicket)
        bowler_stats['strike_rate'] = bowler_stats.apply(
            lambda x: round(x['ball'] / x['is_wicket'], 1) if x['is_wicket'] > 0 else 999.0, axis=1
        )
        
        # Calculate bowling average (runs per wicket)
        bowler_stats['average'] = bowler_stats.apply(
            lambda x: round(x['total_runs'] / x['is_wicket'], 2) if x['is_wicket'] > 0 else 999.0, axis=1
        )
        
        # Calculate percentages
        bowler_stats['dot_percentage'] = ((bowler_stats['dots'] / bowler_stats['ball']) * 100).round(1)
        bowler_stats['boundary_percentage'] = ((bowler_stats['boundaries'] / bowler_stats['ball']) * 100).round(1)
        
        # Sort by economy rate and select top 12 bowlers
        bowler_stats = bowler_stats.sort_values('economy').head(12)
        
        # Prepare custom label for wickets
        bowler_stats['wicket_text'] = bowler_stats.apply(lambda x: f"🎯 {int(x['is_wicket'])} W | {int(x['dots'])} Dots", axis=1)

        # Create the base chart
        base = alt.Chart(bowler_stats).encode(
            y=alt.Y('bowler:N', 
                    sort=alt.EncodingSortField(field='economy', order='ascending'),
                    title='Bowler',
                    axis=alt.Axis(labelLimit=200, labelFontSize=12, labelColor='#e2e8f0', titleColor='#e2e8f0', grid=False, domainColor='rgba(255,255,255,0.1)'))
        )
        
        # Create horizontal bars with team color
        team_color = IPL_TEAM_COLORS.get(team, '#3b82f6')
        
        bars = base.mark_bar(
            cornerRadiusBottomRight=8,
            cornerRadiusTopRight=8,
            size=28,
            opacity=0.9,
            color=team_color
        ).encode(
            x=alt.X('economy:Q', 
                    title='Economy Rate (Runs per Over)', 
                    axis=alt.Axis(labelColor='#94a3b8', titleColor='#e2e8f0', gridColor='rgba(255,255,255,0.05)', domainColor='rgba(255,255,255,0.1)'),
                    scale=alt.Scale(domain=[0, max(15, bowler_stats['economy'].max() + 1)])),
            tooltip=[
                alt.Tooltip('bowler:N', title='🏏 Bowler'),
                alt.Tooltip('economy:Q', title='💰 Economy', format='.2f'),
                alt.Tooltip('is_wicket:Q', title='🎯 Wickets'),
                alt.Tooltip('average:Q', title='📊 Average', format='.2f'),
                alt.Tooltip('strike_rate:Q', title='⚡ Strike Rate', format='.1f'),
                alt.Tooltip('overs:Q', title='⏱️ Overs', format='.1f'),
                alt.Tooltip('total_runs:Q', title='🏃 Runs Conceded'),
                alt.Tooltip('dot_percentage:Q', title='⚫ Dot %', format='.1f'),
                alt.Tooltip('boundary_percentage:Q', title='🔴 Boundary %', format='.1f'),
                alt.Tooltip('fours:Q', title='4️⃣ Fours'),
                alt.Tooltip('sixes:Q', title='6️⃣ Sixes')
            ]
        )
        
        # Add text labels showing economy rate on bars
        text_labels = base.mark_text(
            align='left',
            baseline='middle',
            dx=5,
            fontSize=13,
            fontWeight='bold',
            color='#f8fafc' # Light color for dark theme
        ).encode(
            x=alt.X('economy:Q'),
            text=alt.Text('economy:Q', format='.2f')
        )
        
        # Add wickets and dots count as secondary text
        wicket_labels = base.mark_text(
            align='left',
            baseline='middle',
            dx=45,
            fontSize=11,
            color='#94a3b8',
            fontWeight=500
        ).encode(
            x=alt.X('economy:Q'),
            text=alt.Text('wicket_text:N')
        )
        
        # Combine all layers
        chart = (bars + text_labels + wicket_labels).properties(
            height=max(300, len(bowler_stats) * 45), # Dynamic height based on bowlers
            title={
                'text': [f'{team} - Bowler Economy Analysis'],
                'subtitle': [
                    'Ranked by economy rate (minimum 4 overs)',
                    'Lower economy = Better performance'
                ],
                'fontSize': 18,
                'fontWeight': 'bold',
                'color': '#f8fafc',
                'subtitleFontSize': 12,
                'subtitleColor': '#94a3b8',
                'anchor': 'start',
                'offset': 20,
                'font': 'Segoe UI'
            }
        ).configure_axis(
            labelFontSize=11,
            titleFontSize=13,
            titleFontWeight=600,
            labelFont='Segoe UI',
            titleFont='Segoe UI'
        ).configure_view(
            strokeWidth=0,
            fill='transparent'
        ).configure_legend(
            titleFontSize=12,
            labelFontSize=11,
            symbolType='circle',
            titleFont='Segoe UI',
            labelFont='Segoe UI'
        ).interactive()
        
        return chart
    
    # -----------------------------------------------------------------------------
    # Interactive Plotly 3D Cricket Ball Animation
    # -----------------------------------------------------------------------------
    
    def create_3d_animated_trajectory():
        import plotly.graph_objects as go
        import numpy as np

        # Pitch dimensions
        pitch_y = np.linspace(0, 20, 2)
        pitch_x = np.linspace(-1.5, 1.5, 2)
        Y, X = np.meshgrid(pitch_y, pitch_x)
        Z = np.zeros_like(X)

        # Base figure with the pitch surface
        fig = go.Figure(data=[
            go.Surface(x=X, y=Y, z=Z, colorscale=[[0, '#654321'], [1, '#654321']], showscale=False, opacity=0.9, name='Pitch', hoverinfo='skip')
        ])
        
        # Add pitch creases (Popping and Bowling creases)
        crease_lines = []
        for y_c in [0, 1.22, 18.78, 20]:
            crease_lines.append(go.Scatter3d(
                x=[-1.5, 1.5], y=[y_c, y_c], z=[0.01, 0.01],
                mode='lines', line=dict(color='white', width=3), showlegend=False, hoverinfo='skip'
            ))
        
        for crease in crease_lines:
            fig.add_trace(crease)

        # Add stumps (Bowler end at y=0, Batter end at y=20)
        for y_pos in [0, 20]:
            for x in [-0.11, 0, 0.11]:
                fig.add_trace(go.Scatter3d(
                    x=[x, x], y=[y_pos, y_pos], z=[0, 0.71],
                    mode='lines', line=dict(color='white', width=4), showlegend=False, hoverinfo='skip'
                ))
            # Bails
            fig.add_trace(go.Scatter3d(
                x=[-0.11, 0.11], y=[y_pos, y_pos], z=[0.71, 0.71],
                mode='lines', line=dict(color='white', width=4), showlegend=False, hoverinfo='skip'
            ))

        # Define ball trajectories
        frames_data = []
        num_frames = 50
        
        # 1. Inswinging Yorker (Red)
        t = np.linspace(0, 1, num_frames)
        y1 = np.linspace(0, 20, num_frames)
        x1 = np.where(t < 0.5, -0.3 * t, -0.15 + 0.15*(t-0.5)/0.5) # Swings in to middle stump
        z1 = 2.2 - 2.2 * t  # Release height 2.2m, hits base of stumps

        # 2. Bouncer (Yellow)
        t_bounce2 = 0.55
        y2 = np.linspace(0, 20, num_frames)
        x2 = np.linspace(-0.2, 0.2, num_frames)
        z2 = np.where(t < t_bounce2, 2.2 - 2.2*(t/t_bounce2), 0.0 + 1.8*((t-t_bounce2)/(1-t_bounce2)))
        
        # 3. Good Length Outswinger (Orange)
        t_bounce3 = 0.8
        y3 = np.linspace(0, 20, num_frames)
        x3 = np.where(t < t_bounce3, 0.15 * (t/t_bounce3), 0.15 + 0.35*((t-t_bounce3)/(1-t_bounce3)))
        z3 = np.where(t < t_bounce3, 2.1 - 2.1*(t/t_bounce3), 0.0 + 0.7*((t-t_bounce3)/(1-t_bounce3)))

        # Add Pitch Marks (Impact points)
        fig.add_trace(go.Scatter3d(x=[0], y=[20 * 0.55], z=[0.02], mode='markers', marker=dict(size=8, color='#eab308', symbol='diamond', opacity=0.7), name='Bouncer Pitch'))
        fig.add_trace(go.Scatter3d(x=[0.15], y=[20 * 0.8], z=[0.02], mode='markers', marker=dict(size=8, color='#f97316', symbol='diamond', opacity=0.7), name='Outswinger Pitch'))

        # Calculate offset for ball traces
        ball_idx = len(fig.data) 
        
        # Add initial balls
        fig.add_trace(go.Scatter3d(x=[x1[0]], y=[y1[0]], z=[z1[0]], mode='markers', marker=dict(size=6, color='#ef4444'), name='Inswinging Yorker'))
        fig.add_trace(go.Scatter3d(x=[x2[0]], y=[y2[0]], z=[z2[0]], mode='markers', marker=dict(size=6, color='#eab308'), name='Bouncer'))
        fig.add_trace(go.Scatter3d(x=[x3[0]], y=[y3[0]], z=[z3[0]], mode='markers', marker=dict(size=6, color='#f97316'), name='Good Length Outswinger'))

        # Build Frames
        frames = []
        for k in range(num_frames):
            frame_data = [
                go.Scatter3d(x=x1[:k+1], y=y1[:k+1], z=z1[:k+1], mode='lines+markers', line=dict(color='#ef4444', width=4), marker=dict(size=[0 if i<k else 7 for i in range(k+1)], color='#ef4444')),
                go.Scatter3d(x=x2[:k+1], y=y2[:k+1], z=z2[:k+1], mode='lines+markers', line=dict(color='#eab308', width=4), marker=dict(size=[0 if i<k else 7 for i in range(k+1)], color='#eab308')),
                go.Scatter3d(x=x3[:k+1], y=y3[:k+1], z=z3[:k+1], mode='lines+markers', line=dict(color='#f97316', width=4), marker=dict(size=[0 if i<k else 7 for i in range(k+1)], color='#f97316')),
            ]
            frames.append(go.Frame(data=frame_data, traces=[ball_idx, ball_idx+1, ball_idx+2], name=str(k)))
        
        fig.frames = frames

        # Setup animation controls and clean layout
        fig.update_layout(
            scene=dict(
                xaxis=dict(title='', range=[-2, 2], showgrid=False, zeroline=False, showbackground=False, showticklabels=False),
                yaxis=dict(title='', range=[-1, 21], showgrid=False, zeroline=False, showbackground=False, showticklabels=False),
                zaxis=dict(title='', range=[0, 3], showgrid=False, zeroline=False, showbackground=False, showticklabels=False),
                aspectmode='manual',
                aspectratio=dict(x=1, y=3.5, z=0.5), # Slightly more elongated
                camera=dict(
                    eye=dict(x=-1.5, y=-2.0, z=0.6), # Isometric view for better depth perception!
                    center=dict(x=0, y=0, z=0)
                )
            ),
            updatemenus=[dict(
                type="buttons",
                showactive=False,
                buttons=[
                    dict(label="▶ Play Animation", method="animate", args=[None, dict(frame=dict(duration=40, redraw=True), fromcurrent=True, mode="immediate", transition=dict(duration=0))]),
                    dict(label="⏸ Pause", method="animate", args=[[None], dict(frame=dict(duration=0, redraw=False), mode="immediate", transition=dict(duration=0))])
                ],
                x=0.5, y=-0.1, xanchor="center", yanchor="top", direction="left",
                bgcolor="#1e293b", font=dict(color="#f8fafc")
            )],
            margin=dict(l=0, r=0, b=0, t=0),
            height=600,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            legend=dict(x=0.8, y=0.9, bgcolor='rgba(15,23,42,0.8)', font=dict(color='#f8fafc'))
        )
        
        return fig
    
    # -----------------------------------------------------------------------------
    # 3. Three.js 3D Visualization Helper
    # -----------------------------------------------------------------------------
    
    def render_threejs_chart(data, chart_type, title, width=600, height=400):
        import hashlib
        div_id = f"chart_{hashlib.md5(title.encode()).hexdigest()[:8]}"
        data_json = json.dumps(data)
        
        if chart_type == 'grouped_bar_3d':
            script = f"""
            const scene = new THREE.Scene();
            scene.background = new THREE.Color(0xf5f5f5);
            
            const camera = new THREE.PerspectiveCamera(60, {width}/{height}, 0.1, 1000);
            camera.position.set(15, 15, 15);
            
            const renderer = new THREE.WebGLRenderer({{ antialias: true }});
            renderer.setSize({width}, {height});
            renderer.setClearColor(0xf5f5f5, 1);
            
            const container = document.getElementById('{div_id}');
            container.style.position = 'relative';
            container.appendChild(renderer.domElement);
            
            // Basic Tooltip div
            const tooltip = document.createElement('div');
            tooltip.style.position = 'absolute';
            tooltip.style.backgroundColor = '#ffffff';
            tooltip.style.color = '#000000';
            tooltip.style.padding = '8px';
            tooltip.style.borderRadius = '3px';
            tooltip.style.pointerEvents = 'none';
            tooltip.style.display = 'none';
            tooltip.style.fontFamily = 'Arial, sans-serif';
            tooltip.style.fontSize = '13px';
            tooltip.style.boxShadow = '0 2px 5px rgba(0,0,0,0.2)';
            tooltip.style.border = '1px solid #cccccc';
            tooltip.style.zIndex = '1000';
            container.appendChild(tooltip);
            
            const controls = new THREE.OrbitControls(camera, renderer.domElement);
            controls.enableDamping = true;
            controls.dampingFactor = 0.05;
            
            const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
            scene.add(ambientLight);
            const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
            directionalLight.position.set(10, 20, 10);
            scene.add(directionalLight);
            
            let maxValue = 0;
            data.forEach(cat => {{
                cat.values.forEach(val => {{
                    if (val.value > maxValue) maxValue = val.value;
                }});
            }});
            
            const barWidth = 1.5;
            const barDepth = 1.5;
            const spacing = 5;
            const groupSpacing = 2;
            const colors = [0xFDB913, 0x004BA0]; // Original basic colors
            
            const bars = [];
            
            data.forEach((category, catIndex) => {{
                category.values.forEach((val, teamIndex) => {{
                    const height = (val.value / maxValue) * 10;
                    const geometry = new THREE.BoxGeometry(barWidth, height, barDepth);
                    const material = new THREE.MeshPhongMaterial({{ 
                        color: colors[teamIndex], 
                        shininess: 100
                    }});
                    const bar = new THREE.Mesh(geometry, material);
                    
                    const xPos = catIndex * spacing - (data.length * spacing / 2);
                    const zPos = teamIndex * groupSpacing - 1;
                    bar.position.set(xPos, height/2, zPos);
                    
                    bar.userData = {{
                        team: val.label,
                        phase: category.category,
                        value: val.value.toFixed(2),
                        originalColor: colors[teamIndex]
                    }};
                    
                    scene.add(bar);
                    bars.push(bar);
                }});
            }});
            
            const gridHelper = new THREE.GridHelper(30, 30, 0x888888, 0xdddddd);
            scene.add(gridHelper);
            
            // Interactivity and Optimization
            const raycaster = new THREE.Raycaster();
            const mouse = new THREE.Vector2();
            let hoveredBar = null;
            let needsUpdate = true;
            
            controls.addEventListener('change', () => {{ needsUpdate = true; }});
            
            container.addEventListener('mousemove', (event) => {{
                const rect = renderer.domElement.getBoundingClientRect();
                mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
                mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
                
                raycaster.setFromCamera(mouse, camera);
                const intersects = raycaster.intersectObjects(bars);
                
                if (intersects.length > 0) {{
                    const object = intersects[0].object;
                    
                    if (hoveredBar !== object) {{
                        if (hoveredBar) hoveredBar.material.color.setHex(hoveredBar.userData.originalColor);
                        hoveredBar = object;
                        hoveredBar.material.color.offsetHSL(0, 0, 0.2); // Lighten on hover
                        needsUpdate = true;
                    }}
                    
                    const data = object.userData;
                    tooltip.innerHTML = `<strong>${{data.phase}}</strong><br/>${{data.team}}: <strong>${{data.value}}</strong>`;
                    tooltip.style.display = 'block';
                    tooltip.style.left = (event.clientX - rect.left + 15) + 'px';
                    tooltip.style.top = (event.clientY - rect.top + 15) + 'px';
                    container.style.cursor = 'pointer';
                }} else {{
                    if (hoveredBar) {{
                        hoveredBar.material.color.setHex(hoveredBar.userData.originalColor);
                        hoveredBar = null;
                        needsUpdate = true;
                    }}
                    tooltip.style.display = 'none';
                    container.style.cursor = 'default';
                }}
            }});
            
            container.addEventListener('mouseleave', () => {{
                if (hoveredBar) {{
                    hoveredBar.material.color.setHex(hoveredBar.userData.originalColor);
                    hoveredBar = null;
                    needsUpdate = true;
                }}
                tooltip.style.display = 'none';
                container.style.cursor = 'default';
            }});
            
            function animate() {{
                requestAnimationFrame(animate);
                controls.update(); // requires update for damping
                
                // Always render while damping is active, but we can't easily detect when damping stops.
                // For a small scene, simple requestAnimationFrame is OK if we're not allocating objects.
                renderer.render(scene, camera);
            }}
            animate();
            """
        
        elif chart_type == 'bar_3d':
            script = f"""
            const scene = new THREE.Scene();
            scene.background = new THREE.Color(0xf5f5f5);
            
            const camera = new THREE.PerspectiveCamera(60, {width}/{height}, 0.1, 1000);
            camera.position.set(10, 10, 15);
            
            const renderer = new THREE.WebGLRenderer({{ antialias: true }});
            renderer.setSize({width}, {height});
            document.getElementById('{div_id}').appendChild(renderer.domElement);
            
            const controls = new THREE.OrbitControls(camera, renderer.domElement);
            controls.enableDamping = true;
            
            const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
            scene.add(ambientLight);
            const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
            directionalLight.position.set(10, 20, 10);
            scene.add(directionalLight);
            
            const maxValue = Math.max(...data.map(d => d.value));
            const barWidth = 1.5;
            const spacing = 3;
            
            data.forEach((item, index) => {{
                const height = (item.value / maxValue) * 10;
                const hue = (index / data.length) * 0.7;
                
                const geometry = new THREE.BoxGeometry(barWidth, height, barWidth);
                const material = new THREE.MeshPhongMaterial({{ 
                    color: new THREE.Color().setHSL(hue, 0.7, 0.5),
                    shininess: 100
                }});
                const bar = new THREE.Mesh(geometry, material);
                
                bar.position.set((index - data.length/2) * spacing, height/2, 0);
                bar.userData = {{
                    player: item.label,
                    strikeRate: item.value.toFixed(2),
                    balls: item.balls || 0,
                    runs: item.runs || 0,
                    dismissals: item.dismissals || 0
                }};
                
                scene.add(bar);
            }});
            
            const gridHelper = new THREE.GridHelper(20, 20, 0x888888, 0xdddddd);
            scene.add(gridHelper);
            
            controls.enableDamping = false;
            controls.addEventListener('change', () => renderer.render(scene, camera));
            renderer.render(scene, camera);
            """
        
        elif chart_type == 'pie_3d':
            script = f"""
            const scene = new THREE.Scene();
            scene.background = new THREE.Color(0xf5f5f5);
            
            const camera = new THREE.PerspectiveCamera(60, {width}/{height}, 0.1, 1000);
            camera.position.set(0, 8, 12);
            
            const renderer = new THREE.WebGLRenderer({{ antialias: true }});
            renderer.setSize({width}, {height});
            document.getElementById('{div_id}').appendChild(renderer.domElement);
            
            const controls = new THREE.OrbitControls(camera, renderer.domElement);
            controls.enableDamping = true;
            
            const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
            scene.add(ambientLight);
            const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
            directionalLight.position.set(5, 10, 5);
            scene.add(directionalLight);
            
            const total = data.reduce((sum, item) => sum + item.value, 0);
            let currentAngle = 0;
            const innerRadius = 2;
            const outerRadius = 5;
            const depth = 1;
            
            data.forEach((item, index) => {{
                const angle = (item.value / total) * Math.PI * 2;
                const hue = (index / data.length);
                
                const shape = new THREE.Shape();
                const startAngle = currentAngle;
                const endAngle = currentAngle + angle;
                
                shape.moveTo(outerRadius * Math.cos(startAngle), outerRadius * Math.sin(startAngle));
                shape.absarc(0, 0, outerRadius, startAngle, endAngle, false);
                shape.lineTo(innerRadius * Math.cos(endAngle), innerRadius * Math.sin(endAngle));
                shape.absarc(0, 0, innerRadius, endAngle, startAngle, true);
                
                const geometry = new THREE.ExtrudeGeometry(shape, {{
                    depth: depth,
                    bevelEnabled: true,
                    bevelThickness: 0.1,
                    bevelSize: 0.1,
                    bevelSegments: 2
                }});
                
                const material = new THREE.MeshPhongMaterial({{ 
                    color: new THREE.Color().setHSL(hue, 0.8, 0.6),
                    shininess: 100
                }});
                
                const mesh = new THREE.Mesh(geometry, material);
                mesh.position.z = -depth/2;
                mesh.userData = {{
                    label: item.label,
                    value: item.value,
                    percentage: ((item.value / total) * 100).toFixed(1)
                }};
                
                scene.add(mesh);
                currentAngle = endAngle;
            }});
            
            controls.enableDamping = false;
            controls.addEventListener('change', () => renderer.render(scene, camera));
            renderer.render(scene, camera);
            """
        else:
            script = ""
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
            <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
            <style>
                body {{ margin: 0; padding: 20px; font-family: sans-serif; }}
                #title {{ text-align: center; font-size: 18px; font-weight: bold; margin-bottom: 15px; }}
                #{div_id} {{ border: 1px solid #ddd; border-radius: 8px; overflow: hidden; }}
            </style>
        </head>
        <body>
            <div id="title">{title}</div>
            <div id="{div_id}"></div>
            <script>
                const data = {data_json};
                {script}
            </script>
        </body>
        </html>
        """
        return html
    
    def render_pitch_map(data, title, width=800, height=600):
        """Render advanced 3D pitch map with realistic cricket pitch background"""
        div_id = f"pitch_{hashlib.md5(title.encode()).hexdigest()[:8]}"
        data_json = json.dumps(data)
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
            <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
            <style>
                body {{ margin: 0; padding: 15px; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }}
                .pitch-container-{div_id} {{ 
                    position: relative;
                    background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
                    padding: 20px;
                    border-radius: 12px;
                    box-shadow: 0 8px 32px rgba(0,0,0,0.3);
                }}
                .pitch-title-{div_id} {{ 
                    text-align: center; 
                    font-size: 20px; 
                    font-weight: bold; 
                    margin-bottom: 15px;
                    color: white;
                    text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
                }}
                .pitch-legend-{div_id} {{ 
                    position: absolute; 
                    top: 70px; 
                    right: 25px; 
                    background: rgba(255,255,255,0.98); 
                    padding: 15px; 
                    border-radius: 10px; 
                    font-size: 12px; 
                    box-shadow: 0 4px 20px rgba(0,0,0,0.3); 
                    z-index: 10;
                    border: 2px solid #1e3c72;
                }}
                .legend-item-{div_id} {{ 
                    display: flex; 
                    align-items: center; 
                    margin: 6px 0; 
                    font-weight: 500;
                }}
                .legend-color-{div_id} {{ 
                    width: 16px; 
                    height: 16px; 
                    border-radius: 50%; 
                    margin-right: 8px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.2);
                }}
                .controls-{div_id} {{
                    position: absolute;
                    top: 70px;
                    left: 25px;
                    display: flex;
                    flex-direction: column;
                    gap: 8px;
                    z-index: 10;
                }}
                .view-btn-{div_id} {{
                    background: rgba(255, 255, 255, 0.95);
                    border: 2px solid #1e3c72;
                    padding: 10px 18px;
                    border-radius: 8px;
                    cursor: pointer;
                    font-weight: 600;
                    font-size: 13px;
                    transition: all 0.3s ease;
                    color: #1e3c72;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.2);
                }}
                .view-btn-{div_id}:hover {{
                    background: #1e3c72;
                    color: white;
                    transform: translateY(-2px);
                    box-shadow: 0 4px 16px rgba(30, 60, 114, 0.4);
                }}
                #{div_id} {{ 
                    border-radius: 8px;
                    overflow: hidden;
                    box-shadow: 0 4px 16px rgba(0,0,0,0.3);
                }}
            </style>
        </head>
        <body>
            <div class="pitch-container-{div_id}">
                <div class="pitch-title-{div_id}">{title}</div>
                <div class="controls-{div_id}">
                    <button class="view-btn-{div_id}" onclick="setView_{div_id}('top')">📍 Top View</button>
                    <button class="view-btn-{div_id}" onclick="setView_{div_id}('bowler')">🎯 Bowler End</button>
                    <button class="view-btn-{div_id}" onclick="setView_{div_id}('batter')">🏏 Batter End</button>
                    <button class="view-btn-{div_id}" onclick="setView_{div_id}('side')">👁️ Side View</button>
                    <button class="view-btn-{div_id}" onclick="setView_{div_id}('reset')">🔄 Reset</button>
                </div>
                <div class="pitch-legend-{div_id}">
                    <div style="font-weight: bold; margin-bottom: 8px; color: #1e3c72; font-size: 14px;">Ball Outcomes</div>
                    <div class="legend-item-{div_id}"><div class="legend-color-{div_id}" style="background: #808080;"></div><span>Dot Ball (0)</span></div>
                    <div class="legend-item-{div_id}"><div class="legend-color-{div_id}" style="background: #2196f3;"></div><span>Singles (1-3)</span></div>
                    <div class="legend-item-{div_id}"><div class="legend-color-{div_id}" style="background: #00ff00;"></div><span>Four (4)</span></div>
                    <div class="legend-item-{div_id}"><div class="legend-color-{div_id}" style="background: #9c27b0;"></div><span>Six (6)</span></div>
                    <div class="legend-item-{div_id}"><div class="legend-color-{div_id}" style="background: #ff0000;"></div><span>Wicket (W)</span></div>
                </div>
                <div id="{div_id}"></div>
            </div>
            <script>
            (function() {{
                const pitchData = {data_json};
                const scene = new THREE.Scene();
                scene.background = new THREE.Color(0x87ceeb);
                scene.fog = new THREE.Fog(0x87ceeb, 50, 100);
                
                const camera = new THREE.PerspectiveCamera(50, {width}/{height}, 0.1, 1000);
                camera.position.set(0, 30, 35);
                camera.lookAt(0, 0, 11);
                
                const renderer = new THREE.WebGLRenderer({{ antialias: true, alpha: true }});
                renderer.setSize({width}, {height});
                renderer.setPixelRatio(window.devicePixelRatio);
                renderer.shadowMap.enabled = false;
                // renderer.shadowMap.type = THREE.PCFSoftShadowMap;
                renderer.toneMapping = THREE.ACESFilmicToneMapping;
                renderer.toneMappingExposure = 1.0;
                document.getElementById('{div_id}').appendChild(renderer.domElement);
                
                const controls = new THREE.OrbitControls(camera, renderer.domElement);
                controls.enableDamping = true;
                controls.dampingFactor = 0.08;
                controls.minDistance = 15;
                controls.maxDistance = 80;
                controls.maxPolarAngle = Math.PI / 2.1;
                controls.target.set(0, 0, 11);
                
                // Enhanced lighting system
                const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
                scene.add(ambientLight);
                
                const mainLight = new THREE.DirectionalLight(0xffffff, 0.9);
                mainLight.position.set(15, 35, 20);
                mainLight.castShadow = true;
                mainLight.shadow.mapSize.width = 4096;
                mainLight.shadow.mapSize.height = 4096;
                mainLight.shadow.camera.near = 0.5;
                mainLight.shadow.camera.far = 100;
                mainLight.shadow.camera.left = -30;
                mainLight.shadow.camera.right = 30;
                mainLight.shadow.camera.top = 30;
                mainLight.shadow.camera.bottom = -30;
                scene.add(mainLight);
                
                const fillLight = new THREE.DirectionalLight(0xffffff, 0.3);
                fillLight.position.set(-15, 20, 10);
                scene.add(fillLight);
                
                const backLight = new THREE.DirectionalLight(0xffffff, 0.2);
                backLight.position.set(0, 15, -20);
                scene.add(backLight);
                
                // Cricket Stadium - Circular outfield
                const stadiumRadius = 70;
                
                // Stadium bowl/ground
                const stadiumGeometry = new THREE.CircleGeometry(stadiumRadius, 64);
                const stadiumMaterial = new THREE.MeshStandardMaterial({{ 
                    color: 0x1a5c1a,
                    roughness: 0.85,
                    metalness: 0.1
                }});
                const stadium = new THREE.Mesh(stadiumGeometry, stadiumMaterial);
                stadium.rotation.x = -Math.PI / 2;
                stadium.position.set(0, -0.05, 11);
                stadium.receiveShadow = true;
                scene.add(stadium);
                
                // Add stadium grass texture pattern
                const stadiumTexture = document.createElement('canvas');
                stadiumTexture.width = 1024;
                stadiumTexture.height = 1024;
                const stadiumCtx = stadiumTexture.getContext('2d');
                
                // Base green
                stadiumCtx.fillStyle = '#1a5c1a';
                stadiumCtx.fillRect(0, 0, 1024, 1024);
                
                // Grass blades
                for (let i = 0; i < 500; i++) {{
                    const shade = Math.random() * 30 - 15;
                    stadiumCtx.fillStyle = `rgb(${{26 + shade}},${{92 + shade * 1.5}},${{26 + shade}})`;
                    stadiumCtx.fillRect(Math.random() * 1024, Math.random() * 1024, 2, 2);
                }}
                
                // Mowing pattern - stripes
                stadiumCtx.globalAlpha = 0.15;
                for (let i = 0; i < 20; i++) {{
                    if (i % 2 === 0) {{
                        stadiumCtx.fillStyle = '#0d4a0d';
                    }} else {{
                        stadiumCtx.fillStyle = '#236b23';
                    }}
                    const stripeWidth = 1024 / 20;
                    stadiumCtx.fillRect(i * stripeWidth, 0, stripeWidth, 1024);
                }}
                stadiumCtx.globalAlpha = 1.0;
                
                const texture = new THREE.CanvasTexture(stadiumTexture);
                texture.wrapS = THREE.RepeatWrapping;
                texture.wrapT = THREE.RepeatWrapping;
                texture.repeat.set(4, 4);
                stadium.material.map = texture;
                stadium.material.needsUpdate = true;
                
                // Inner circle (30-yard circle)
                const innerCircleGeometry = new THREE.RingGeometry(27, 27.3, 64);
                const innerCircleMaterial = new THREE.MeshStandardMaterial({{ 
                    color: 0xffffff,
                    roughness: 0.9,
                    emissive: 0xffffff,
                    emissiveIntensity: 0.1
                }});
                const innerCircle = new THREE.Mesh(innerCircleGeometry, innerCircleMaterial);
                innerCircle.rotation.x = -Math.PI / 2;
                innerCircle.position.set(0, 0, 11);
                innerCircle.receiveShadow = true;
                scene.add(innerCircle);
                
                // Boundary rope
                const boundaryGeometry = new THREE.RingGeometry(stadiumRadius - 0.5, stadiumRadius, 64);
                const boundaryMaterial = new THREE.MeshStandardMaterial({{ 
                    color: 0xffffff,
                    roughness: 0.7,
                    emissive: 0xffffff,
                    emissiveIntensity: 0.2
                }});
                const boundary = new THREE.Mesh(boundaryGeometry, boundaryMaterial);
                boundary.rotation.x = -Math.PI / 2;
                boundary.position.set(0, 0.02, 11);
                scene.add(boundary);
                
                // Stadium boundary markers (advertising boards simulation)
                const markerCount = 32;
                for (let i = 0; i < markerCount; i++) {{
                    const angle = (i / markerCount) * Math.PI * 2;
                    const radius = stadiumRadius - 2;
                    const x = Math.cos(angle) * radius;
                    const z = Math.sin(angle) * radius + 11;
                    
                    const markerGeometry = new THREE.BoxGeometry(3, 1.5, 0.2);
                    const hue = (i / markerCount) * 360;
                    const markerMaterial = new THREE.MeshStandardMaterial({{ 
                        color: new THREE.Color(`hsl(${{hue}}, 70%, 50%)`),
                        roughness: 0.5,
                        metalness: 0.3,
                        emissive: new THREE.Color(`hsl(${{hue}}, 70%, 30%)`),
                        emissiveIntensity: 0.3
                    }});
                    const marker = new THREE.Mesh(markerGeometry, markerMaterial);
                    marker.position.set(x, 0.75, z);
                    marker.lookAt(0, 0.75, 11);
                    marker.castShadow = false;
                    scene.add(marker);
                }}
                
                // Floodlight towers (4 corners)
                const floodlightPositions = [
                    {{ x: 50, z: -30 }},
                    {{ x: -50, z: -30 }},
                    {{ x: 50, z: 52 }},
                    {{ x: -50, z: 52 }}
                ];
                
                floodlightPositions.forEach(pos => {{
                    // Tower pole
                    const poleGeometry = new THREE.CylinderGeometry(0.5, 0.8, 40, 8);
                    const poleMaterial = new THREE.MeshStandardMaterial({{ 
                        color: 0x808080,
                        roughness: 0.6,
                        metalness: 0.7
                    }});
                    const pole = new THREE.Mesh(poleGeometry, poleMaterial);
                    pole.position.set(pos.x, 20, pos.z);
                    pole.castShadow = false;
                    scene.add(pole);
                    
                    // Light fixture on top
                    const lightGeometry = new THREE.BoxGeometry(3, 2, 1);
                    const lightMaterial = new THREE.MeshStandardMaterial({{ 
                        color: 0xffff00,
                        roughness: 0.3,
                        metalness: 0.5,
                        emissive: 0xffff88,
                        emissiveIntensity: 0.8
                    }});
                    const lightFixture = new THREE.Mesh(lightGeometry, lightMaterial);
                    lightFixture.position.set(pos.x, 41, pos.z);
                    lightFixture.lookAt(0, 0, 11);
                    scene.add(lightFixture);
                }});
                
                // Cricket pitch - tan/brown color with texture (centered in stadium)
                const pitchGeometry = new THREE.PlaneGeometry(2.6, 22.5);
                const pitchCanvas = document.createElement('canvas');
                pitchCanvas.width = 256;
                pitchCanvas.height = 2048;
                const pitchCtx = pitchCanvas.getContext('2d');
                
                // Base color - light brown
                pitchCtx.fillStyle = '#c9a875';
                pitchCtx.fillRect(0, 0, 256, 2048);
                
                // Add dirt texture
                for (let i = 0; i < 8000; i++) {{
                    const shade = Math.random() * 40 - 20;
                    pitchCtx.fillStyle = `rgb(${{201 + shade}},${{168 + shade}},${{117 + shade}})`;
                    pitchCtx.fillRect(Math.random() * 256, Math.random() * 2048, 3, 3);
                }}
                
                // Worn areas (darker patches)
                pitchCtx.fillStyle = 'rgba(160, 130, 80, 0.3)';
                for (let i = 0; i < 5; i++) {{
                    const y = 800 + Math.random() * 400;
                    pitchCtx.fillRect(60 + Math.random() * 130, y, 40 + Math.random() * 30, 60 + Math.random() * 40);
                }}
                
                const pitchTexture = new THREE.CanvasTexture(pitchCanvas);
                const pitchMaterial = new THREE.MeshStandardMaterial({{ 
                    map: pitchTexture,
                    roughness: 0.8,
                    metalness: 0.0
                }});
                const pitch = new THREE.Mesh(pitchGeometry, pitchMaterial);
                pitch.rotation.x = -Math.PI / 2;
                pitch.position.set(0, 0, 11);
                pitch.receiveShadow = true;
                pitch.castShadow = false;
                scene.add(pitch);
                
                // Pitch markings - white creases
                const creaseMaterial = new THREE.MeshStandardMaterial({{ 
                    color: 0xffffff,
                    roughness: 0.7,
                    emissive: 0xffffff,
                    emissiveIntensity: 0.2
                }});
                
                // Bowling creases
                const creaseGeometry = new THREE.PlaneGeometry(2.7, 0.08);
                const crease1 = new THREE.Mesh(creaseGeometry, creaseMaterial);
                crease1.rotation.x = -Math.PI / 2;
                crease1.position.set(0, 0.01, 0);
                crease1.receiveShadow = true;
                scene.add(crease1);
                
                const crease2 = new THREE.Mesh(creaseGeometry, creaseMaterial);
                crease2.rotation.x = -Math.PI / 2;
                crease2.position.set(0, 0.01, 22);
                crease2.receiveShadow = true;
                scene.add(crease2);
                
                // Popping creases (4 feet in front of stumps)
                const poppingCreaseGeometry = new THREE.PlaneGeometry(2.7, 0.06);
                const poppingCrease1 = new THREE.Mesh(poppingCreaseGeometry, creaseMaterial);
                poppingCrease1.rotation.x = -Math.PI / 2;
                poppingCrease1.position.set(0, 0.01, 1.22);
                scene.add(poppingCrease1);
                
                const poppingCrease2 = new THREE.Mesh(poppingCreaseGeometry, creaseMaterial);
                poppingCrease2.rotation.x = -Math.PI / 2;
                poppingCrease2.position.set(0, 0.01, 20.78);
                scene.add(poppingCrease2);
                
                // Return creases (perpendicular lines)
                const returnCreaseGeometry = new THREE.PlaneGeometry(0.06, 2.44);
                for (let x of [-1.35, 1.35]) {{
                    const returnCrease1 = new THREE.Mesh(returnCreaseGeometry, creaseMaterial);
                    returnCrease1.rotation.x = -Math.PI / 2;
                    returnCrease1.position.set(x, 0.01, 0);
                    scene.add(returnCrease1);
                    
                    const returnCrease2 = new THREE.Mesh(returnCreaseGeometry, creaseMaterial);
                    returnCrease2.rotation.x = -Math.PI / 2;
                    returnCrease2.position.set(x, 0.01, 22);
                    scene.add(returnCrease2);
                }}
                
                // Stumps - realistic wooden stumps
                const stumpMaterial = new THREE.MeshStandardMaterial({{ 
                    color: 0x8B4513,
                    roughness: 0.7,
                    metalness: 0.1
                }});
                
                const stumpPositions = [-0.115, 0, 0.115];
                for (let x of stumpPositions) {{
                    // Bowler end stumps
                    const stump1 = new THREE.Mesh(
                        new THREE.CylinderGeometry(0.022, 0.022, 0.71, 8), 
                        stumpMaterial
                    );
                    stump1.position.set(x, 0.355, 0);
                    stump1.castShadow = true;
                    stump1.receiveShadow = true;
                    scene.add(stump1);
                    
                    // Batter end stumps
                    const stump2 = new THREE.Mesh(
                        new THREE.CylinderGeometry(0.022, 0.022, 0.71, 8), 
                        stumpMaterial
                    );
                    stump2.position.set(x, 0.355, 22);
                    stump2.castShadow = true;
                    stump2.receiveShadow = true;
                    scene.add(stump2);
                }}
                
                // Bails on top of stumps
                const bailMaterial = new THREE.MeshStandardMaterial({{ 
                    color: 0x8B4513,
                    roughness: 0.6,
                    metalness: 0.2
                }});
                
                for (let i = 0; i < 2; i++) {{
                    const x = i === 0 ? -0.0575 : 0.0575;
                    
                    const bail1 = new THREE.Mesh(
                        new THREE.CylinderGeometry(0.012, 0.012, 0.115, 8),
                        bailMaterial
                    );
                    bail1.rotation.z = Math.PI / 2;
                    bail1.position.set(x, 0.73, 0);
                    bail1.castShadow = true;
                    scene.add(bail1);
                    
                    const bail2 = new THREE.Mesh(
                        new THREE.CylinderGeometry(0.012, 0.012, 0.115, 8),
                        bailMaterial
                    );
                    bail2.rotation.z = Math.PI / 2;
                    bail2.position.set(x, 0.73, 22);
                    bail2.castShadow = true;
                    scene.add(bail2);
                }}
                
                // Ball landing positions with enhanced materials
                const colorMap = {{ 
                    'red': 0xff0000, 
                    'purple': 0x9c27b0, 
                    'green': 0x00ff00, 
                    'blue': 0x2196f3, 
                    'gray': 0x808080 
                }};
                
                const sharedGeometry = new THREE.SphereGeometry(1, 16, 16);
                const sharedMaterials = {{}};
                for (const [key, colorHex] of Object.entries(colorMap)) {{
                    sharedMaterials[key] = new THREE.MeshStandardMaterial({{ 
                        color: colorHex,
                        roughness: 0.3,
                        metalness: 0.5,
                        emissive: colorHex,
                        emissiveIntensity: 0.4
                    }});
                }}
                
                pitchData.forEach(ball => {{
                    const radius = ball.size * 0.02;
                    const material = sharedMaterials[ball.color] || sharedMaterials['gray'];
                    const sphere = new THREE.Mesh(sharedGeometry, material);
                    sphere.scale.set(radius, radius, radius);
                    sphere.position.set(ball.x, radius + 0.01, ball.y);
                    sphere.castShadow = true;
                    sphere.receiveShadow = true;
                    sphere.userData = {{ 
                        batter: ball.batter, 
                        bowler: ball.bowler, 
                        runs: ball.runs, 
                        wicket: ball.wicket 
                    }};
                    scene.add(sphere);
                }});
                
                // View preset functions
                window.setView_{div_id} = function(view) {{
                    let targetPos, targetLookAt;
                    switch(view) {{
                        case 'top':
                            targetPos = {{ x: 0, y: 50, z: 11 }};
                            targetLookAt = {{ x: 0, y: 0, z: 11 }};
                            break;
                        case 'bowler':
                            targetPos = {{ x: 0, y: 8, z: -15 }};
                            targetLookAt = {{ x: 0, y: 0, z: 11 }};
                            break;
                        case 'batter':
                            targetPos = {{ x: 0, y: 8, z: 38 }};
                            targetLookAt = {{ x: 0, y: 0, z: 11 }};
                            break;
                        case 'side':
                            targetPos = {{ x: 25, y: 15, z: 11 }};
                            targetLookAt = {{ x: 0, y: 0, z: 11 }};
                            break;
                        case 'reset':
                            targetPos = {{ x: 0, y: 30, z: 35 }};
                            targetLookAt = {{ x: 0, y: 0, z: 11 }};
                            break;
                    }}
                    
                    const startPos = {{ x: camera.position.x, y: camera.position.y, z: camera.position.z }};
                    const startTime = Date.now();
                    const duration = 1200;
                    
                    function animateCamera() {{
                        const elapsed = Date.now() - startTime;
                        const progress = Math.min(elapsed / duration, 1);
                        const eased = progress < 0.5 ? 2 * progress * progress : -1 + (4 - 2 * progress) * progress;
                        
                        camera.position.x = startPos.x + (targetPos.x - startPos.x) * eased;
                        camera.position.y = startPos.y + (targetPos.y - startPos.y) * eased;
                        camera.position.z = startPos.z + (targetPos.z - startPos.z) * eased;
                        
                        controls.target.set(targetLookAt.x, targetLookAt.y, targetLookAt.z);
                        controls.update();
                        
                        if (progress < 1) {{
                            renderer.render(scene, camera);
                            requestAnimationFrame(animateCamera);
                        }} else {{
                            renderer.render(scene, camera); // Final render
                        }}
                    }}
                    animateCamera();
                }};
                
                controls.enableDamping = false;
                controls.addEventListener('change', () => renderer.render(scene, camera));
                
                // Initial render
                renderer.render(scene, camera);
            }})();
            </script>
        </body>
        </html>
        """
        return html
    
    def render_wagon_wheel(data, title, width=600, height=600, boundary_radius=None):
        """Render wagon wheel visualization with realistic cricket stadium using Three.js"""
        if boundary_radius is None:
            boundary_radius = DEFAULT_BOUNDARY
        data_json = json.dumps(data)
        div_id = f"wagon_wheel_{hashlib.md5(title.encode()).hexdigest()[:8]}"
        unique_id = hashlib.md5(title.encode()).hexdigest()[:8]
        ground_radius = boundary_radius + 5
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
            <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
            <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/loaders/GLTFLoader.js"></script>
            <style>
                body {{ 
                    margin: 0; 
                    padding: 0; 
                    font-family: 'Inter', sans-serif;
                    background: #0b0f1a;
                    color: #e2e8f0;
                }}
                .wagon-container {{ 
                    position: relative;
                    border: 1px solid rgba(255, 255, 255, 0.08); 
                    border-radius: 12px;
                    overflow: hidden;
                    background: #05070c;
                    box-shadow: 0 10px 40px rgba(0,0,0,0.6);
                }}
                .wagon-title {{
                    text-align: center;
                    font-size: 16px;
                    font-weight: 800;
                    color: white;
                    padding: 12px;
                    text-transform: uppercase;
                    letter-spacing: 2px;
                    font-family: 'Orbitron', sans-serif;
                    background: linear-gradient(135deg, #38bdf8, #818cf8);
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                }}
                .legend-tab-toggle {{
                    position: absolute;
                    top: 55px;
                    right: 15px;
                    background: rgba(15, 23, 42, 0.92);
                    padding: 8px 14px;
                    border-radius: 20px;
                    color: white;
                    font-size: 12px;
                    font-weight: 700;
                    backdrop-filter: blur(12px);
                    border: 1.5px solid rgba(56, 189, 248, 0.5);
                    box-shadow: 0 6px 24px rgba(0,0,0,0.4);
                    z-index: 105;
                    cursor: pointer;
                    user-select: none;
                    display: flex;
                    align-items: center;
                    gap: 8px;
                    transition: all 0.25s ease;
                }}
                .legend-tab-toggle:hover {{
                    background: rgba(30, 41, 59, 0.95);
                    border-color: #38bdf8;
                    transform: translateY(-2px);
                    box-shadow: 0 8px 28px rgba(56, 189, 248, 0.4);
                }}
                .tab-chevron {{
                    font-size: 10px;
                    color: #38bdf8;
                    transition: transform 0.3s ease;
                }}
                .legend-box {{
                    position: absolute;
                    top: 95px;
                    right: 15px;
                    background: rgba(15, 23, 42, 0.95);
                    padding: 12px 14px;
                    border-radius: 12px;
                    color: white;
                    font-size: 12px;
                    backdrop-filter: blur(16px);
                    border: 1.5px solid rgba(255,255,255,0.2);
                    box-shadow: 0 10px 40px rgba(0,0,0,0.6);
                    z-index: 100;
                    user-select: none;
                    min-width: 210px;
                    transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
                    transform-origin: top right;
                }}
                .legend-box.collapsed {{
                    opacity: 0;
                    pointer-events: none;
                    transform: scale(0.85) translateY(-10px);
                }}
                .legend-header {{
                    font-weight: 700;
                    font-size: 11px;
                    letter-spacing: 1px;
                    margin-bottom: 8px;
                    border-bottom: 1px solid rgba(255,255,255,0.2);
                    padding-bottom: 6px;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    color: #94a3b8;
                }}
                .reset-btn {{
                    font-size: 10px;
                    background: rgba(255,255,255,0.12);
                    padding: 2px 8px;
                    border-radius: 4px;
                    cursor: pointer;
                    transition: all 0.2s;
                    color: #38bdf8;
                }}
                .reset-btn:hover {{
                    background: #38bdf8;
                    color: #000;
                }}
                .legend-item {{
                    display: flex;
                    align-items: center;
                    margin: 5px 0;
                    padding: 6px 8px;
                    border-radius: 6px;
                    cursor: pointer;
                    transition: all 0.2s ease;
                    border: 1px solid transparent;
                }}
                .legend-item:hover {{
                    background: rgba(255, 255, 255, 0.15);
                    transform: translateX(-3px);
                    border-color: rgba(255,255,255,0.3);
                }}
                .legend-item.active-filter {{
                    background: rgba(56, 189, 248, 0.25);
                    border: 1px solid #38bdf8;
                }}
                .legend-item.inactive-filter {{
                    opacity: 0.35;
                    filter: grayscale(80%);
                }}
                .legend-color {{
                    width: 14px;
                    height: 14px;
                    border-radius: 50%;
                    margin-right: 8px;
                    flex-shrink: 0;
                }}
                .legend-label {{
                    flex-grow: 1;
                    font-weight: 600;
                    font-size: 12px;
                }}
                .count-badge {{
                    background: rgba(255,255,255,0.18);
                    padding: 2px 7px;
                    border-radius: 10px;
                    font-size: 11px;
                    font-weight: bold;
                }}
                .popup-card {{
                    position: absolute;
                    bottom: 20px;
                    left: 20px;
                    background: rgba(15, 23, 42, 0.95);
                    color: white;
                    padding: 14px 18px;
                    border-radius: 12px;
                    border: 1.5px solid rgba(56, 189, 248, 0.6);
                    box-shadow: 0 10px 40px rgba(0,0,0,0.7);
                    backdrop-filter: blur(15px);
                    z-index: 200;
                    min-width: 270px;
                    max-width: 320px;
                    transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
                }}
                .popup-card.hidden {{
                    opacity: 0;
                    pointer-events: none;
                    transform: translateY(20px) scale(0.95);
                }}
                .popup-header {{
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    font-weight: bold;
                    font-size: 14px;
                    border-bottom: 1px solid rgba(255,255,255,0.2);
                    padding-bottom: 8px;
                    margin-bottom: 10px;
                }}
                .popup-close {{
                    cursor: pointer;
                    font-size: 18px;
                    color: #94a3b8;
                    transition: color 0.2s;
                }}
                .popup-close:hover {{
                    color: #ff4d4d;
                }}
                .stat-row {{
                    display: flex;
                    justify-content: space-between;
                    margin: 6px 0;
                    font-size: 12px;
                }}
                .stat-label {{
                    color: #94a3b8;
                }}
                .stat-val {{
                    font-weight: 700;
                    color: #38bdf8;
                }}
            </style>
        </head>
        <body>
            <div class="wagon-container">
                <div class="wagon-title">{title}</div>
                <div id="{div_id}"></div>

                <!-- Clickable Small Tab Toggle Pill Button -->
                <div class="legend-tab-toggle" id="legend-toggle-btn-{unique_id}" title="Click to filter shot types">
                    <span id="tab-label-{unique_id}">🎯 SHOT TYPES</span>
                    <span class="tab-chevron" id="tab-chevron-{unique_id}">▼</span>
                </div>

                <!-- Small Tab Menu Panel (Pops open on click) -->
                <div class="legend-box collapsed" id="legend-box-{unique_id}">
                    <div class="legend-header">
                        <span>FILTER SHOTS</span>
                        <span class="reset-btn" id="reset-filter-btn-{unique_id}" title="Show All Shots">Show All</span>
                    </div>
                    <div class="legend-item" id="legend-red-{unique_id}" data-color="red" title="Click to filter & pop details">
                        <div class="legend-color" style="background: #ff4d4d; box-shadow: 0 0 8px rgba(255, 77, 77, 0.8);"></div>
                        <span class="legend-label">Boundaries (4s & 6s)</span>
                        <span class="count-badge" id="count-red-{unique_id}">0</span>
                    </div>
                    <div class="legend-item" id="legend-orange-{unique_id}" data-color="orange" title="Click to filter & pop details">
                        <div class="legend-color" style="background: #ff9800; box-shadow: 0 0 8px rgba(255, 152, 0, 0.8);"></div>
                        <span class="legend-label">Twos (2 runs)</span>
                        <span class="count-badge" id="count-orange-{unique_id}">0</span>
                    </div>
                    <div class="legend-item" id="legend-blue-{unique_id}" data-color="blue" title="Click to filter & pop details">
                        <div class="legend-color" style="background: #2196f3; box-shadow: 0 0 8px rgba(33, 150, 243, 0.8);"></div>
                        <span class="legend-label">Threes (3 runs)</span>
                        <span class="count-badge" id="count-blue-{unique_id}">0</span>
                    </div>
                    <div class="legend-item" id="legend-green-{unique_id}" data-color="green" title="Click to filter & pop details">
                        <div class="legend-color" style="background: #00e676; box-shadow: 0 0 8px rgba(0, 230, 118, 0.8);"></div>
                        <span class="legend-label">Singles (1 run)</span>
                        <span class="count-badge" id="count-green-{unique_id}">0</span>
                    </div>
                </div>

                <!-- Interactive Pop-Up Modal Card -->
                <div id="shot-popup-card-{unique_id}" class="popup-card hidden">
                    <div class="popup-header">
                        <span id="popup-title-{unique_id}">Shot Details</span>
                        <span class="popup-close" id="popup-close-btn-{unique_id}">&times;</span>
                    </div>
                    <div class="popup-body" id="popup-body-{unique_id}">
                        <!-- Content dynamically populated on click -->
                    </div>
                </div>
            </div>
            <script>
            (function() {{
                const wagonData = {data_json};
                const scene = new THREE.Scene();
                const uid = "{unique_id}";
                
                // Realistic sky gradient (Dark Telemetry Mode)
                const skyCanvas = document.createElement('canvas');
                skyCanvas.width = 512; skyCanvas.height = 512;
                const skyCtx = skyCanvas.getContext('2d');
                const skyGrad = skyCtx.createLinearGradient(0, 0, 0, 512);
                skyGrad.addColorStop(0, '#05070c');
                skyGrad.addColorStop(0.5, '#0b0f1a');
                skyGrad.addColorStop(1, '#1e293b');
                skyCtx.fillStyle = skyGrad;
                skyCtx.fillRect(0, 0, 512, 512);
                const skyTexture = new THREE.CanvasTexture(skyCanvas);
                scene.background = skyTexture;
                scene.fog = new THREE.Fog(0x0b0f1a, 80, 200);
                
                const camera = new THREE.PerspectiveCamera(50, {width}/{height}, 0.1, 500);
                camera.position.set(0, 85, 5);
                camera.lookAt(0, 0, 0);
                
                const renderer = new THREE.WebGLRenderer({{ antialias: true }});
                renderer.setSize({width}, {height});
                renderer.shadowMap.enabled = true;
                renderer.shadowMap.type = THREE.PCFShadowMap;
                renderer.toneMapping = THREE.ACESFilmicToneMapping;
                renderer.toneMappingExposure = 1.1;
                document.getElementById('{div_id}').appendChild(renderer.domElement);
                
                // Warm stadium lighting
                const ambientLight = new THREE.AmbientLight(0xfff5e6, 0.5);
                scene.add(ambientLight);
                const hemisphereLight = new THREE.HemisphereLight(0x87ceeb, 0x1a7a1a, 0.4);
                scene.add(hemisphereLight);
                
                const sunLight = new THREE.DirectionalLight(0xfffde6, 0.9);
                sunLight.position.set(50, 120, 50);
                sunLight.castShadow = true;
                sunLight.shadow.mapSize.width = 1024;
                sunLight.shadow.mapSize.height = 1024;
                sunLight.shadow.camera.left = -100;
                sunLight.shadow.camera.right = 100;
                sunLight.shadow.camera.top = 100;
                sunLight.shadow.camera.bottom = -100;
                scene.add(sunLight);
                
                const fillLight = new THREE.DirectionalLight(0xb0d4f1, 0.3);
                fillLight.position.set(-50, 80, -50);
                scene.add(fillLight);
                
                // Procedural grass with mowing stripes
                const grassCanvas = document.createElement('canvas');
                grassCanvas.width = 1024;
                grassCanvas.height = 1024;
                const grassCtx = grassCanvas.getContext('2d');
                
                for (let i = 0; i < 20; i++) {{
                    grassCtx.fillStyle = i % 2 === 0 ? '#157015' : '#1a7a1a';
                    grassCtx.fillRect(0, i * 51.2, 1024, 51.2);
                }}
                for (let i = 0; i < 8000; i++) {{
                    const x = Math.random() * 1024;
                    const y = Math.random() * 1024;
                    const brightness = 90 + Math.random() * 50;
                    grassCtx.fillStyle = `rgba(20, ${{brightness}}, 20, 0.6)`;
                    grassCtx.fillRect(x, y, 2, 2);
                }}
                
                const grassTexture = new THREE.CanvasTexture(grassCanvas);
                grassTexture.wrapS = THREE.RepeatWrapping;
                grassTexture.wrapT = THREE.RepeatWrapping;
                
                // Circular stadium ground
                const groundGeometry = new THREE.CircleGeometry({ground_radius}, 64);
                const groundMaterial = new THREE.MeshStandardMaterial({{ 
                    map: grassTexture,
                    roughness: 0.85,
                    metalness: 0.1
                }});
                const ground = new THREE.Mesh(groundGeometry, groundMaterial);
                ground.rotation.x = -Math.PI / 2;
                ground.receiveShadow = true;
                scene.add(ground);
                
                // 30-yard circle
                const innerCircleGeometry = new THREE.RingGeometry(27.43, 27.73, 64);
                const innerCircleMaterial = new THREE.MeshStandardMaterial({{ 
                    color: 0xffffff, roughness: 0.6, metalness: 0.2
                }});
                const innerCircle = new THREE.Mesh(innerCircleGeometry, innerCircleMaterial);
                innerCircle.rotation.x = -Math.PI / 2;
                innerCircle.position.y = 0.05;
                scene.add(innerCircle);
                
                // Boundary rope
                const boundaryGeometry = new THREE.RingGeometry({boundary_radius} - 0.5, {boundary_radius}, 64);
                const boundaryMaterial = new THREE.MeshStandardMaterial({{ 
                    color: 0xffffff, roughness: 0.4, metalness: 0.3
                }});
                const boundary = new THREE.Mesh(boundaryGeometry, boundaryMaterial);
                boundary.rotation.x = -Math.PI / 2;
                boundary.position.y = 0.1;
                scene.add(boundary);
                
                // Load realistic 3D Stadium Model
                const loader = new THREE.GLTFLoader();
                loader.load(
                    '/app/static/stadium.glb',
                    function (gltf) {{
                        const model = gltf.scene;
                        const box = new THREE.Box3().setFromObject(model);
                        const size = box.getSize(new THREE.Vector3());
                        const center = box.getCenter(new THREE.Vector3());
                        
                        model.position.x += (model.position.x - center.x);
                        model.position.y += (model.position.y - box.min.y) - 2;
                        model.position.z += (model.position.z - center.z);
                        
                        const maxDim = Math.max(size.x, size.z);
                        const scaleFactor = 250 / maxDim;
                        model.scale.set(scaleFactor, scaleFactor, scaleFactor);
                        
                        model.traverse(function (node) {{
                            if (node.isMesh) {{
                                node.castShadow = false;
                                node.receiveShadow = false;
                                if (node.material) {{
                                    node.material.roughness = 0.75;
                                    node.material.metalness = 0.15;
                                }}
                            }}
                        }});
                        
                        scene.add(model);
                        renderer.render(scene, camera);
                    }},
                    undefined,
                    function (error) {{
                        console.error('Error loading 3D stadium model:', error);
                    }}
                );
                
                // Create pitch
                const pitchCanvas = document.createElement('canvas');
                pitchCanvas.width = 256; pitchCanvas.height = 2048;
                const pitchCtx = pitchCanvas.getContext('2d');
                pitchCtx.fillStyle = '#c9a875';
                pitchCtx.fillRect(0, 0, 256, 2048);
                
                for (let i = 0; i < 10000; i++) {{
                    const x = Math.random() * 256;
                    const y = Math.random() * 2048;
                    const shade = 170 + Math.random() * 50;
                    pitchCtx.fillStyle = `rgb(${{shade}}, ${{shade * 0.75}}, ${{shade * 0.55}})`;
                    pitchCtx.fillRect(x, y, 1, 1);
                }}
                for (let i = 0; i < 8; i++) {{
                    const y = 900 + Math.random() * 300;
                    pitchCtx.fillStyle = 'rgba(150, 120, 85, 0.4)';
                    pitchCtx.fillRect(50 + Math.random() * 30, y, 120 + Math.random() * 40, 50);
                }}
                const pitchTexture = new THREE.CanvasTexture(pitchCanvas);
                const pitchGeometry = new THREE.PlaneGeometry(3.05, 20.12);
                const pitchMaterial = new THREE.MeshStandardMaterial({{ map: pitchTexture, roughness: 0.92, metalness: 0.08 }});
                const pitch = new THREE.Mesh(pitchGeometry, pitchMaterial);
                pitch.rotation.x = -Math.PI / 2; pitch.position.y = 0.15; pitch.receiveShadow = true;
                scene.add(pitch);
                
                const stumpGeometry = new THREE.CylinderGeometry(0.022, 0.022, 0.71, 8);
                const stumpMaterial = new THREE.MeshStandardMaterial({{ color: 0x8B4513, roughness: 0.4, metalness: 0.2 }});
                const batterEndZ = -10.06;
                const bowlerEndZ = 10.06;
                
                [-0.11, 0, 0.11].forEach(xPos => {{
                    const stump = new THREE.Mesh(stumpGeometry, stumpMaterial);
                    stump.position.set(xPos, 0.355, batterEndZ); scene.add(stump);
                    const s2 = new THREE.Mesh(stumpGeometry, stumpMaterial);
                    s2.position.set(xPos, 0.355, bowlerEndZ); scene.add(s2);
                }});
                
                // Color hex mapping & counts
                const colorHexMap = {{
                    'red': 0xff4d4d,     // Boundaries (4s & 6s)
                    'orange': 0xff9800,  // Twos
                    'blue': 0x2196f3,    // Threes
                    'green': 0x00e676    // Singles
                }};
                const categoryLabels = {{
                    'red': 'Boundaries (4s & 6s)',
                    'orange': 'Twos (2 runs)',
                    'blue': 'Threes (3 runs)',
                    'green': 'Singles (1 run)'
                }};
                
                const counts = {{ 'red': 0, 'orange': 0, 'blue': 0, 'green': 0 }};
                wagonData.forEach(shot => {{
                    const c = shot.color || 'green';
                    if (counts[c] !== undefined) counts[c]++;
                }});
                
                // Populate badge counts
                for (const key in counts) {{
                    const badgeEl = document.getElementById(`count-${{key}}-${{uid}}`);
                    if (badgeEl) badgeEl.innerText = counts[key];
                }}
                
                // Shot 3D objects tracking
                const shotObjects = [];
                const sharedBallGeometry = new THREE.SphereGeometry(1, 12, 12);
                const centerPoint = new THREE.Vector3(0, 0.4, batterEndZ);

                wagonData.forEach((shot, index) => {{
                    const radius = 0.25;
                    const cKey = shot.color || 'green';
                    const hexColor = colorHexMap[cKey] || 0x00e676;
                    
                    const ballMat = new THREE.MeshStandardMaterial({{ 
                        color: hexColor, roughness: 0.3, metalness: 0.7, emissive: hexColor, emissiveIntensity: 0.4 
                    }});
                    const lineMat = new THREE.LineBasicMaterial({{ 
                        color: hexColor, linewidth: 2, opacity: 0.65, transparent: true 
                    }});

                    const landingZ = batterEndZ + shot.y;
                    const apexHeight = shot.apex_y || (shot.runs === 6 ? 18.0 : (shot.runs === 4 ? 3.0 : 0.8));
                    const startPoint = new THREE.Vector3(0, 0.4, batterEndZ);
                    const endPoint = new THREE.Vector3(shot.x, radius + 0.2, landingZ);
                    const midPoint = new THREE.Vector3(shot.x * 0.5, apexHeight, batterEndZ + shot.y * 0.5);
                    const curve = new THREE.QuadraticBezierCurve3(startPoint, midPoint, endPoint);
                    const points = curve.getPoints(24);
                    
                    const lineGeometry = new THREE.BufferGeometry().setFromPoints(points);
                    const line = new THREE.Line(lineGeometry, lineMat);
                    scene.add(line);
                    
                    const ball = new THREE.Mesh(sharedBallGeometry, ballMat);
                    ball.scale.set(radius, radius, radius);
                    ball.position.set(shot.x, radius + 0.2, landingZ);
                    ball.castShadow = true;
                    ball.userData = {{ ...shot, index, cKey }};
                    scene.add(ball);
                    
                    shotObjects.push({{ line, ball, cKey, shot }});
                }});

                // Interactive Legend Filters & Pop-Up Card
                let activeFilterColor = null;
                const popupCard = document.getElementById(`shot-popup-card-${{uid}}`);
                const popupBody = document.getElementById(`popup-body-${{uid}}`);
                const popupTitle = document.getElementById(`popup-title-${{uid}}`);
                const popupCloseBtn = document.getElementById(`popup-close-btn-${{uid}}`);
                const resetBtn = document.getElementById(`reset-filter-btn-${{uid}}`);
                const legendToggleBtn = document.getElementById(`legend-toggle-btn-${{uid}}`);
                const legendBox = document.getElementById(`legend-box-${{uid}}`);
                const tabChevron = document.getElementById(`tab-chevron-${{uid}}`);
                const tabLabel = document.getElementById(`tab-label-${{uid}}`);
                
                if (legendToggleBtn && legendBox) {{
                    legendToggleBtn.addEventListener('click', (e) => {{
                        e.stopPropagation();
                        const isCollapsed = legendBox.classList.contains('collapsed');
                        if (isCollapsed) {{
                            legendBox.classList.remove('collapsed');
                            if (tabChevron) tabChevron.innerText = '▲';
                        }} else {{
                            legendBox.classList.add('collapsed');
                            if (tabChevron) tabChevron.innerText = '▼';
                        }}
                    }});
                }}
                
                if (popupCloseBtn) {{
                    popupCloseBtn.addEventListener('click', () => {{
                        popupCard.classList.add('hidden');
                    }});
                }}
                
                if (resetBtn) {{
                    resetBtn.addEventListener('click', () => {{
                        activeFilterColor = null;
                        if (tabLabel) tabLabel.innerText = '🎯 SHOT TYPES';
                        document.querySelectorAll(`.legend-item`).forEach(el => {{
                            el.classList.remove('active-filter', 'inactive-filter');
                        }});
                        shotObjects.forEach(obj => {{
                            obj.line.visible = true;
                            obj.ball.visible = true;
                            obj.line.material.opacity = 0.65;
                            obj.ball.material.opacity = 1.0;
                        }});
                        popupCard.classList.add('hidden');
                        if (legendBox) legendBox.classList.add('collapsed');
                        if (tabChevron) tabChevron.innerText = '▼';
                        renderer.render(scene, camera);
                    }});
                }}
                
                function popShotTypeDetails(colorKey) {{
                    const label = categoryLabels[colorKey] || colorKey;
                    const totalShots = wagonData.length;
                    const categoryShots = wagonData.filter(s => (s.color || 'green') === colorKey);
                    const cnt = categoryShots.length;
                    const pct = totalShots > 0 ? ((cnt / totalShots) * 100).toFixed(1) : 0;
                    
                    let totalRuns = 0;
                    let totalDist = 0;
                    const zoneCounts = {{}};
                    const batterCounts = {{}};
                    
                    categoryShots.forEach(s => {{
                        totalRuns += (s.runs || 0);
                        if (s.distance) totalDist += s.distance;
                        const z = s.zone || 'Outfield';
                        zoneCounts[z] = (zoneCounts[z] || 0) + 1;
                        const b = s.batter || 'Unknown';
                        batterCounts[b] = (batterCounts[b] || 0) + 1;
                    }});
                    
                    const avgDist = cnt > 0 && totalDist > 0 ? (totalDist / cnt).toFixed(1) + ' m' : '~65 m';
                    let topZone = 'None';
                    let maxZ = 0;
                    for (const z in zoneCounts) {{
                        if (zoneCounts[z] > maxZ) {{
                            maxZ = zoneCounts[z];
                            topZone = z;
                        }}
                    }}
                    
                    let topBatter = 'None';
                    let maxB = 0;
                    for (const b in batterCounts) {{
                        if (batterCounts[b] > maxB) {{
                            maxB = batterCounts[b];
                            topBatter = b;
                        }}
                    }}
                    
                    popupTitle.innerHTML = `🎯 ${{label}}`;
                    popupBody.innerHTML = `
                        <div class="stat-row"><span class="stat-label">Total Shots:</span><span class="stat-val">${{cnt}} (${{pct}}% of innings)</span></div>
                        <div class="stat-row"><span class="stat-label">Total Runs:</span><span class="stat-val">${{totalRuns}} runs</span></div>
                        <div class="stat-row"><span class="stat-label">Top Scoring Zone:</span><span class="stat-val">${{topZone}}</span></div>
                        <div class="stat-row"><span class="stat-label">Avg Hit Distance:</span><span class="stat-val">${{avgDist}}</span></div>
                        <div class="stat-row"><span class="stat-label">Top Scorer:</span><span class="stat-val">${{topBatter}} (${{maxB}} shots)</span></div>
                        <div style="margin-top:10px;font-size:11px;color:#38bdf8;text-align:center;font-style:italic">⚡ Filter Active: Displaying ${{label}} only</div>
                    `;
                    popupCard.classList.remove('hidden');
                }}
                
                ['red', 'orange', 'blue', 'green'].forEach(colorKey => {{
                    const el = document.getElementById(`legend-${{colorKey}}-${{uid}}`);
                    if (!el) return;
                    el.addEventListener('click', () => {{
                        if (activeFilterColor === colorKey) {{
                            // Toggle off filter
                            activeFilterColor = null;
                            if (tabLabel) tabLabel.innerText = '🎯 SHOT TYPES';
                            ['red', 'orange', 'blue', 'green'].forEach(ck => {{
                                const item = document.getElementById(`legend-${{ck}}-${{uid}}`);
                                if (item) item.classList.remove('active-filter', 'inactive-filter');
                            }});
                            shotObjects.forEach(obj => {{
                                obj.line.visible = true;
                                obj.ball.visible = true;
                                obj.line.material.opacity = 0.65;
                            }});
                            popupCard.classList.add('hidden');
                        }} else {{
                            // Toggle on filter
                            activeFilterColor = colorKey;
                            if (tabLabel) tabLabel.innerText = `🎯 ${{categoryLabels[colorKey]}}`;
                            ['red', 'orange', 'blue', 'green'].forEach(ck => {{
                                const item = document.getElementById(`legend-${{ck}}-${{uid}}`);
                                if (item) {{
                                    if (ck === colorKey) {{
                                        item.classList.add('active-filter');
                                        item.classList.remove('inactive-filter');
                                    }} else {{
                                        item.classList.add('inactive-filter');
                                        item.classList.remove('active-filter');
                                    }}
                                }}
                            }});
                            shotObjects.forEach(obj => {{
                                const match = obj.cKey === colorKey;
                                obj.line.visible = match;
                                obj.ball.visible = match;
                                obj.line.material.opacity = match ? 0.9 : 0.1;
                            }});
                            popShotTypeDetails(colorKey);
                        }}
                        if (legendBox) legendBox.classList.add('collapsed');
                        if (tabChevron) tabChevron.innerText = '▼';
                        renderer.render(scene, camera);
                    }});
                }});
                
                // Raycasting on 3D Ball Click
                const raycaster = new THREE.Raycaster();
                const mouse = new THREE.Vector2();
                
                renderer.domElement.addEventListener('click', (event) => {{
                    const rect = renderer.domElement.getBoundingClientRect();
                    mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
                    mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
                    
                    raycaster.setFromCamera(mouse, camera);
                    const ballMeshes = shotObjects.map(o => o.ball);
                    const intersects = raycaster.intersectObjects(ballMeshes);
                    
                    if (intersects.length > 0) {{
                        const clickedBall = intersects[0].object;
                        const data = clickedBall.userData;
                        
                        const shotDist = (data.distance !== undefined && data.distance !== null && data.distance > 0) 
                            ? data.distance + ' m' 
                            : (Math.sqrt((data.x||0)*(data.x||0) + (data.y||0)*(data.y||0))).toFixed(1) + ' m';
                        const ballSpd = (data.ball_speed !== undefined && data.ball_speed !== null && data.ball_speed > 0)
                            ? data.ball_speed + ' km/h'
                            : '138.5 km/h';

                        popupTitle.innerHTML = `🏏 Shot Detail: ${{data.runs}} Runs`;
                        popupBody.innerHTML = `
                            <div class="stat-row"><span class="stat-label">Batter:</span><span class="stat-val">${{data.batter || 'Batter'}}</span></div>
                            <div class="stat-row"><span class="stat-label">Bowler:</span><span class="stat-val">${{data.bowler || 'Bowler'}}</span></div>
                            <div class="stat-row"><span class="stat-label">Runs Scored:</span><span class="stat-val">${{data.runs}} Runs</span></div>
                            <div class="stat-row"><span class="stat-label">Scoring Zone:</span><span class="stat-val">${{data.zone || 'Outfield'}}</span></div>
                            <div class="stat-row"><span class="stat-label">3D Apex Height:</span><span class="stat-val">${{data.apex_y ? data.apex_y + ' m' : (data.runs === 6 ? '18.5 m' : '3.0 m')}}</span></div>
                            <div class="stat-row"><span class="stat-label">Shot Distance:</span><span class="stat-val">${{shotDist}}</span></div>
                            <div class="stat-row"><span class="stat-label">Ball Speed:</span><span class="stat-val">${{ballSpd}}</span></div>
                        `;
                        popupCard.classList.remove('hidden');
                    }}
                }});
                
                // OrbitControls setup
                const controls = new THREE.OrbitControls(camera, renderer.domElement);
                controls.enableDamping = true;
                controls.dampingFactor = 0.05;
                controls.minDistance = 25;
                controls.maxDistance = 150;
                controls.maxPolarAngle = Math.PI / 2.1;
                controls.target.set(0, 0, 0);
                
                controls.addEventListener('change', () => renderer.render(scene, camera));
                renderer.render(scene, camera);
            }})();
            </script>
        </body>
        </html>
        """
        return html

    def create_polar_sector_radar_chart(wagon_data, title, team_name):
        """Create a broadcast-quality 360° Polar Rose Sector Chart for Wagon Wheel analysis."""
        if not wagon_data:
            return None
        import plotly.graph_objects as go
        
        # 8 Standard Cricket Sectors mapped to natural cricket field angles (0° = Straight/Long-Off)
        sector_defs = [
            {'label': 'Straight (Long-On / Off)', 'angle': 90, 'keywords': ['Straight', 'Long-On', 'Long-Off']},
            {'label': 'Cover & Extra Cover', 'angle': 45, 'keywords': ['Cover', 'Extra Cover']},
            {'label': 'Point & Backward Point', 'angle': 0, 'keywords': ['Point']},
            {'label': 'Third Man', 'angle': 315, 'keywords': ['Third Man']},
            {'label': 'Fine Leg', 'angle': 270, 'keywords': ['Fine Leg']},
            {'label': 'Square Leg', 'angle': 225, 'keywords': ['Square Leg']},
            {'label': 'Mid-Wicket (Cow Corner)', 'angle': 180, 'keywords': ['Mid-Wicket', 'Cow Corner']},
            {'label': 'Mid-On / Mid-Off', 'angle': 135, 'keywords': ['Mid-On', 'Mid-Off']}
        ]
        
        sector_runs = [0] * 8
        sector_boundaries = [0] * 8
        sector_shots = [0] * 8
        
        for shot in wagon_data:
            z = shot.get('zone', '')
            r = shot.get('runs', 0)
            
            matched = False
            for idx, sdef in enumerate(sector_defs):
                if any(kw.lower() in z.lower() for kw in sdef['keywords']):
                    sector_runs[idx] += r
                    sector_shots[idx] += 1
                    if r >= 4:
                        sector_boundaries[idx] += 1
                    matched = True
                    break
            if not matched:
                sector_runs[0] += r
                sector_shots[0] += 1
                if r >= 4:
                    sector_boundaries[0] += 1
                    
        total_runs = sum(sector_runs)
        if total_runs == 0:
            total_runs = 1
            
        percentages = [(r / total_runs) * 100 for r in sector_runs]
        
        # Vibrant color palette based on run intensity
        colors = []
        for pct in percentages:
            if pct >= 20.0:
                colors.append('rgba(239, 68, 68, 0.90)')  # Vibrant Neon Red/Pink for Hot Zones
            elif pct >= 12.0:
                colors.append('rgba(245, 158, 11, 0.88)') # Amber Orange
            elif pct >= 6.0:
                colors.append('rgba(56, 189, 248, 0.85)') # Bright Cyan
            else:
                colors.append('rgba(51, 65, 85, 0.65)')   # Slate Gray
                
        labels = [s['label'] for s in sector_defs]
        angles = [s['angle'] for s in sector_defs]
        
        hover_texts = []
        for i in range(8):
            txt = (
                f"<b>🎯 {labels[i]}</b><br>"
                f"Total Runs: <b>{sector_runs[i]} runs</b> ({percentages[i]:.1f}% share)<br>"
                f"Shots Hit: {sector_shots[i]}<br>"
                f"Boundaries (4s & 6s): {sector_boundaries[i]}"
            )
            hover_texts.append(txt)
            
        fig = go.Figure()
        
        # Primary Sector Rose Wedges (Total Runs)
        fig.add_trace(go.Barpolar(
            r=sector_runs,
            theta=angles,
            width=[40] * 8,
            marker_color=colors,
            marker_line_color='#ffffff',
            marker_line_width=1.5,
            opacity=0.9,
            hoverinfo='text',
            text=hover_texts,
            name='Total Runs'
        ))
        
        fig.update_layout(
            dragmode=False,
            polar=dict(
                bgcolor='rgba(15, 23, 42, 0.85)',
                radialaxis=dict(
                    visible=True,
                    showticklabels=True,
                    ticksuffix=' r',
                    gridcolor='rgba(255, 255, 255, 0.15)',
                    linecolor='rgba(255, 255, 255, 0.2)',
                    tickfont=dict(color='#94a3b8', size=10)
                ),
                angularaxis=dict(
                    tickmode='array',
                    tickvals=angles,
                    ticktext=labels,
                    direction='clockwise',
                    gridcolor='rgba(255, 255, 255, 0.15)',
                    linecolor='rgba(255, 255, 255, 0.3)',
                    tickfont=dict(color='#f8fafc', size=11, family='Segoe UI, sans-serif')
                )
            ),
            showlegend=False,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=60, r=60, t=50, b=50),
            height=420,
            title=dict(
                text=f"🌀 360° Sector Run Distribution Rose — {title}",
                font=dict(size=14, color='#38bdf8', family='Segoe UI, sans-serif')
            )
        )
        return fig
    
    def render_bowling_length_map(df, team, phase=None, bowler_type=None, unique_id="", pitch_data_override=None, title=None):
        """Render 3D bowling length visualization with zones and percentages.
        Uses pitch_data_override (from real Hawk-Eye coordinates) when provided,
        otherwise falls back to synthetic position generation."""
        if not title:
            bt_str = f" ({bowler_type})" if bowler_type else ""
            phase_str = f" - {phase}" if phase else ""
            title = f"🎳 3D Pitch Length Map — {team}{bt_str}{phase_str}"
            
        if pitch_data_override:
            pitch_data = pitch_data_override
        else:
            pitch_data = generate_pitch_map_data_complete(df, team=team, phase=phase, bowler_type=bowler_type)
        
        if not pitch_data:
            return "<p>No data available for bowling length map</p>"
        
        div_id = f"bowling_length_{unique_id}"
        data_json = json.dumps(pitch_data)
        
        title_parts = [f"{team} - Bowling Length Analysis"]
        if phase:
            title_parts.append(f"({phase})")
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
            <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
            <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@500;700;900&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
            <style>
                body {{ 
                    margin: 0; 
                    padding: 0; 
                    font-family: 'Inter', sans-serif;
                    background: #0b0f1a;
                    color: #e2e8f0;
                    overflow: hidden;
                }}
                .bowling-container {{ 
                    position: relative; 
                    text-align: center;
                    background: transparent;
                    padding: 0;
                    border-radius: 0;
                }}
                .bowling-title {{ 
                    text-align: center; 
                    font-size: 16px; 
                    font-weight: 800; 
                    padding: 12px;
                    margin-bottom: 0;
                    color: #ffffff;
                    text-transform: uppercase;
                    letter-spacing: 2px;
                    font-family: 'Orbitron', sans-serif;
                    background: linear-gradient(135deg, #38bdf8, #818cf8);
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                }}
                #{div_id} {{ 
                    border: 1px solid rgba(255,255,255,0.08); 
                    border-radius: 12px; 
                    display: inline-block;
                    box-shadow: 0 12px 40px rgba(0,0,0,0.6);
                    background: #05070c;
                }}
                .stats-overlay {{
                    position: absolute;
                    top: 60px;
                    right: 20px;
                    background: rgba(11, 15, 26, 0.9);
                    backdrop-filter: blur(12px);
                    -webkit-backdrop-filter: blur(12px);
                    padding: 15px;
                    border-radius: 12px;
                    color: #f8fafc;
                    font-size: 12px;
                    min-width: 190px;
                    border: 1px solid rgba(56, 189, 248, 0.25);
                    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
                    display: none;
                    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
                }}
                .stats-overlay.show {{
                    display: block;
                    animation: slideIn 0.25s ease-out;
                }}
                @keyframes slideIn {{
                    from {{
                        opacity: 0;
                        transform: scale(0.95) translateX(15px);
                    }}
                    to {{
                        opacity: 1;
                        transform: scale(1) translateX(0);
                    }}
                }}
                .toggle-stats-btn, .toggle-views-btn, .view-btn {{
                    border: none;
                    color: white;
                    padding: 8px 14px;
                    border-radius: 8px;
                    cursor: pointer;
                    font-weight: 600;
                    font-size: 11px;
                    font-family: 'Inter', sans-serif;
                    transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
                    z-index: 100;
                }}
                .toggle-stats-btn {{
                    position: absolute;
                    top: 15px;
                    right: 20px;
                    background: rgba(56, 189, 248, 0.15);
                    border: 1px solid rgba(56, 189, 248, 0.3);
                    box-shadow: 0 4px 15px rgba(56, 189, 248, 0.1);
                }}
                .toggle-stats-btn:hover {{
                    background: rgba(56, 189, 248, 0.35);
                    transform: translateY(-2px);
                    box-shadow: 0 6px 20px rgba(56, 189, 248, 0.2);
                }}
                .toggle-views-btn {{
                    position: absolute;
                    top: 15px;
                    left: 20px;
                    background: rgba(129, 140, 248, 0.15);
                    border: 1px solid rgba(129, 140, 248, 0.3);
                    box-shadow: 0 4px 15px rgba(129, 140, 248, 0.1);
                }}
                .toggle-views-btn:hover {{
                    background: rgba(129, 140, 248, 0.35);
                    transform: translateY(-2px);
                    box-shadow: 0 6px 20px rgba(129, 140, 248, 0.2);
                }}
                .zone-stat {{
                    margin: 6px 0;
                    padding: 8px 10px;
                    background: rgba(255,255,255,0.03);
                    border-radius: 6px;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    border-left: 3.5px solid;
                    border-top: 1px solid rgba(255,255,255,0.02);
                }}
                .zone-name {{
                    font-weight: 700;
                    text-transform: uppercase;
                    font-size: 9px;
                    letter-spacing: 1px;
                }}
                .zone-percentage {{
                    font-size: 18px;
                    font-weight: 800;
                    font-family: 'Orbitron', sans-serif;
                }}
                .short {{ color: #ef4444; border-color: #ef4444; }}
                .length {{ color: #f59e0b; border-color: #f59e0b; }}
                .full {{ color: #10b981; border-color: #10b981; }}
                .yorker {{ color: #38bdf8; border-color: #38bdf8; }}
                .legend-title {{
                    font-weight: 700;
                    margin-bottom: 10px;
                    font-size: 11px;
                    border-bottom: 1px solid rgba(255,255,255,0.1);
                    padding-bottom: 8px;
                    text-transform: uppercase;
                    letter-spacing: 1.5px;
                    color: #94a3b8;
                }}
                .view-controls {{
                    position: absolute;
                    top: 60px;
                    left: 20px;
                    background: rgba(11, 15, 26, 0.9);
                    padding: 12px;
                    border-radius: 12px;
                    color: white;
                    font-size: 11px;
                    border: 1px solid rgba(129, 140, 248, 0.25);
                    backdrop-filter: blur(12px);
                    display: none;
                    z-index: 10;
                    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
                    min-width: 110px;
                }}
                .view-controls.show {{
                    display: block;
                    animation: slideInLeft 0.25s ease-out;
                }}
                @keyframes slideInLeft {{
                    from {{
                        opacity: 0;
                        transform: scale(0.95) translateX(-15px);
                    }}
                    to {{
                        opacity: 1;
                        transform: scale(1) translateX(0);
                    }}
                }}
                .view-btn {{
                    background: rgba(255, 255, 255, 0.06);
                    border: 1px solid rgba(255, 255, 255, 0.12);
                    margin: 4px 0;
                    width: 100%;
                    box-shadow: none;
                }}
                .view-btn:hover {{
                    background: rgba(255, 255, 255, 0.18);
                    transform: translateY(-2px);
                    box-shadow: 0 4px 12px rgba(255,255,255,0.05);
                }}
                .controls-title {{
                    font-weight: 700;
                    margin-bottom: 8px;
                    font-size: 10px;
                    border-bottom: 1px solid rgba(255,255,255,0.1);
                    padding-bottom: 6px;
                    text-transform: uppercase;
                    letter-spacing: 1.5px;
                    color: #94a3b8;
                    text-align: center;
                }}
            </style>
        </head>
        <body>
            <div class="bowling-container">
                <div class="bowling-title">{title}</div>
                <div id="{div_id}"></div>
                <button class="toggle-views-btn" onclick="toggleViews_{unique_id}()">📐 Views</button>
                <button class="toggle-stats-btn" onclick="toggleStats_{unique_id}()">📊 Statistics</button>
                <div class="view-controls" id="view-controls-{unique_id}">
                    <div class="controls-title">📐 VIEWS</div>
                    <button class="view-btn" onclick="setTopView_{unique_id}()">📍 Top</button>
                    <button class="view-btn" onclick="setBowlerView_{unique_id}()">🎯 Bowler</button>
                    <button class="view-btn" onclick="setBatterView_{unique_id}()">🏏 Batter</button>
                    <button class="view-btn" onclick="setSideView_{unique_id}()">👁️ Side</button>
                    <button class="view-btn" onclick="resetView_{unique_id}()">🔄 Reset</button>
                </div>
                <div class="stats-overlay" id="stats-overlay-{unique_id}">
                    <div class="legend-title">📊 Bowling Length %</div>
                    <div id="zone-stats-{unique_id}"></div>
                </div>
            </div>
            
            <script>
            (function() {{
                const pitchData = {data_json};
                
                // Scene setup
                const scene = new THREE.Scene();
                // Dark telemetric/stadium background
                scene.background = new THREE.Color(0x0a0c14);
                scene.fog = new THREE.Fog(0x0a0c14, 100, 250);
                
                // Camera setup
                const camera = new THREE.PerspectiveCamera(45, 900/700, 0.1, 500);
                camera.position.set(0, 20, 30);
                camera.lookAt(0, 0, 11);
                
                // Renderer setup
                const renderer = new THREE.WebGLRenderer({{ antialias: true }});
                renderer.setSize(900, 700);
                renderer.shadowMap.enabled = true;
                renderer.shadowMap.type = THREE.PCFSoftShadowMap;
                document.getElementById('{div_id}').appendChild(renderer.domElement);
                
                // Controls
                const controls = new THREE.OrbitControls(camera, renderer.domElement);
                controls.enableDamping = true;
                controls.dampingFactor = 0.08;
                controls.target.set(0, 0, 11);
                controls.minDistance = 8;
                controls.maxDistance = 65;
                controls.maxPolarAngle = Math.PI / 2.05;
                
                // High-fidelity Lighting (Stadium floodlight system)
                const ambientLight = new THREE.AmbientLight(0xffffff, 0.45);
                scene.add(ambientLight);
                
                const keyLight1 = new THREE.SpotLight(0xffffff, 1.2, 180, Math.PI/4, 0.4, 1);
                keyLight1.position.set(30, 45, 11);
                keyLight1.target.position.set(0, 0, 11);
                keyLight1.castShadow = true;
                keyLight1.shadow.mapSize.width = 1024;
                keyLight1.shadow.mapSize.height = 1024;
                scene.add(keyLight1);
                
                const keyLight2 = new THREE.SpotLight(0xffffff, 1.2, 180, Math.PI/4, 0.4, 1);
                keyLight2.position.set(-30, 45, 11);
                keyLight2.target.position.set(0, 0, 11);
                keyLight2.castShadow = true;
                scene.add(keyLight2);
                
                const keyLight3 = new THREE.SpotLight(0xfff3e0, 0.8, 150, Math.PI/3, 0.5, 1);
                keyLight3.position.set(0, 40, -25);
                keyLight3.target.position.set(0, 0, 11);
                scene.add(keyLight3);
                
                const keyLight4 = new THREE.SpotLight(0xe8eaf6, 0.8, 150, Math.PI/3, 0.5, 1);
                keyLight4.position.set(0, 40, 47);
                keyLight4.target.position.set(0, 0, 11);
                scene.add(keyLight4);
                
                // --- PROCEDURAL STADIUM ---
                const groundRadius = 75;
                
                // Stadium ground
                const groundGeometry = new THREE.CircleGeometry(groundRadius, 64);
                const groundMaterial = new THREE.MeshStandardMaterial({{ 
                    color: 0x07150a, // Very dark turf base
                    roughness: 0.95
                }});
                const ground = new THREE.Mesh(groundGeometry, groundMaterial);
                ground.rotation.x = -Math.PI / 2;
                ground.position.set(0, -0.05, 11);
                ground.receiveShadow = true;
                scene.add(ground);
                
                // Boundary rope (white)
                const boundaryGeo = new THREE.TorusGeometry(groundRadius - 1.5, 0.3, 8, 48);
                const boundaryMat = new THREE.MeshStandardMaterial({{ color: 0xffffff, roughness: 0.8 }});
                const boundary = new THREE.Mesh(boundaryGeo, boundaryMat);
                boundary.rotation.x = Math.PI / 2;
                boundary.position.set(0, 0.05, 11);
                scene.add(boundary);
                
                // Stadium stands (Tier 1 - Darker blue/grey)
                const standsMat = new THREE.MeshStandardMaterial({{ color: 0x0f172a, roughness: 0.9 }});
                const tier1Geo = new THREE.TorusGeometry(groundRadius + 6, 10, 8, 36);
                const tier1 = new THREE.Mesh(tier1Geo, standsMat);
                tier1.rotation.x = Math.PI / 2;
                tier1.position.set(0, 1.5, 11);
                scene.add(tier1);
                
                // Stadium stands (Tier 2)
                const tier2Mat = new THREE.MeshStandardMaterial({{ color: 0x1e293b, roughness: 0.95 }});
                const tier2Geo = new THREE.TorusGeometry(groundRadius + 18, 14, 8, 36);
                const tier2 = new THREE.Mesh(tier2Geo, tier2Mat);
                tier2.rotation.x = Math.PI / 2;
                tier2.position.set(0, 8, 11);
                scene.add(tier2);
                
                // Floodlight poles
                const poleGeo = new THREE.CylinderGeometry(0.4, 0.8, 35, 8);
                const poleMat = new THREE.MeshStandardMaterial({{ color: 0x475569, metalness: 0.8, roughness: 0.3 }});
                const lightAngles = [Math.PI/4, 3*Math.PI/4, 5*Math.PI/4, 7*Math.PI/4];
                
                lightAngles.forEach(angle => {{
                    const px = Math.cos(angle) * (groundRadius + 20);
                    const pz = Math.sin(angle) * (groundRadius + 20) + 11;
                    
                    const pole = new THREE.Mesh(poleGeo, poleMat);
                    pole.position.set(px, 17.5, pz);
                    scene.add(pole);
                    
                    // Light Panel
                    const panelGeo = new THREE.BoxGeometry(7, 3, 0.8);
                    const panelMat = new THREE.MeshStandardMaterial({{ color: 0x334155, emissive: 0xffffff, emissiveIntensity: 1.5 }});
                    const panel = new THREE.Mesh(panelGeo, panelMat);
                    panel.position.set(px, 35, pz);
                    panel.lookAt(0, 10, 11);
                    scene.add(panel);
                }});
                
                // Create grass texture canvas (dark stadium turf)
                const grassCanvas = document.createElement('canvas');
                grassCanvas.width = 512;
                grassCanvas.height = 512;
                const grassCtx = grassCanvas.getContext('2d');
                
                // Base turf green
                grassCtx.fillStyle = '#0c2211';
                grassCtx.fillRect(0, 0, 512, 512);
                
                // Grass blades detailing
                for (let i = 0; i < 400; i++) {{
                    const shade = Math.random() * 20 - 10;
                    grassCtx.fillStyle = `rgb(${{12 + shade}},${{34 + shade * 1.3}},${{17 + shade}})`;
                    grassCtx.fillRect(Math.random() * 512, Math.random() * 512, 2, 2);
                }}
                
                // Mowing pattern stripes (Subtle)
                grassCtx.globalAlpha = 0.08;
                for (let i = 0; i < 16; i++) {{
                    grassCtx.fillStyle = i % 2 === 0 ? '#000000' : '#ffffff';
                    const stripeWidth = 512 / 16;
                    grassCtx.fillRect(i * stripeWidth, 0, stripeWidth, 512);
                }}
                grassCtx.globalAlpha = 1.0;
                
                const grassTexture = new THREE.CanvasTexture(grassCanvas);
                grassTexture.wrapS = THREE.RepeatWrapping;
                grassTexture.wrapT = THREE.RepeatWrapping;
                grassTexture.repeat.set(8, 8);
                ground.material.map = grassTexture;
                ground.material.needsUpdate = true;
                
                // 30-yard inner circle line
                const innerCircleGeometry = new THREE.RingGeometry(27, 27.25, 64);
                const innerCircleMaterial = new THREE.MeshBasicMaterial({{ 
                    color: 0xffffff,
                    transparent: true,
                    opacity: 0.25,
                    side: THREE.DoubleSide
                }});
                const innerCircle = new THREE.Mesh(innerCircleGeometry, innerCircleMaterial);
                innerCircle.rotation.x = -Math.PI / 2;
                innerCircle.position.set(0, 0.01, 11);
                scene.add(innerCircle);
                
                // Cricket pitch (clay brown)
                const pitchGeometry = new THREE.PlaneGeometry(2.7, 22.5);
                const pitchCanvas = document.createElement('canvas');
                pitchCanvas.width = 256;
                pitchCanvas.height = 2048;
                const pitchCtx = pitchCanvas.getContext('2d');
                
                // Base clay brown
                pitchCtx.fillStyle = '#bfa581';
                pitchCtx.fillRect(0, 0, 256, 2048);
                
                // Clay worn patch texturing
                for (let i = 0; i < 6000; i++) {{
                    const shade = Math.random() * 30 - 15;
                    pitchCtx.fillStyle = `rgb(${{191 + shade}},${{165 + shade}},${{129 + shade}})`;
                    pitchCtx.fillRect(Math.random() * 256, Math.random() * 2048, 2, 2);
                }}
                
                // Side grass blending (Fades grass onto the sides of the pitch)
                const grad = pitchCtx.createLinearGradient(0, 0, 256, 0);
                grad.addColorStop(0, 'rgba(12, 34, 17, 0.5)');
                grad.addColorStop(0.1, 'rgba(12, 34, 17, 0.1)');
                grad.addColorStop(0.5, 'rgba(0,0,0,0)');
                grad.addColorStop(0.9, 'rgba(12, 34, 17, 0.1)');
                grad.addColorStop(1, 'rgba(12, 34, 17, 0.5)');
                pitchCtx.fillStyle = grad;
                pitchCtx.fillRect(0, 0, 256, 2048);
                
                // Worn rough patches where balls drop
                pitchCtx.fillStyle = 'rgba(141, 115, 85, 0.2)';
                for (let i = 0; i < 20; i++) {{
                    const rx = 30 + Math.random() * 196;
                    const ry = 200 + Math.random() * 1648;
                    pitchCtx.beginPath();
                    pitchCtx.arc(rx, ry, 15 + Math.random() * 15, 0, Math.PI * 2);
                    pitchCtx.fill();
                }}
                
                const pitchTexture = new THREE.CanvasTexture(pitchCanvas);
                const pitchMaterial = new THREE.MeshStandardMaterial({{ 
                    map: pitchTexture,
                    roughness: 0.88,
                    metalness: 0.05
                }});
                const pitch = new THREE.Mesh(pitchGeometry, pitchMaterial);
                ground.receiveShadow = true;
                pitch.rotation.x = -Math.PI / 2;
                pitch.position.set(0, 0.02, 11);
                pitch.receiveShadow = true;
                scene.add(pitch);
                
                // White Crease Lines
                const creaseMaterial = new THREE.MeshBasicMaterial({{ 
                    color: 0xffffff,
                    transparent: true,
                    opacity: 0.85
                }});
                
                // Creases
                const creaseGeometry = new THREE.PlaneGeometry(2.8, 0.06);
                const crease1 = new THREE.Mesh(creaseGeometry, creaseMaterial);
                crease1.rotation.x = -Math.PI / 2;
                crease1.position.set(0, 0.03, 0);
                scene.add(crease1);
                
                const crease2 = new THREE.Mesh(creaseGeometry, creaseMaterial);
                crease2.rotation.x = -Math.PI / 2;
                crease2.position.set(0, 0.03, 22);
                scene.add(crease2);
                
                // Popping creases (1.22m in front of stumps)
                const popCreaseGeo = new THREE.PlaneGeometry(2.8, 0.05);
                const popCrease1 = new THREE.Mesh(popCreaseGeo, creaseMaterial);
                popCrease1.rotation.x = -Math.PI / 2;
                popCrease1.position.set(0, 0.03, 1.22);
                scene.add(popCrease1);
                
                const popCrease2 = new THREE.Mesh(popCreaseGeo, creaseMaterial);
                popCrease2.rotation.x = -Math.PI / 2;
                popCrease2.position.set(0, 0.03, 20.78);
                scene.add(popCrease2);
                
                // Return Creases
                const returnCreaseGeo = new THREE.PlaneGeometry(0.05, 2.44);
                for (let x of [-1.32, 1.32]) {{
                    const ret1 = new THREE.Mesh(returnCreaseGeo, creaseMaterial);
                    ret1.rotation.x = -Math.PI / 2;
                    ret1.position.set(x, 0.03, 0);
                    scene.add(ret1);
                    
                    const ret2 = new THREE.Mesh(returnCreaseGeo, creaseMaterial);
                    ret2.rotation.x = -Math.PI / 2;
                    ret2.position.set(x, 0.03, 22);
                    scene.add(ret2);
                }}
                
                // Stumps
                const stumpMaterial = new THREE.MeshStandardMaterial({{ 
                    color: 0xe5a93c, // Rich wooden color
                    roughness: 0.45,
                    metalness: 0.1
                }});
                
                const stumpPositions = [-0.115, 0, 0.115];
                stumpPositions.forEach(x => {{
                    // Bowler end stumps
                    const stump1 = new THREE.Mesh(
                        new THREE.CylinderGeometry(0.019, 0.019, 0.71, 12),
                        stumpMaterial
                    );
                    stump1.position.set(x, 0.355, 0);
                    stump1.castShadow = true;
                    scene.add(stump1);
                    
                    // Batter end stumps
                    const stump2 = new THREE.Mesh(
                        new THREE.CylinderGeometry(0.019, 0.019, 0.71, 12),
                        stumpMaterial
                    );
                    stump2.position.set(x, 0.355, 22);
                    stump2.castShadow = true;
                    scene.add(stump2);
                }});
                
                // Bails
                const bailMaterial = new THREE.MeshStandardMaterial({{ 
                    color: 0xbf851f, 
                    roughness: 0.4
                }});
                for (let i = 0; i < 2; i++) {{
                    const bx = i === 0 ? -0.0575 : 0.0575;
                    const bail1 = new THREE.Mesh(new THREE.CylinderGeometry(0.01, 0.01, 0.11, 8), bailMaterial);
                    bail1.rotation.z = Math.PI/2;
                    bail1.position.set(bx, 0.72, 0);
                    scene.add(bail1);
                    
                    const bail2 = new THREE.Mesh(new THREE.CylinderGeometry(0.01, 0.01, 0.11, 8), bailMaterial);
                    bail2.rotation.z = Math.PI/2;
                    bail2.position.set(bx, 0.72, 22);
                    scene.add(bail2);
                }}
                
                // Flat Translucent Pitch Zone Overlays
                const zones = [
                    {{ name: 'YORKER', start: 0, end: 2, color: 0x38bdf8, label: 'YORKER (0-2m)' }},
                    {{ name: 'FULL', start: 2, end: 6, color: 0x10b981, label: 'FULL (2-6m)' }},
                    {{ name: 'LENGTH', start: 6, end: 12, color: 0xf59e0b, label: 'GOOD LENGTH (6-12m)' }},
                    {{ name: 'SHORT', start: 12, end: 22, color: 0xef4444, label: 'SHORT / BOUNCER (12-22m)' }}
                ];
                
                zones.forEach(zone => {{
                    const zoneLength = zone.end - zone.start;
                    const zoneGeometry = new THREE.PlaneGeometry(2.65, zoneLength);
                    const zoneMaterial = new THREE.MeshBasicMaterial({{ 
                        color: zone.color,
                        transparent: true,
                        opacity: 0.14,
                        side: THREE.DoubleSide
                    }});
                    const zoneMesh = new THREE.Mesh(zoneGeometry, zoneMaterial);
                    zoneMesh.rotation.x = -Math.PI / 2;
                    zoneMesh.position.set(0, 0.03, zone.start + zoneLength/2);
                    scene.add(zoneMesh);
                }});
                
                // Procedural high-fidelity ball textures (Colored with white seams)
                function createProceduralBallTexture(colorHex) {{
                    const canvas = document.createElement('canvas');
                    canvas.width = 64;
                    canvas.height = 32;
                    const ctx = canvas.getContext('2d');
                    
                    // Base leather color
                    ctx.fillStyle = colorHex;
                    ctx.fillRect(0, 0, 64, 32);
                    
                    // White Seam
                    ctx.fillStyle = '#ffffff';
                    ctx.fillRect(31, 0, 2, 32);
                    
                    // Seam Stitches
                    ctx.fillStyle = 'rgba(255, 255, 255, 0.4)';
                    for (let y = 0; y < 32; y += 4) {{
                        ctx.fillRect(29, y, 1, 1);
                        ctx.fillRect(34, y, 1, 1);
                    }}
                    
                    const texture = new THREE.CanvasTexture(canvas);
                    return texture;
                }}
                
                const colorMap = {{ 
                    'red': '#ef4444', 
                    'purple': '#a855f7', 
                    'green': '#10b981', 
                    'blue': '#38bdf8', 
                    'gray': '#64748b' 
                }};
                
                const sharedBallGeometry = new THREE.SphereGeometry(1, 16, 16);
                const ballMaterials = {{}};
                for (const [key, colorHex] of Object.entries(colorMap)) {{
                    ballMaterials[key] = new THREE.MeshStandardMaterial({{ 
                        map: createProceduralBallTexture(colorHex),
                        roughness: 0.15,
                        metalness: 0.15,
                        emissive: new THREE.Color(colorHex),
                        emissiveIntensity: key === 'red' ? 0.35 : 0.15
                    }});
                }}
                
                pitchData.forEach(ball => {{
                    let radius = 0.04;
                    if (ball.wicket) radius = 0.06;
                    else if (ball.runs >= 6) radius = 0.052;
                    else if (ball.runs === 4) radius = 0.046;
                    else if (ball.runs > 0) radius = 0.04;
                    else radius = 0.036;
                    
                    const ballMaterial = ballMaterials[ball.color] || ballMaterials['gray'];
                    const ballMesh = new THREE.Mesh(sharedBallGeometry, ballMaterial);
                    ballMesh.scale.set(radius, radius, radius);
                    ballMesh.position.set(ball.x, radius + 0.02, ball.y);
                    
                    // Random rotation for realistic seam alignment
                    ballMesh.rotation.set(
                        Math.random() * Math.PI,
                        Math.random() * Math.PI,
                        Math.random() * Math.PI
                    );
                    
                    ballMesh.castShadow = true;
                    scene.add(ballMesh);
                }});
                
                // Calculate zone statistics
                const zoneCounts = {{ YORKER: 0, FULL: 0, LENGTH: 0, SHORT: 0 }};
                pitchData.forEach(ball => {{
                    const y = ball.y;
                    if (y >= 0 && y < 2) zoneCounts.YORKER++;
                    else if (y >= 2 && y < 6) zoneCounts.FULL++;
                    else if (y >= 6 && y < 12) zoneCounts.LENGTH++;
                    else if (y >= 12 && y <= 22) zoneCounts.SHORT++;
                }});
                
                const total = pitchData.length;
                const statsData = [
                    {{ name: 'YORKER', count: zoneCounts.YORKER, class: 'yorker' }},
                    {{ name: 'FULL', count: zoneCounts.FULL, class: 'full' }},
                    {{ name: 'LENGTH', count: zoneCounts.LENGTH, class: 'length' }},
                    {{ name: 'SHORT', count: zoneCounts.SHORT, class: 'short' }}
                ];
                
                const statsHtml = statsData.map(stat => {{
                    const percentage = total > 0 ? ((stat.count / total) * 100).toFixed(0) : 0;
                    return `
                        <div class="zone-stat ${{stat.class}}">
                            <span class="zone-name">${{stat.name}}</span>
                            <span class="zone-percentage">${{percentage}}%</span>
                        </div>
                    `;
                }}).join('');
                
                document.getElementById('zone-stats-{unique_id}').innerHTML = statsHtml;
                
                // Camera animation helper
                function animateCamera(targetPos, targetLookAt) {{
                    const startPos = camera.position.clone();
                    const startTarget = controls.target.clone();
                    const startTime = Date.now();
                    const duration = 1000;
                    
                    function animate() {{
                        const elapsed = Date.now() - startTime;
                        const progress = Math.min(elapsed / duration, 1);
                        const eased = 1 - Math.pow(1 - progress, 3); // Cubic ease-out
                        
                        camera.position.lerpVectors(startPos, targetPos, eased);
                        controls.target.lerpVectors(startTarget, targetLookAt, eased);
                        controls.update();
                        
                        if (progress < 1) {{
                            renderer.render(scene, camera);
                            requestAnimationFrame(animate);
                        }} else {{
                            renderer.render(scene, camera);
                        }}
                    }}
                    animate();
                }}
                
                // View preset triggers
                window.setTopView_{unique_id} = () => animateCamera(
                    new THREE.Vector3(0, 38, 11),
                    new THREE.Vector3(0, 0, 11)
                );
                
                window.setBowlerView_{unique_id} = () => animateCamera(
                    new THREE.Vector3(0, 8, -8),
                    new THREE.Vector3(0, 0, 11)
                );
                
                window.setBatterView_{unique_id} = () => animateCamera(
                    new THREE.Vector3(0, 8, 32),
                    new THREE.Vector3(0, 0, 11)
                );
                
                window.setSideView_{unique_id} = () => animateCamera(
                    new THREE.Vector3(26, 12, 11),
                    new THREE.Vector3(0, 0, 11)
                );
                
                window.resetView_{unique_id} = () => animateCamera(
                    new THREE.Vector3(0, 20, 30),
                    new THREE.Vector3(0, 0, 11)
                );
                
                controls.addEventListener('change', () => renderer.render(scene, camera));
                
                // Initial render
                renderer.render(scene, camera);
                
                // UI Toggle helpers
                window.toggleStats_{unique_id} = function() {{
                    const statsOverlay = document.getElementById('stats-overlay-{unique_id}');
                    statsOverlay.classList.toggle('show');
                }};
                
                window.toggleViews_{unique_id} = function() {{
                    const viewControls = document.getElementById('view-controls-{unique_id}');
                    viewControls.classList.toggle('show');
                }};
            }})();
            </script>
        </body>
        </html>
        """
        return html

    def render_stumps_view(data, title, width=500, height=600):
        """Render stumps view visualization as 3D with interactive controls like Bowling Length Analysis"""
        data_json = json.dumps(data)
        div_id = f"stumps_view_{hashlib.md5(title.encode()).hexdigest()[:8]}"
        unique_id = hashlib.md5(title.encode()).hexdigest()[:8]
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
            <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
            <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/loaders/GLTFLoader.js"></script>
            <style>
                body {{ 
                    margin: 0; 
                    padding: 20px; 
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                }}
                .stumps-container {{ 
                    position: relative; 
                    text-align: center;
                    background: rgba(255,255,255,0.05);
                    padding: 20px;
                    border-radius: 15px;
                    backdrop-filter: blur(10px);
                }}
                .stumps-title {{ 
                    text-align: center; 
                    font-size: 26px; 
                    font-weight: bold; 
                    margin-bottom: 20px;
                    color: white;
                    text-transform: uppercase;
                    letter-spacing: 3px;
                    text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
                }}
                .stats-overlay {{
                    position: absolute;
                    top: 90px;
                    right: 30px;
                    background: rgba(0,0,0,0.95);
                    padding: 12px 16px;
                    border-radius: 10px;
                    color: white;
                    font-size: 11px;
                    min-width: 160px;
                    border: 2px solid rgba(255,255,255,0.2);
                    backdrop-filter: blur(10px);
                    display: none;
                    transition: all 0.3s ease;
                }}
                .stats-overlay.show {{
                    display: block;
                    animation: slideIn 0.3s ease-out;
                }}
                @keyframes slideIn {{
                    from {{
                        opacity: 0;
                        transform: translateX(20px);
                    }}
                    to {{
                        opacity: 1;
                        transform: translateX(0);
                    }}
                }}
                .toggle-stats-btn {{
                    position: absolute;
                    top: 90px;
                    right: 30px;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    border: none;
                    color: white;
                    padding: 10px 16px;
                    border-radius: 8px;
                    cursor: pointer;
                    font-weight: bold;
                    font-size: 12px;
                    transition: all 0.3s ease;
                    box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
                    z-index: 100;
                }}
                .toggle-stats-btn:hover {{
                    transform: translateY(-2px);
                    box-shadow: 0 6px 20px rgba(102, 126, 234, 0.5);
                }}
                .toggle-views-btn {{
                    position: absolute;
                    top: 90px;
                    left: 30px;
                    background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
                    border: none;
                    color: white;
                    padding: 10px 16px;
                    border-radius: 8px;
                    cursor: pointer;
                    font-weight: bold;
                    font-size: 12px;
                    transition: all 0.3s ease;
                    box-shadow: 0 4px 15px rgba(240, 147, 251, 0.3);
                    z-index: 100;
                }}
                .toggle-views-btn:hover {{
                    transform: translateY(-2px);
                    box-shadow: 0 6px 20px rgba(240, 147, 251, 0.5);
                }}
                .zone-stat {{
                    margin: 6px 0;
                    padding: 8px 10px;
                    background: linear-gradient(135deg, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0.05) 100%);
                    border-radius: 6px;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    border-left: 3px solid;
                }}
                .zone-name {{
                    font-weight: bold;
                    text-transform: uppercase;
                    font-size: 10px;
                    letter-spacing: 1px;
                }}
                .zone-percentage {{
                    font-size: 20px;
                    font-weight: bold;
                }}
                .wickets {{ color: #ff6b6b; border-color: #ff6b6b; }}
                .boundaries {{ color: #9c27b0; border-color: #9c27b0; }}
                .singles {{ color: #00ff00; border-color: #00ff00; }}
                .twos {{ color: #2196f3; border-color: #2196f3; }}
                .dots {{ color: #808080; border-color: #808080; }}
                .legend-title {{
                    font-weight: bold;
                    margin-bottom: 10px;
                    font-size: 12px;
                    border-bottom: 2px solid rgba(255,255,255,0.3);
                    padding-bottom: 8px;
                    text-transform: uppercase;
                    letter-spacing: 1.5px;
                }}
                .view-controls {{
                    position: absolute;
                    top: 90px;
                    left: 30px;
                    background: rgba(0,0,0,0.9);
                    padding: 12px 14px;
                    border-radius: 10px;
                    color: white;
                    font-size: 11px;
                    border: 2px solid rgba(255,255,255,0.2);
                    backdrop-filter: blur(10px);
                    display: none;
                    z-index: 10;
                }}
                .view-controls.show {{
                    display: block;
                    animation: slideInLeft 0.3s ease-out;
                }}
                @keyframes slideInLeft {{
                    from {{
                        opacity: 0;
                        transform: translateX(-20px);
                    }}
                    to {{
                        opacity: 1;
                        transform: translateX(0);
                    }}
                }}
                .view-btn {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    border: none;
                    color: white;
                    padding: 8px 12px;
                    margin: 3px 0;
                    border-radius: 6px;
                    cursor: pointer;
                    width: 100%;
                    font-weight: bold;
                    font-size: 11px;
                    transition: all 0.3s ease;
                    box-shadow: 0 3px 10px rgba(102, 126, 234, 0.3);
                }}
                .view-btn:hover {{
                    transform: translateY(-2px);
                    box-shadow: 0 5px 15px rgba(102, 126, 234, 0.5);
                }}
                .controls-title {{
                    font-weight: bold;
                    margin-bottom: 8px;
                    font-size: 12px;
                    border-bottom: 2px solid rgba(255,255,255,0.3);
                    padding-bottom: 6px;
                    text-transform: uppercase;
                    letter-spacing: 1.5px;
                }}
            </style>
        </head>
        <body>
            <div class="stumps-container">
                <div class="stumps-title">{title}</div>
                <div id="{div_id}"></div>
                <button class="toggle-views-btn" onclick="toggleViews_{unique_id}()">📐 Views</button>
                <button class="toggle-stats-btn" onclick="toggleStats_{unique_id}()">📊 Statistics</button>
                <div class="view-controls" id="view-controls-{unique_id}">
                    <div class="controls-title">📐 VIEWS</div>
                    <button class="view-btn" onclick="setFrontView_{unique_id}()">📍 Front</button>
                    <button class="view-btn" onclick="setTopView_{unique_id}()">🎯 Top</button>
                    <button class="view-btn" onclick="setSideView_{unique_id}()">👁️ Side</button>
                    <button class="view-btn" onclick="resetView_{unique_id}()">🔄 Reset</button>
                </div>
                <div class="stats-overlay" id="stats-overlay-{unique_id}">
                    <div class="legend-title">📊 Ball Statistics</div>
                    <div id="zone-stats-{unique_id}"></div>
                </div>
            </div>
            
            <script>
            (function() {{
                const stumpsData = {data_json};
                const scene = new THREE.Scene();
                
                // Realistic sky gradient
                const skyCanvas = document.createElement('canvas');
                skyCanvas.width = 512; skyCanvas.height = 512;
                const skyCtx = skyCanvas.getContext('2d');
                const skyGrad = skyCtx.createLinearGradient(0, 0, 0, 512);
                skyGrad.addColorStop(0, '#1a3a5c');
                skyGrad.addColorStop(0.3, '#3a7bd5');
                skyGrad.addColorStop(0.6, '#87ceeb');
                skyGrad.addColorStop(1, '#b5e3f5');
                skyCtx.fillStyle = skyGrad;
                skyCtx.fillRect(0, 0, 512, 512);
                const skyTexture = new THREE.CanvasTexture(skyCanvas);
                scene.background = skyTexture;
                scene.fog = new THREE.Fog(0x87ceeb, 40, 120);
                
                const camera = new THREE.PerspectiveCamera(45, {width}/{height}, 0.1, 200);
                camera.position.set(0, 8, 25);
                camera.lookAt(0, 1.5, 0);
                
                const renderer = new THREE.WebGLRenderer({{ antialias: true }});
                renderer.setSize({width}, {height});
                renderer.shadowMap.enabled = true;
                renderer.shadowMap.type = THREE.PCFShadowMap;
                renderer.toneMapping = THREE.ACESFilmicToneMapping;
                renderer.toneMappingExposure = 1.1;
                document.getElementById('{div_id}').appendChild(renderer.domElement);
                
                const controls = new THREE.OrbitControls(camera, renderer.domElement);
                controls.enableDamping = true;
                controls.dampingFactor = 0.05;
                controls.minDistance = 8;
                controls.maxDistance = 50;
                controls.maxPolarAngle = Math.PI / 2;
                controls.target.set(0, 1.5, 0);
                
                // Lighting — warm stadium feel
                const ambientLight = new THREE.AmbientLight(0xfff5e6, 0.5);
                scene.add(ambientLight);
                const hemisphereLight = new THREE.HemisphereLight(0x87ceeb, 0x1a7a1a, 0.4);
                scene.add(hemisphereLight);
                
                const sunLight = new THREE.DirectionalLight(0xfffde6, 0.9);
                sunLight.position.set(15, 30, 20);
                sunLight.castShadow = true;
                sunLight.shadow.mapSize.width = 1024;
                sunLight.shadow.mapSize.height = 1024;
                sunLight.shadow.camera.left = -30;
                sunLight.shadow.camera.right = 30;
                sunLight.shadow.camera.top = 30;
                sunLight.shadow.camera.bottom = -30;
                scene.add(sunLight);
                
                const fillLight = new THREE.DirectionalLight(0xb0d4f1, 0.3);
                fillLight.position.set(-10, 15, -10);
                scene.add(fillLight);
                
                // Procedural grass with mowing stripes
                const grassCanvas = document.createElement('canvas');
                grassCanvas.width = 512; grassCanvas.height = 512;
                const grassCtx = grassCanvas.getContext('2d');
                for (let i = 0; i < 16; i++) {{
                    grassCtx.fillStyle = i % 2 === 0 ? '#1a7a1a' : '#15701a';
                    grassCtx.fillRect(0, i * 32, 512, 32);
                }}
                for (let i = 0; i < 3000; i++) {{
                    const gx = Math.random() * 512;
                    const gy = Math.random() * 512;
                    grassCtx.fillStyle = `rgba(20, ${{85 + Math.random() * 50}}, 18, 0.5)`;
                    grassCtx.fillRect(gx, gy, 1, 2);
                }}
                const grassTexture = new THREE.CanvasTexture(grassCanvas);
                grassTexture.wrapS = THREE.RepeatWrapping;
                grassTexture.wrapT = THREE.RepeatWrapping;
                grassTexture.repeat.set(4, 4);
                
                // Ground — large oval outfield
                const groundGeometry = new THREE.CircleGeometry(60, 64);
                const groundMaterial = new THREE.MeshStandardMaterial({{ 
                    map: grassTexture,
                    roughness: 0.85,
                    metalness: 0.05
                }});
                const ground = new THREE.Mesh(groundGeometry, groundMaterial);
                ground.rotation.x = -Math.PI / 2;
                ground.receiveShadow = true;
                scene.add(ground);
                
                // Boundary rope (white ring)
                const ropeGeo = new THREE.RingGeometry(55, 55.4, 64);
                const ropeMat = new THREE.MeshStandardMaterial({{ color: 0xffffff, roughness: 0.4 }});
                const rope = new THREE.Mesh(ropeGeo, ropeMat);
                rope.rotation.x = -Math.PI / 2; rope.position.y = 0.06;
                scene.add(rope);
                
                // 30-yard inner circle
                const innerGeo = new THREE.RingGeometry(27.4, 27.7, 64);
                const innerMat = new THREE.MeshStandardMaterial({{ color: 0xffffff, roughness: 0.5 }});
                const innerCircle = new THREE.Mesh(innerGeo, innerMat);
                innerCircle.rotation.x = -Math.PI / 2; innerCircle.position.y = 0.04;
                scene.add(innerCircle);
                
                // Load realistic 3D Stadium Model in the background
                const loader = new THREE.GLTFLoader();
                loader.load(
                    '/app/static/stadium.glb',
                    function (gltf) {{
                        const model = gltf.scene;
                        
                        // Compute bounding box
                        const box = new THREE.Box3().setFromObject(model);
                        const size = box.getSize(new THREE.Vector3());
                        const center = box.getCenter(new THREE.Vector3());
                        
                        // Center model
                        model.position.x += (model.position.x - center.x);
                        model.position.y += (model.position.y - box.min.y) - 1.5;
                        model.position.z += (model.position.z - center.z);
                        
                        // Scale to cover the outfield
                        const maxDim = Math.max(size.x, size.z);
                        const scaleFactor = 200 / maxDim;
                        model.scale.set(scaleFactor, scaleFactor, scaleFactor);
                        
                        model.traverse(function (node) {{
                            if (node.isMesh) {{
                                node.castShadow = false;
                                node.receiveShadow = false;
                                if (node.material) {{
                                    node.material.roughness = 0.75;
                                    node.material.metalness = 0.15;
                                }}
                            }}
                        }});
                        
                        scene.add(model);
                        renderer.render(scene, camera);
                    }},
                    undefined,
                    function (error) {{
                        console.error('Error loading 3D stadium model:', error);
                    }}
                );
                scene.add(ground);
                
                // Cricket pitch dimensions (22 yards = 20.12m length, 3.05m width)
                const pitchLength = 20.12;
                const pitchWidth = 3.05;
                
                // Pitch surface
                const pitchGeometry = new THREE.PlaneGeometry(pitchWidth, pitchLength);
                const pitchMaterial = new THREE.MeshStandardMaterial({{ 
                    color: 0xd4a574,
                    roughness: 0.9,
                    metalness: 0.1
                }});
                const pitch = new THREE.Mesh(pitchGeometry, pitchMaterial);
                pitch.rotation.x = -Math.PI / 2;
                pitch.position.y = 0.01;
                pitch.receiveShadow = true;
                scene.add(pitch);
                
                // Stump specifications (standard cricket dimensions)
                const stumpMaterial = new THREE.MeshStandardMaterial({{ 
                    color: 0x8B4513,
                    roughness: 0.4,
                    metalness: 0.2
                }});
                const stumpHeight = 0.71; // 71cm
                const stumpRadius = 0.02; // 2cm radius
                const stumpSpacing = 0.11; // 11cm between stumps
                const stumpPositions = [-stumpSpacing, 0, stumpSpacing];
                
                // Batting stumps at near end (z = pitchLength/2)
                const battingStumpZ = pitchLength / 2;
                stumpPositions.forEach(x => {{
                    const stump = new THREE.Mesh(
                        new THREE.CylinderGeometry(stumpRadius, stumpRadius, stumpHeight, 8), 
                        stumpMaterial
                    );
                    stump.position.set(x, stumpHeight / 2, battingStumpZ);
                    stump.castShadow = true;
                    scene.add(stump);
                }});
                
                // Bails on batting stumps
                const bailMaterial = new THREE.MeshStandardMaterial({{ 
                    color: 0x8B4513,
                    roughness: 0.4,
                    metalness: 0.2
                }});
                const bailLength = 0.11;
                [-stumpSpacing/2, stumpSpacing/2].forEach(x => {{
                    const bail = new THREE.Mesh(
                        new THREE.CylinderGeometry(0.01, 0.01, bailLength, 8),
                        bailMaterial
                    );
                    bail.rotation.z = Math.PI / 2;
                    bail.position.set(x, stumpHeight, battingStumpZ);
                    scene.add(bail);
                }});
                
                // Bowling stumps at far end (z = -pitchLength/2)
                const bowlingStumpZ = -pitchLength / 2;
                stumpPositions.forEach(x => {{
                    const stump = new THREE.Mesh(
                        new THREE.CylinderGeometry(stumpRadius, stumpRadius, stumpHeight, 8), 
                        stumpMaterial
                    );
                    stump.position.set(x, stumpHeight / 2, bowlingStumpZ);
                    stump.castShadow = true;
                    scene.add(stump);
                }});
                
                // Bails on bowling stumps
                [-stumpSpacing/2, stumpSpacing/2].forEach(x => {{
                    const bail = new THREE.Mesh(
                        new THREE.CylinderGeometry(0.01, 0.01, bailLength, 8),
                        bailMaterial
                    );
                    bail.rotation.z = Math.PI / 2;
                    bail.position.set(x, stumpHeight, bowlingStumpZ);
                    scene.add(bail);
                }});
                
                // Crease lines
                const lineMaterial = new THREE.MeshStandardMaterial({{ 
                    color: 0xffffff,
                    roughness: 0.6
                }});
                
                // Batting crease (at batting end)
                const battingCrease = new THREE.Mesh(
                    new THREE.PlaneGeometry(pitchWidth, 0.05),
                    lineMaterial
                );
                battingCrease.rotation.x = -Math.PI / 2;
                battingCrease.position.set(0, 0.02, battingStumpZ);
                scene.add(battingCrease);
                
                // Bowling crease (at bowling end)
                const bowlingCrease = new THREE.Mesh(
                    new THREE.PlaneGeometry(pitchWidth, 0.05),
                    lineMaterial
                );
                bowlingCrease.rotation.x = -Math.PI / 2;
                bowlingCrease.position.set(0, 0.02, bowlingStumpZ);
                scene.add(bowlingCrease);
                
                // Wide line markers (dashed effect with small rectangles)
                // Positioned at approximately 1.2m from center on each side
                const wideLineMaterial = new THREE.MeshStandardMaterial({{ 
                    color: 0xff0000,
                    transparent: true,
                    opacity: 0.6
                }});
                
                const wideLineX = 1.2;
                for (let z = -pitchLength/2; z < pitchLength/2; z += 0.4) {{
                    // Left wide line
                    const leftWide = new THREE.Mesh(
                        new THREE.PlaneGeometry(0.03, 0.2),
                        wideLineMaterial
                    );
                    leftWide.rotation.x = -Math.PI / 2;
                    leftWide.position.set(-wideLineX, 0.02, z);
                    scene.add(leftWide);
                    
                    // Right wide line
                    const rightWide = new THREE.Mesh(
                        new THREE.PlaneGeometry(0.03, 0.2),
                        wideLineMaterial
                    );
                    rightWide.rotation.x = -Math.PI / 2;
                    rightWide.position.set(wideLineX, 0.02, z);
                    scene.add(rightWide);
                }}
                
                // Color map for balls
                const colorMap = {{
                    'red': 0xff0000,
                    'purple': 0x9c27b0,
                    'green': 0x00ff00,
                    'blue': 0x2196f3,
                    'gray': 0x808080
                }};
                
                // Statistics
                let stats = {{
                    total: stumpsData.length,
                    wickets: 0,
                    boundaries: 0,
                    singles: 0,
                    twosThrees: 0,
                    dots: 0
                }};
                
                const sharedBallGeometry = new THREE.SphereGeometry(1, 16, 16);
                const ballMaterials = {{}};
                for (const [key, colorHex] of Object.entries(colorMap)) {{
                    ballMaterials[key] = new THREE.MeshStandardMaterial({{ 
                        color: colorHex,
                        roughness: 0.3,
                        metalness: 0.6,
                        emissive: colorHex,
                        emissiveIntensity: 0.2
                    }});
                }}
                
                // Draw balls with better distribution across pitch
                stumpsData.forEach(ball => {{
                    // Update stats
                    switch(ball.color) {{
                        case 'red': stats.wickets++; break;
                        case 'purple': stats.boundaries++; break;
                        case 'green': stats.singles++; break;
                        case 'blue': stats.twosThrees++; break;
                        case 'gray': stats.dots++; break;
                    }}
                    
                    const radius = ball.size * 0.012;
                    const ballMaterial = ballMaterials[ball.color] || ballMaterials['gray'];
                    const sphere = new THREE.Mesh(sharedBallGeometry, ballMaterial);
                    sphere.scale.set(radius, radius, radius);
                    
                    // Position mapping for better visualization:
                    // ball.x: horizontal position (-2 to 2) - maps to line (wide left to wide right)
                    // ball.y: vertical position along pitch (0 to 5) - maps to length (bowling end to batting end)
                    // ball.z: height above ground
                    
                    // Map x coordinate: -2 to 2 range maps to -1.4 to 1.4 on pitch (within 3.05m width)
                    const xPos = ball.x * 0.7;
                    
                    // Map y coordinate: 0 to 5 range maps along full pitch length (20.12m)
                    // bowling end (-10.06) to batting end (+10.06)
                    const zPos = (ball.y * 4.024) - 10.06;
                    
                    // Height: slightly above pitch surface
                    const yPos = radius + 0.02;
                    
                    sphere.position.set(xPos, yPos, zPos);
                    sphere.castShadow = true;
                    scene.add(sphere);
                }});
                
                // Display statistics
                const statsHtml = `
                    <div class="zone-stat wickets">
                        <span class="zone-name">Wickets</span>
                        <span class="zone-percentage">${{stats.wickets}}</span>
                    </div>
                    <div class="zone-stat boundaries">
                        <span class="zone-name">Boundaries</span>
                        <span class="zone-percentage">${{stats.boundaries}}</span>
                    </div>
                    <div class="zone-stat singles">
                        <span class="zone-name">Singles</span>
                        <span class="zone-percentage">${{stats.singles}}</span>
                    </div>
                    <div class="zone-stat twos">
                        <span class="zone-name">2s/3s</span>
                        <span class="zone-percentage">${{stats.twosThrees}}</span>
                    </div>
                    <div class="zone-stat dots">
                        <span class="zone-name">Dot Balls</span>
                        <span class="zone-percentage">${{stats.dots}}</span>
                    </div>
                    <div class="zone-stat" style="border-top: 2px solid rgba(255,255,255,0.3); margin-top: 10px; padding-top: 10px;">
                        <span class="zone-name">Total</span>
                        <span class="zone-percentage">${{stats.total}}</span>
                    </div>
                `;
                document.getElementById('zone-stats-{unique_id}').innerHTML = statsHtml;
                
                // Camera animation function
                function animateCamera(targetPos, targetLookAt, duration = 1000) {{
                    const startPos = {{
                        x: camera.position.x,
                        y: camera.position.y,
                        z: camera.position.z
                    }};
                    const startTime = Date.now();
                    
                    function animate() {{
                        const elapsed = Date.now() - startTime;
                        const progress = Math.min(elapsed / duration, 1);
                        const eased = progress < 0.5 
                            ? 2 * progress * progress 
                            : -1 + (4 - 2 * progress) * progress;
                        
                        camera.position.x = startPos.x + (targetPos.x - startPos.x) * eased;
                        camera.position.y = startPos.y + (targetPos.y - startPos.y) * eased;
                        camera.position.z = startPos.z + (targetPos.z - startPos.z) * eased;
                        
                        controls.target.set(targetLookAt.x, targetLookAt.y, targetLookAt.z);
                        controls.update();
                        
                        if (progress < 1) {{
                            renderer.render(scene, camera);
                            requestAnimationFrame(animate);
                        }} else {{
                            renderer.render(scene, camera); // Final render
                        }}
                    }}
                    animate();
                }}
                
                // View preset functions
                window.setFrontView_{unique_id} = () => animateCamera(
                    {{ x: 0, y: 8, z: 25 }},
                    {{ x: 0, y: 1.5, z: 0 }}
                );
                
                window.setTopView_{unique_id} = () => animateCamera(
                    {{ x: 0, y: 30, z: 0 }},
                    {{ x: 0, y: 0, z: 0 }}
                );
                
                window.setSideView_{unique_id} = () => animateCamera(
                    {{ x: 25, y: 8, z: 0 }},
                    {{ x: 0, y: 1.5, z: 0 }}
                );
                
                window.resetView_{unique_id} = () => animateCamera(
                    {{ x: 0, y: 8, z: 25 }},
                    {{ x: 0, y: 1.5, z: 0 }}
                );
                
                controls.enableDamping = false; // Disable damping since we don't have a continuous animation loop
                controls.addEventListener('change', () => renderer.render(scene, camera));
                
                // Initial render
                renderer.render(scene, camera);
                
                // Toggle statistics overlay
                window.toggleStats_{unique_id} = function() {{
                    const statsOverlay = document.getElementById('stats-overlay-{unique_id}');
                    statsOverlay.classList.toggle('show');
                }};
                
                // Toggle view controls
                window.toggleViews_{unique_id} = function() {{
                    const viewControls = document.getElementById('view-controls-{unique_id}');
                    viewControls.classList.toggle('show');
                }};
            }})();
            </script>
        </body>
        </html>
        """
        return html
    
    
    def render_advanced_pitch_viz(data, title, width=1200, height=450):
        """Render advanced 4-panel pitch visualization with heat maps"""
        import json
        
        if not data:
            return "<p>No data available</p>"
        
        data_json = json.dumps(data)
        div_id = f"advanced_pitch_{hashlib.md5(title.encode()).hexdigest()[:8]}"
        
        # Separate wickets and non-wickets
        wickets = [d for d in data if d['wicket'] == 1]
        hitting = [d for d in data if d['wicket'] == 0]
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <script src="https://cdn.plot.ly/plotly-2.26.0.min.js"></script>
            <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@500;700;900&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
            <style>
                body {{ 
                    margin: 0; 
                    padding: 0; 
                    background: transparent; 
                    font-family: 'Inter', sans-serif;
                }}
                .viz-container-{div_id} {{ 
                    display: grid; 
                    grid-template-columns: repeat(2, 1fr); 
                    gap: 16px; 
                    margin: 10px 0;
                    background: transparent;
                    padding: 0;
                    border-radius: 12px;
                }}
                .viz-item-{div_id} {{ 
                    border: 1px solid rgba(255, 255, 255, 0.08); 
                    border-radius: 12px; 
                    padding: 15px;
                    background: rgba(15, 23, 42, 0.6);
                    backdrop-filter: blur(12px);
                    -webkit-backdrop-filter: blur(12px);
                    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
                    box-shadow: 0 8px 32px rgba(0,0,0,0.4);
                }}
                .viz-item-{div_id}:hover {{ 
                    transform: translateY(-3px);
                    box-shadow: 0 12px 36px rgba(56, 189, 248, 0.15);
                    border-color: rgba(56, 189, 248, 0.3);
                }}
                .viz-subtitle-{div_id} {{ 
                    text-align: center; 
                    font-size: 13px; 
                    font-weight: 700; 
                    margin-bottom: 12px;
                    color: #f1f5f9;
                    font-family: 'Orbitron', sans-serif;
                    text-transform: uppercase;
                    letter-spacing: 2px;
                    background: linear-gradient(135deg, #e2e8f0, #94a3b8);
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                }}
            </style>
        </head>
        <body>
            <div class="viz-container-{div_id}">
                <div class="viz-item-{div_id}">
                    <div class="viz-subtitle-{div_id}">Wickets</div>
                    <div id="plot1_{div_id}"></div>
                </div>
                <div class="viz-item-{div_id}">
                    <div class="viz-subtitle-{div_id}">Non‑Wickets</div>
                    <div id="plot2_{div_id}"></div>
                </div>
                <div class="viz-item-{div_id}">
                    <div class="viz-subtitle-{div_id}">Density Heat Map</div>
                    <div id="plot3_{div_id}"></div>
                </div>
                <div class="viz-item-{div_id}">
                    <div class="viz-subtitle-{div_id}">Combined</div>
                    <div id="plot4_{div_id}"></div>
                </div>
            </div>
            
            <script>
            (function() {{
                const allData = {data_json};
                const wickets = allData.filter(d => d.wicket === 1);
                const hitting = allData.filter(d => d.wicket === 0);
                
                const commonLayout = {{
                    height: 380,
                    margin: {{ t: 10, r: 10, b: 30, l: 30 }},
                    xaxis: {{ 
                        range: [-1.5, 1.5], 
                        showgrid: true, 
                        gridcolor: 'rgba(255, 255, 255, 0.05)',
                        gridwidth: 1,
                        zeroline: false,
                        title: '',
                        tickfont: {{ size: 9, color: '#94a3b8', family: 'Inter' }}
                    }},
                    yaxis: {{ 
                        range: [0, 22], 
                        showgrid: true,
                        gridcolor: 'rgba(255, 255, 255, 0.05)',
                        gridwidth: 1,
                        zeroline: false,
                        title: '',
                        tickfont: {{ size: 9, color: '#94a3b8', family: 'Inter' }}
                    }},
                    plot_bgcolor: '#3e2723',
                    paper_bgcolor: 'rgba(0,0,0,0)',
                    showlegend: false,
                    images: [
                        // Pitch center strip (glowing worn area)
                        {{
                            source: 'data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="1" height="1"><rect width="100%" height="100%" fill="%234e3629"/></svg>',
                            xref: 'x',
                            yref: 'y',
                            x: -0.5,
                            y: 22,
                            sizex: 1,
                            sizey: 22,
                            sizing: 'stretch',
                            opacity: 0.7,
                            layer: 'below'
                        }}
                    ]
                }};
                
                // Cricket stumps (3 vertical lines for each end)
                const stumpHeight = 0.35;
                
                // Batting end stumps (bottom)
                const battingStumps = [
                    {{ x: [-0.115, -0.115], y: [0, stumpHeight], mode: 'lines', line: {{ color: '#d7be96', width: 3 }}, hoverinfo: 'skip' }},
                    {{ x: [0, 0], y: [0, stumpHeight], mode: 'lines', line: {{ color: '#d7be96', width: 3 }}, hoverinfo: 'skip' }},
                    {{ x: [0.115, 0.115], y: [0, stumpHeight], mode: 'lines', line: {{ color: '#d7be96', width: 3 }}, hoverinfo: 'skip' }},
                    // Bails
                    {{ x: [-0.115, 0.115], y: [stumpHeight, stumpHeight], mode: 'lines', line: {{ color: '#d7be96', width: 2 }}, hoverinfo: 'skip' }}
                ];
                
                // Bowling end stumps (top)
                const bowlingStumps = [
                    {{ x: [-0.115, -0.115], y: [22 - stumpHeight, 22], mode: 'lines', line: {{ color: '#d7be96', width: 3 }}, hoverinfo: 'skip' }},
                    {{ x: [0, 0], y: [22 - stumpHeight, 22], mode: 'lines', line: {{ color: '#d7be96', width: 3 }}, hoverinfo: 'skip' }},
                    {{ x: [0.115, 0.115], y: [22 - stumpHeight, 22], mode: 'lines', line: {{ color: '#d7be96', width: 3 }}, hoverinfo: 'skip' }},
                    // Bails
                    {{ x: [-0.115, 0.115], y: [22 - stumpHeight, 22 - stumpHeight], mode: 'lines', line: {{ color: '#d7be96', width: 2 }}, hoverinfo: 'skip' }}
                ];
                
                // Crease lines
                const creaseLines = [
                    // Batting crease (bottom)
                    {{ x: [-1.35, 1.35], y: [1.22, 1.22], mode: 'lines', line: {{ color: 'rgba(255,255,255,0.7)', width: 2 }}, hoverinfo: 'skip' }},
                    {{ x: [-1.35, 1.35], y: [0, 0], mode: 'lines', line: {{ color: 'rgba(255,255,255,0.7)', width: 2 }}, hoverinfo: 'skip' }},
                    // Bowling crease (top)
                    {{ x: [-1.35, 1.35], y: [20.78, 20.78], mode: 'lines', line: {{ color: 'rgba(255,255,255,0.7)', width: 2 }}, hoverinfo: 'skip' }},
                    {{ x: [-1.35, 1.35], y: [22, 22], mode: 'lines', line: {{ color: 'rgba(255,255,255,0.7)', width: 2 }}, hoverinfo: 'skip' }},
                    // Return creases
                    {{ x: [-1.35, -1.35], y: [0, 2.44], mode: 'lines', line: {{ color: 'rgba(255,255,255,0.7)', width: 1.5 }}, hoverinfo: 'skip' }},
                    {{ x: [1.35, 1.35], y: [0, 2.44], mode: 'lines', line: {{ color: 'rgba(255,255,255,0.7)', width: 1.5 }}, hoverinfo: 'skip' }},
                    {{ x: [-1.35, -1.35], y: [19.56, 22], mode: 'lines', line: {{ color: 'rgba(255,255,255,0.7)', width: 1.5 }}, hoverinfo: 'skip' }},
                    {{ x: [1.35, 1.35], y: [19.56, 22], mode: 'lines', line: {{ color: 'rgba(255,255,255,0.7)', width: 1.5 }}, hoverinfo: 'skip' }}
                ];
                
                // Plot 1: Wickets
                const wicketsTrace = {{
                    x: wickets.map(d => d.x),
                    y: wickets.map(d => d.y),
                    mode: 'markers',
                    type: 'scatter',
                    marker: {{
                        size: 11,
                        color: '#ef4444',
                        opacity: 0.9,
                        line: {{ width: 1.5, color: '#ffffff' }}
                    }},
                    hovertemplate: '<b>WICKET</b><br>%{{text}}<extra></extra>',
                    text: wickets.map(d => 'Batter: ' + d.batter + '<br>Bowler: ' + d.bowler)
                }};
                
                const layout1 = Object.assign({{}}, commonLayout);
                if (wickets.length === 0) {{
                    layout1.annotations = [{{
                        text: "<b>NO WICKETS IN SELECTED RANGE</b>",
                        xref: "paper", yref: "paper",
                        x: 0.5, y: 0.5, showarrow: false,
                        font: {{ size: 12, color: "#ef4444", family: 'Orbitron' }},
                        bgcolor: "rgba(15, 23, 42, 0.9)",
                        bordercolor: "#ef4444",
                        borderwidth: 1.5,
                        borderpad: 8
                    }}];
                }}
                
                Plotly.newPlot('plot1_{div_id}', [wicketsTrace, ...creaseLines, ...battingStumps, ...bowlingStumps], layout1, {{displayModeBar: false, responsive: true}});
                
                // Plot 2: Non‑Wickets (per-delivery color by runs)
                const hittingTrace = {{
                    x: hitting.map(d => d.x),
                    y: hitting.map(d => d.y),
                    mode: 'markers',
                    type: 'scatter',
                    marker: {{
                        size: hitting.map(d => d.size),
                        color: hitting.map(d => d.color),
                        opacity: 0.8,
                        line: {{ width: 0.5, color: 'rgba(255,255,255,0.8)' }}
                    }},
                    hovertemplate: '<b>%{{text}} run(s)</b><br>%{{customdata}}<extra></extra>',
                    text: hitting.map(d => d.runs),
                    customdata: hitting.map(d => 'Bowler: ' + d.bowler)
                }};
                
                Plotly.newPlot('plot2_{div_id}', [hittingTrace, ...creaseLines, ...battingStumps, ...bowlingStumps], commonLayout, {{displayModeBar: false, responsive: true}});
                
                // Plot 3: Heat map
                const heatmapTrace = {{
                    x: allData.map(d => d.x),
                    y: allData.map(d => d.y),
                    type: 'histogram2dcontour',
                    colorscale: [
                        [0, '#3e2723'],
                        [0.2, '#4e3629'],
                        [0.4, '#38bdf8'],
                        [0.6, '#6366f1'],
                        [0.8, '#a855f7'],
                        [1, '#ef4444']
                    ],
                    showscale: true,
                    colorbar: {{
                        len: 0.7,
                        thickness: 8,
                        x: 1.02,
                        tickfont: {{ size: 8, color: '#94a3b8' }}
                    }},
                    contours: {{
                        coloring: 'heatmap',
                        showlabels: false
                    }},
                    hoverinfo: 'skip'
                }};
                
                Plotly.newPlot('plot3_{div_id}', [heatmapTrace, ...creaseLines, ...battingStumps, ...bowlingStumps], commonLayout, {{displayModeBar: false, responsive: true}});
                
                // Plot 4: Combined
                const wicketsCombined = {{
                    x: wickets.map(d => d.x),
                    y: wickets.map(d => d.y),
                    mode: 'markers',
                    type: 'scatter',
                    marker: {{
                        size: 8,
                        color: '#ef4444',
                        opacity: 0.9,
                        line: {{ width: 1, color: '#ffffff' }}
                    }},
                    hovertemplate: '<b>WICKET</b><br>%{{text}}<extra></extra>',
                    text: wickets.map(d => 'Batter: ' + d.batter + '<br>Bowler: ' + d.bowler)
                }};
                
                const hittingCombined = {{
                    x: hitting.map(d => d.x),
                    y: hitting.map(d => d.y),
                    mode: 'markers',
                    type: 'scatter',
                    marker: {{
                        size: hitting.map(d => d.size),
                        color: hitting.map(d => d.color),
                        opacity: 0.7
                    }},
                    hovertemplate: '<b>%{{text}} runs</b><br>%{{customdata}}<extra></extra>',
                    text: hitting.map(d => d.runs),
                    customdata: hitting.map(d => 'Bowler: ' + d.bowler)
                }};
                
                Plotly.newPlot('plot4_{div_id}', [hittingCombined, wicketsCombined, ...creaseLines, ...battingStumps, ...bowlingStumps], commonLayout, {{displayModeBar: false, responsive: true}});
            }})();
            </script>
        </body>
        </html>
        """
        return html
    
    def render_player_stats_cards(stats_df, title):
        """Render player statistics cards with Pace/Spin splits & Impact Rating"""
        if stats_df.empty:
            return "<p>No player statistics available</p>"
        div_id = f"player_stats_{hashlib.md5(title.encode()).hexdigest()[:8]}"
        players_data = []
        for idx, row in stats_df.iterrows():
            players_data.append({
                'name': str(row['batter']),
                'runs': int(row['runs_off_bat']),
                'balls': int(row['ball']),
                'sr': float(row['strike_rate']),
                'avg': float(row['average']),
                'fours': int(row['fours']),
                'sixes': int(row['sixes']),
                'dismissals': int(row['is_wicket']),
                'highest': int(row['highest_score']),
                'sr_pace': float(row.get('sr_pace', row['strike_rate'])),
                'sr_spin': float(row.get('sr_spin', row['strike_rate'])),
                'impact': float(row.get('impact_score', 0))
            })
        
        data_json = json.dumps(players_data)
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{
                    margin: 0;
                    padding: 0;
                    background: transparent;
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                }}
                .stats-container-{div_id} {{
                    display: grid;
                    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
                    gap: 16px;
                    padding: 15px;
                }}
                .player-card-{div_id} {{
                    background: rgba(15, 23, 42, 0.7);
                    backdrop-filter: blur(12px);
                    -webkit-backdrop-filter: blur(12px);
                    border: 1px solid rgba(255, 255, 255, 0.1);
                    border-radius: 12px;
                    padding: 16px;
                    color: #f8fafc;
                    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
                    transition: all 0.3s ease;
                    position: relative;
                    overflow: hidden;
                }}
                .player-card-{div_id}::before {{
                    content: '';
                    position: absolute;
                    top: 0; left: 0; right: 0;
                    height: 3px;
                    background: var(--accent-color, #3b82f6);
                }}
                .player-card-{div_id}:hover {{
                    transform: translateY(-5px);
                    box-shadow: 0 12px 40px rgba(0, 0, 0, 0.5), 0 0 15px var(--accent-color);
                    border-color: rgba(255, 255, 255, 0.2);
                }}
                .player-rank-{div_id} {{
                    position: absolute;
                    top: 12px;
                    right: 12px;
                    background: linear-gradient(135deg, rgba(255,255,255,0.1), rgba(255,255,255,0.05));
                    border: 1px solid rgba(255,255,255,0.2);
                    width: 30px;
                    height: 30px;
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-size: 14px;
                    font-weight: 700;
                    color: var(--accent-color);
                    box-shadow: 0 2px 10px rgba(0,0,0,0.2);
                }}
                .player-name-{div_id} {{
                    font-size: 17px;
                    font-weight: 700;
                    margin-bottom: 12px;
                    padding-right: 45px;
                    letter-spacing: 0.5px;
                    color: #ffffff;
                }}
                .main-stats-{div_id} {{
                    display: flex;
                    justify-content: space-between;
                    margin-bottom: 12px;
                    padding: 12px;
                    background: rgba(0, 0, 0, 0.3);
                    border-radius: 8px;
                    border: 1px solid rgba(255,255,255,0.05);
                }}
                .stat-item-{div_id} {{
                    text-align: center;
                }}
                .stat-value-{div_id} {{
                    font-size: 20px;
                    font-weight: 800;
                    display: block;
                    color: #38bdf8;
                }}
                .stat-label-{div_id} {{
                    font-size: 10px;
                    opacity: 0.7;
                    text-transform: uppercase;
                    letter-spacing: 1px;
                }}
                .splits-{div_id} {{
                    display: flex;
                    gap: 8px;
                    margin-bottom: 10px;
                }}
                .split-badge-{div_id} {{
                    flex: 1;
                    background: rgba(56, 189, 248, 0.1);
                    border: 1px solid rgba(56, 189, 248, 0.25);
                    padding: 6px 8px;
                    border-radius: 6px;
                    text-align: center;
                }}
                .split-val-{div_id} {{
                    font-size: 13px;
                    font-weight: 700;
                    display: block;
                    color: #38bdf8;
                }}
                .split-lbl-{div_id} {{
                    font-size: 9px;
                    color: #94a3b8;
                    text-transform: uppercase;
                }}
                .boundaries-{div_id} {{
                    display: flex;
                    gap: 10px;
                    margin-bottom: 12px;
                }}
                .boundary-badge-{div_id} {{
                    flex: 1;
                    background: rgba(255, 255, 255, 0.05);
                    border: 1px solid rgba(255, 255, 255, 0.1);
                    padding: 6px;
                    border-radius: 6px;
                    text-align: center;
                }}
                .boundary-value-{div_id} {{
                    font-size: 15px;
                    font-weight: 700;
                    display: block;
                    color: #e2e8f0;
                }}
                .boundary-label-{div_id} {{
                    font-size: 9px;
                    opacity: 0.6;
                    text-transform: uppercase;
                }}
                .secondary-stats-{div_id} {{
                    display: grid;
                    grid-template-columns: repeat(2, 1fr);
                    gap: 8px;
                }}
                .secondary-stat-{div_id} {{
                    background: rgba(0, 0, 0, 0.2);
                    padding: 6px 10px;
                    border-radius: 6px;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    font-size: 11px;
                    border: 1px solid rgba(255,255,255,0.03);
                }}
                .secondary-stat-{div_id} span {{
                    color: #94a3b8;
                }}
                .secondary-stat-{div_id} strong {{
                    color: #f1f5f9;
                }}
            </style>
        </head>
        <body>
            <div class="stats-container-{div_id}" id="{div_id}"></div>
            
            <script>
            (function() {{
                const players = {data_json};
                const container = document.getElementById('{div_id}');
                
                const neonColors = [
                    '#3b82f6', '#ef4444', '#10b981', '#8b5cf6', '#f97316',
                    '#06b6d4', '#ec4899', '#84cc16', '#6366f1', '#14b8a6'
                ];
                
                players.forEach((player, index) => {{
                    const card = document.createElement('div');
                    card.className = 'player-card-{div_id}';
                    const accentColor = neonColors[index % neonColors.length];
                    card.style.setProperty('--accent-color', accentColor);
                    
                    card.innerHTML = `
                        <div class="player-rank-{div_id}">${{index + 1}}</div>
                        <div class="player-name-{div_id}">${{player.name}}</div>
                        
                        <div class="main-stats-{div_id}">
                            <div class="stat-item-{div_id}">
                                <span class="stat-value-{div_id}" style="color: ${{accentColor}}">${{player.runs}}</span>
                                <span class="stat-label-{div_id}">Runs</span>
                            </div>
                            <div class="stat-item-{div_id}">
                                <span class="stat-value-{div_id}">${{player.balls}}</span>
                                <span class="stat-label-{div_id}">Balls</span>
                            </div>
                            <div class="stat-item-{div_id}">
                                <span class="stat-value-{div_id}">${{player.sr.toFixed(1)}}</span>
                                <span class="stat-label-{div_id}">SR</span>
                            </div>
                        </div>

                        <div class="splits-{div_id}">
                            <div class="split-badge-{div_id}">
                                <span class="split-val-{div_id}">${{player.sr_pace.toFixed(1)}}</span>
                                <span class="split-lbl-{div_id}">⚡ vs Pace</span>
                            </div>
                            <div class="split-badge-{div_id}">
                                <span class="split-val-{div_id}">${{player.sr_spin.toFixed(1)}}</span>
                                <span class="split-lbl-{div_id}">🌀 vs Spin</span>
                            </div>
                            <div class="split-badge-{div_id}" style="background:rgba(245,158,11,0.1);border-color:rgba(245,158,11,0.3)">
                                <span class="split-val-{div_id}" style="color:#fbbf24">${{player.impact.toFixed(1)}}</span>
                                <span class="split-lbl-{div_id}">⭐ Impact</span>
                            </div>
                        </div>
                        
                        <div class="boundaries-{div_id}">
                            <div class="boundary-badge-{div_id}">
                                <span class="boundary-value-{div_id}">${{player.fours}}</span>
                                <span class="boundary-label-{div_id}">4s</span>
                            </div>
                            <div class="boundary-badge-{div_id}">
                                <span class="boundary-value-{div_id}">${{player.sixes}}</span>
                                <span class="boundary-label-{div_id}">6s</span>
                            </div>
                            <div class="boundary-badge-{div_id}">
                                <span class="boundary-value-{div_id}">${{player.highest}}</span>
                                <span class="boundary-label-{div_id}">HS</span>
                            </div>
                        </div>
                        
                        <div class="secondary-stats-{div_id}">
                            <div class="secondary-stat-{div_id}">
                                <span>Avg</span>
                                <strong>${{player.avg.toFixed(1)}}</strong>
                            </div>
                            <div class="secondary-stat-{div_id}">
                                <span>Out</span>
                                <strong>${{player.dismissals}}</strong>
                            </div>
                        </div>
                    `;
                    container.appendChild(card);
                }});
            }})();
            </script>
        </body>
        </html>
        """
        return html

    def render_bowler_stats_cards(stats_df, title):
        """Render bowler statistics cards with Economy, Dot Ball %, Best Figures & Impact Score"""
        if stats_df.empty:
            return "<p>No bowler statistics available</p>"
        div_id = f"bowler_stats_{hashlib.md5(title.encode()).hexdigest()[:8]}"
        bowlers_data = []
        for idx, row in stats_df.iterrows():
            bowlers_data.append({
                'name': str(row['bowler']),
                'wickets': int(row['wickets']),
                'balls': int(row['balls']),
                'econ': float(row['economy']),
                'avg': float(row['average']),
                'sr': float(row['strike_rate']),
                'dot_pct': float(row['dot_pct']),
                'best': str(row.get('best_figures', '-')),
                'impact': float(row.get('impact_score', 0))
            })
        
        data_json = json.dumps(bowlers_data)
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{
                    margin: 0;
                    padding: 0;
                    background: transparent;
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                }}
                .stats-container-{div_id} {{
                    display: grid;
                    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
                    gap: 16px;
                    padding: 15px;
                }}
                .player-card-{div_id} {{
                    background: rgba(15, 23, 42, 0.75);
                    backdrop-filter: blur(12px);
                    -webkit-backdrop-filter: blur(12px);
                    border: 1px solid rgba(255, 255, 255, 0.1);
                    border-radius: 12px;
                    padding: 16px;
                    color: #f8fafc;
                    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
                    transition: all 0.3s ease;
                    position: relative;
                    overflow: hidden;
                }}
                .player-card-{div_id}::before {{
                    content: '';
                    position: absolute;
                    top: 0; left: 0; right: 0;
                    height: 3px;
                    background: var(--accent-color, #10b981);
                }}
                .player-card-{div_id}:hover {{
                    transform: translateY(-5px);
                    box-shadow: 0 12px 40px rgba(0, 0, 0, 0.5), 0 0 15px var(--accent-color);
                    border-color: rgba(255, 255, 255, 0.2);
                }}
                .player-rank-{div_id} {{
                    position: absolute;
                    top: 12px;
                    right: 12px;
                    background: linear-gradient(135deg, rgba(255,255,255,0.1), rgba(255,255,255,0.05));
                    border: 1px solid rgba(255,255,255,0.2);
                    width: 30px;
                    height: 30px;
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-size: 14px;
                    font-weight: 700;
                    color: var(--accent-color);
                    box-shadow: 0 2px 10px rgba(0,0,0,0.2);
                }}
                .player-name-{div_id} {{
                    font-size: 17px;
                    font-weight: 700;
                    margin-bottom: 12px;
                    padding-right: 45px;
                    letter-spacing: 0.5px;
                    color: #ffffff;
                }}
                .main-stats-{div_id} {{
                    display: flex;
                    justify-content: space-between;
                    margin-bottom: 12px;
                    padding: 12px;
                    background: rgba(0, 0, 0, 0.3);
                    border-radius: 8px;
                    border: 1px solid rgba(255,255,255,0.05);
                }}
                .stat-item-{div_id} {{
                    text-align: center;
                }}
                .stat-value-{div_id} {{
                    font-size: 20px;
                    font-weight: 800;
                    display: block;
                    color: #10b981;
                }}
                .stat-label-{div_id} {{
                    font-size: 10px;
                    opacity: 0.7;
                    text-transform: uppercase;
                    letter-spacing: 1px;
                }}
                .splits-{div_id} {{
                    display: flex;
                    gap: 8px;
                    margin-bottom: 12px;
                }}
                .split-badge-{div_id} {{
                    flex: 1;
                    background: rgba(16, 185, 129, 0.12);
                    border: 1px solid rgba(16, 185, 129, 0.3);
                    padding: 6px 8px;
                    border-radius: 6px;
                    text-align: center;
                }}
                .split-val-{div_id} {{
                    font-size: 14px;
                    font-weight: 700;
                    display: block;
                    color: #34d399;
                }}
                .split-lbl-{div_id} {{
                    font-size: 9px;
                    color: #9ca3af;
                    text-transform: uppercase;
                }}
                .secondary-stats-{div_id} {{
                    display: grid;
                    grid-template-columns: repeat(2, 1fr);
                    gap: 8px;
                }}
                .secondary-stat-{div_id} {{
                    background: rgba(0, 0, 0, 0.2);
                    padding: 6px 10px;
                    border-radius: 6px;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    font-size: 11px;
                    border: 1px solid rgba(255,255,255,0.03);
                }}
                .secondary-stat-{div_id} span {{
                    color: #94a3b8;
                }}
                .secondary-stat-{div_id} strong {{
                    color: #f1f5f9;
                }}
            </style>
        </head>
        <body>
            <div class="stats-container-{div_id}" id="{div_id}"></div>
            
            <script>
            (function() {{
                const bowlers = {data_json};
                const container = document.getElementById('{div_id}');
                
                const neonColors = [
                    '#10b981', '#06b6d4', '#8b5cf6', '#3b82f6', '#f97316',
                    '#ec4899', '#84cc16', '#ef4444', '#6366f1', '#14b8a6'
                ];
                
                bowlers.forEach((b, index) => {{
                    const card = document.createElement('div');
                    card.className = 'player-card-{div_id}';
                    const accentColor = neonColors[index % neonColors.length];
                    card.style.setProperty('--accent-color', accentColor);
                    
                    card.innerHTML = `
                        <div class="player-rank-{div_id}">${{index + 1}}</div>
                        <div class="player-name-{div_id}">${{b.name}}</div>
                        
                        <div class="main-stats-{div_id}">
                            <div class="stat-item-{div_id}">
                                <span class="stat-value-{div_id}" style="color: ${{accentColor}}">${{b.wickets}}</span>
                                <span class="stat-label-{div_id}">Wickets</span>
                            </div>
                            <div class="stat-item-{div_id}">
                                <span class="stat-value-{div_id}">${{b.econ.toFixed(2)}}</span>
                                <span class="stat-label-{div_id}">Econ</span>
                            </div>
                            <div class="stat-item-{div_id}">
                                <span class="stat-value-{div_id}">${{b.dot_pct.toFixed(1)}}%</span>
                                <span class="stat-label-{div_id}">Dot%</span>
                            </div>
                        </div>
                        
                        <div class="splits-{div_id}">
                            <div class="split-badge-{div_id}">
                                <span class="split-val-{div_id}">${{b.best}}</span>
                                <span class="split-lbl-{div_id}">Best Fig</span>
                            </div>
                            <div class="split-badge-{div_id}" style="background:rgba(245,158,11,0.1);border-color:rgba(245,158,11,0.3)">
                                <span class="split-val-{div_id}" style="color:#fbbf24">${{b.impact.toFixed(1)}}</span>
                                <span class="split-lbl-{div_id}">⭐ Impact Rating</span>
                            </div>
                        </div>
                        
                        <div class="secondary-stats-{div_id}">
                            <div class="secondary-stat-{div_id}">
                                <span>Avg</span>
                                <strong>${{b.avg.toFixed(1)}}</strong>
                            </div>
                            <div class="secondary-stat-{div_id}">
                                <span>Bowl SR</span>
                                <strong>${{b.sr.toFixed(1)}}</strong>
                            </div>
                        </div>
                    `;
                    container.appendChild(card);
                }});
            }})();
            </script>
        </body>
        </html>
        """
        return html
    
    # -----------------------------------------------------------------------------
    # 4. Main Application
    # -----------------------------------------------------------------------------
    
    # ── Restore & Style Streamlit Side Panel ──────────────────────────────────
    st.markdown("""
    <style>
        /* Side Panel Drawer Styling */
        section[data-testid="stSidebar"] {
            background: linear-gradient(180deg, rgba(11, 15, 25, 0.98), rgba(17, 24, 39, 0.98)) !important;
            border-right: 2px solid rgba(56, 189, 248, 0.35) !important;
            backdrop-filter: blur(20px) !important;
            transition: margin-left 0.35s cubic-bezier(0.16, 1, 0.3, 1), transform 0.35s cubic-bezier(0.16, 1, 0.3, 1), width 0.35s ease !important;
        }
        /* Hide native Streamlit red collapse button */
        [data-testid="stSidebarCollapseButton"] {
            display: none !important;
            visibility: hidden !important;
            opacity: 0 !important;
            pointer-events: none !important;
        }
        /* Open Button when Side Panel is Collapsed */
        [data-testid="stSidebarCollapsedControl"] {
            display: flex !important;
            visibility: visible !important;
            position: fixed !important;
            top: 14px !important;
            left: 14px !important;
            z-index: 9999999 !important;
            background: linear-gradient(135deg, #0284c7, #4f46e5) !important;
            border: 1px solid rgba(56, 189, 248, 0.8) !important;
            border-radius: 10px !important;
            padding: 6px 12px !important;
            box-shadow: 0 0 18px rgba(56, 189, 248, 0.7) !important;
            pointer-events: auto !important;
            transition: all 0.2s ease !important;
        }
        [data-testid="stSidebarCollapsedControl"] button {
            color: #ffffff !important;
        }
        [data-testid="stSidebarCollapsedControl"]:hover {
            transform: scale(1.05) !important;
            box-shadow: 0 0 24px rgba(56, 189, 248, 0.9) !important;
        }
        section[data-testid="stSidebar"] .block-container {
            padding-top: 1.5rem !important;
            padding-bottom: 2rem !important;
        }
        /* Main dashboard 100% full screen expansion styling */
        section.main, .main, [data-testid="stMain"] {
            transition: margin-left 0.35s cubic-bezier(0.16, 1, 0.3, 1), width 0.35s cubic-bezier(0.16, 1, 0.3, 1), max-width 0.35s cubic-bezier(0.16, 1, 0.3, 1) !important;
        }
        .main .block-container {
            padding-top: 0.2rem !important;
            padding-left: 2rem !important;
            padding-right: 2rem !important;
            max-width: 100% !important;
            width: 100% !important;
        }
    </style>
    """, unsafe_allow_html=True)
    
    with st.spinner("Loading Data..."):
        df = load_data()

    # -------------------------------------------------------------------------
    # Venue boundary lookup (approximate boundary radii for major IPL venues)
    # -------------------------------------------------------------------------
    VENUE_BOUNDARIES = {
        'M Chinnaswamy Stadium': 63,
        'Chinnaswamy Stadium': 63,
        'Eden Gardens': 66,
        'Wankhede Stadium': 65,
        'MA Chidambaram Stadium': 65,
        'Chepauk': 65,
        'Arun Jaitley Stadium': 64,
        'Feroz Shah Kotla': 64,
        'Narendra Modi Stadium': 70,
        'Motera': 70,
        'Rajiv Gandhi International Stadium': 65,
        'Uppal': 65,
        'Punjab Cricket Association Stadium': 68,
        'IS Bindra Stadium': 68,
        'Sawai Mansingh Stadium': 65,
        'Holkar Cricket Stadium': 67,
        'Dr DY Patil Sports Academy': 65,
        'Brabourne Stadium': 62,
        'Ekana Cricket Stadium': 68,
        'Bharat Ratna Shri Atal Bihari Vajpayee Ekana Cricket Stadium': 68,
        'Maharashtra Cricket Association Stadium': 62,
        'Gahunje': 62,
        'Himachal Pradesh Cricket Association Stadium': 63,
        'Dharamsala': 63,
        'Barsapara Cricket Stadium': 65,
        'JSCA International Stadium Complex': 62,
        'Dubai International Cricket Stadium': 70,
        'Sharjah Cricket Stadium': 60,
        'Sheikh Zayed Stadium': 68,
        'Newlands': 65,
        'Kingsmead': 64,
        'SuperSport Park': 66,
        'St Georges Park': 64,
        'Buffalo Park': 63,
        'De Beers Diamond Oval': 62,
        'New Wanderers Stadium': 65,
        'Willowmoore Park': 63,
    }
    DEFAULT_BOUNDARY = 65

    def normalize_venue(raw_name):
        if pd.isna(raw_name):
            return None
        name = raw_name.split(',')[0].strip().replace('.', ' ')
        return name

    def get_venue_boundary(venue_name):
        norm = normalize_venue(venue_name)
        if not norm:
            return DEFAULT_BOUNDARY
        return VENUE_BOUNDARIES.get(norm, DEFAULT_BOUNDARY)

    def map_bowler_type_hp(bt):
        if not bt or bt == 'All Types':
            return None
        if isinstance(bt, list):
            return bt
        bt_lower = str(bt).lower().strip()
        if bt_lower == 'pace':
            return ['Right-Arm Pace', 'Left-Arm Pace']
        if bt_lower == 'spin':
            return ['Right-Arm Leg Spin', 'Right-Arm Off Spin', 'Left-Arm Orthodox', 'Left-Arm Wrist Spin']
        if 'right' in bt_lower and ('pace' in bt_lower or 'fast' in bt_lower or 'medium' in bt_lower or 'seam' in bt_lower):
            return 'Right-Arm Pace'
        if 'left' in bt_lower and ('pace' in bt_lower or 'fast' in bt_lower or 'medium' in bt_lower or 'seam' in bt_lower):
            return 'Left-Arm Pace'
        if 'off' in bt_lower or 'offbreak' in bt_lower:
            return 'Right-Arm Off Spin'
        if 'leg' in bt_lower or 'legbreak' in bt_lower:
            return 'Right-Arm Leg Spin'
        if 'orthodox' in bt_lower:
            return 'Left-Arm Orthodox'
        if 'wrist' in bt_lower or 'unorthodox' in bt_lower:
            return 'Left-Arm Wrist Spin'
        return bt

    # ── ADVANCED PRO HEADER & COMMAND CENTER ──────────────────────────────────
    _uname = st.session_state.get("username", "analyst")
    
    st.markdown(f"""
    <style>
    /* Pro Top Header */
    .pro-header-bar {{
        background: linear-gradient(135deg, rgba(11, 15, 25, 0.98), rgba(17, 24, 39, 0.98));
        border-bottom: 2px solid rgba(56, 189, 248, 0.3);
        padding: 14px 24px;
        margin-bottom: 14px;
        border-radius: 0 0 16px 16px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5);
    }}
    .pro-brand {{
        font-family: 'Orbitron', monospace;
        font-size: 20px;
        font-weight: 900;
        letter-spacing: 2px;
        background: linear-gradient(135deg, #38bdf8, #818cf8, #f093fb);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        display: flex;
        align-items: center;
        gap: 10px;
    }}
    .pro-badge {{
        font-size: 10px;
        font-weight: 900;
        background: linear-gradient(135deg, #ef4444, #f59e0b);
        color: #ffffff;
        padding: 2px 8px;
        border-radius: 6px;
        letter-spacing: 1px;
        vertical-align: middle;
        -webkit-text-fill-color: #ffffff;
    }}
    .pro-pill-chip {{
        background: rgba(30, 41, 59, 0.8);
        border: 1px solid rgba(56, 189, 248, 0.25);
        border-radius: 20px;
        padding: 5px 14px;
        font-size: 11px;
        font-weight: 600;
        color: #cbd5e1;
        display: inline-flex;
        align-items: center;
        gap: 6px;
    }}
    .vs-emblem-shield {{
        width: 48px;
        height: 48px;
        border-radius: 50%;
        background: linear-gradient(135deg, #1e1b4b, #311b92);
        border: 2px solid #818cf8;
        box-shadow: 0 0 24px rgba(129, 140, 248, 0.7);
        display: flex;
        align-items: center;
        justify-content: center;
        font-family: 'Orbitron', sans-serif;
        font-weight: 900;
        font-size: 15px;
        color: #ffffff;
        margin: 26px auto 0 auto;
    </style>
    """, unsafe_allow_html=True)

    # 1. Season Data Preparation
    if 'season' in df.columns:
        def parse_season_clean(val):
            if pd.isna(val):
                return np.nan
            val_str = str(val).split('/')[0].strip()
            try:
                v = int(float(val_str))
                return 2008 if v == 2007 else v
            except (ValueError, TypeError):
                return np.nan

        df['season'] = df['season'].apply(parse_season_clean)
        parsed_seasons = [int(s) for s in sorted(df['season'].dropna().unique()) if pd.notna(s)]
        # Ensure complete coverage from 2008 through 2026
        available_seasons = sorted(list(set(parsed_seasons + list(range(2008, 2027)))))
    else:
        available_seasons = list(range(2008, 2027))

    season_dropdown_options = ['All Seasons (2008-2026)'] + [str(s) for s in sorted(available_seasons, reverse=True)]

    col_h1, col_h2 = st.columns([3, 2])
    with col_h1:
        st.markdown("""
        <div class="pro-header-bar" style="margin-bottom:0;">
          <div class="pro-brand">
            🏏 IPL ANALYTICS
          </div>
          <div style="display:flex;align-items:center;gap:10px;">
            <div class="pro-pill-chip">⚡ TELEMETRY: <strong style="color:#38bdf8">295,759 BALLS</strong></div>
          </div>
        </div>
        """, unsafe_allow_html=True)

    with col_h2:
        top_selected_season = st.selectbox(
            "📅 Choose Season",
            options=season_dropdown_options,
            index=0,
            key="top_header_season_select"
        )

    ACTIVE_IPL_TEAMS = [
        'Chennai Super Kings',
        'Delhi Capitals',
        'Gujarat Titans',
        'Kolkata Knight Riders',
        'Lucknow Super Giants',
        'Mumbai Indians',
        'Punjab Kings',
        'Rajasthan Royals',
        'Royal Challengers Bengaluru',
        'Sunrisers Hyderabad'
    ]

    # ── Floating Open Side Panel Button on Main Dashboard ────────────────────────
    st.markdown("""
    <div id="floating-open-panel-container" style="position:fixed; top:14px; left:14px; z-index:9999999;">
      <button id="open-side-panel-btn" style="background:linear-gradient(135deg,#0284c7,#4f46e5); border:1px solid rgba(56,189,248,0.8); color:#ffffff; border-radius:10px; padding:8px 16px; font-family:'Orbitron',sans-serif; font-size:12px; font-weight:700; cursor:pointer; box-shadow:0 0 20px rgba(56,189,248,0.8); display:flex; align-items:center; gap:6px;">
        <span>☰</span> <span>PANEL CONTROLS</span>
      </button>
    </div>
    """, unsafe_allow_html=True)

    components.html("""
    <script>
    (function() {
        function getParentDoc() {
            try { return window.parent.document; } catch(e) { return document; }
        }

        function doToggle(action) {
            var pDoc = getParentDoc();
            var sidebar = pDoc.querySelector('section[data-testid="stSidebar"]');
            
            var expandBtn = pDoc.querySelector('button[aria-label*="Expand"]') || 
                              pDoc.querySelector('[data-testid="stSidebarCollapsedControl"] button') ||
                              pDoc.querySelector('[data-testid="stSidebarCollapsedControl"]');
            var collapseBtn = pDoc.querySelector('button[aria-label*="Collapse"]') || 
                                pDoc.querySelector('[data-testid="stSidebarCollapseButton"] button') ||
                                pDoc.querySelector('[data-testid="stSidebarCollapseButton"]');

            if (action === 'open' && expandBtn) {
                expandBtn.click();
            } else if (action === 'close' && collapseBtn) {
                collapseBtn.click();
            }

            if (sidebar) {
                var mainSection = pDoc.querySelector('section.main') || pDoc.querySelector('.main') || pDoc.querySelector('[data-testid="stMain"]');
                if (action === 'open') {
                    sidebar.setAttribute('aria-expanded', 'true');
                    sidebar.style.setProperty('display', 'block', 'important');
                    sidebar.style.setProperty('visibility', 'visible', 'important');
                    sidebar.style.setProperty('margin-left', '0px', 'important');
                    sidebar.style.setProperty('transform', 'translateX(0px)', 'important');
                    sidebar.style.setProperty('width', '320px', 'important');
                    sidebar.style.setProperty('min-width', '320px', 'important');

                    if (mainSection) {
                        mainSection.style.setProperty('margin-left', '320px', 'important');
                        mainSection.style.setProperty('width', 'calc(100% - 320px)', 'important');
                        mainSection.style.setProperty('max-width', 'calc(100% - 320px)', 'important');
                    }
                } else if (action === 'close') {
                    sidebar.setAttribute('aria-expanded', 'false');
                    sidebar.style.setProperty('margin-left', '-340px', 'important');
                    sidebar.style.setProperty('transform', 'translateX(-340px)', 'important');

                    if (mainSection) {
                        mainSection.style.setProperty('margin-left', '0px', 'important');
                        mainSection.style.setProperty('width', '100%', 'important');
                        mainSection.style.setProperty('max-width', '100%', 'important');
                    }
                }
            }
        }

        var pDoc = getParentDoc();
        pDoc.addEventListener('click', function(evt) {
            var openElem = evt.target.closest('#open-side-panel-btn') || evt.target.closest('#floating-open-panel-container');
            if (openElem) {
                evt.preventDefault();
                evt.stopPropagation();
                doToggle('open');
            }

            var closeElem = evt.target.closest('#close-side-panel-btn');
            if (closeElem) {
                evt.preventDefault();
                evt.stopPropagation();
                doToggle('close');
            }
        }, true);
    })();
    </script>
    """, height=0, width=0)

    # ── Side Panel Navigation Bar (st.sidebar) ──────────────────────────────────
    with st.sidebar:
        st.markdown("""
        <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:14px;">
          <div>
            <div style="font-family:'Orbitron',sans-serif; font-size:17px; font-weight:900; color:#38bdf8; letter-spacing:1.2px; text-transform:uppercase;">
              🏏 IPL ANALYTICS
            </div>
            <div style="font-size:11px; color:#94a3b8;">
              Performance Intelligence
            </div>
          </div>
          <button id="close-side-panel-btn" style="background:linear-gradient(135deg,rgba(239,68,68,0.85),rgba(220,38,38,0.95)); border:1px solid rgba(248,113,113,0.8); color:#ffffff; border-radius:8px; padding:6px 12px; font-family:'Inter',sans-serif; font-size:12px; font-weight:700; cursor:pointer; box-shadow:0 0 12px rgba(239,68,68,0.5); display:flex; align-items:center; gap:4px;">
            ✕ CLOSE
          </button>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("### ⚔️ MATCH SETUP")
        
        team_filter_mode = st.radio(
            "Franchise Selection Mode",
            ["Active 10 Teams", "All Franchises"],
            help="Filter team dropdowns to active 10 IPL franchises or include historical defunct franchises",
            key="side_team_filter_mode_radio"
        )

        available_teams = sorted([t for t in df['batting_team'].unique() if pd.notna(t)])
        if team_filter_mode == "Active 10 Teams":
            teams = [t for t in available_teams if t in ACTIVE_IPL_TEAMS]
            if not teams:
                teams = available_teams
        else:
            teams = available_teams

        if len(teams) < 2:
            st.error("⚠️ Not enough teams in selected data. Please adjust filters.")
            st.stop()

        team1 = st.selectbox("🟡 Team 1 (Primary Team)", teams, index=0, key="side_team1_select")
        
        st.markdown("""
        <div style="display:flex;align-items:center;justify-content:center;margin:8px 0;">
          <span style="font-family:'Orbitron',sans-serif;font-weight:900;font-size:14px;background:linear-gradient(135deg,#667eea,#f093fb);-webkit-background-clip:text;-webkit-text-fill-color:transparent;">─── VS ───</span>
        </div>
        """, unsafe_allow_html=True)

        team2_options = [t for t in teams if t != team1]
        if not team2_options:
            team2_options = teams
        team2 = st.selectbox("🔵 Team 2 (Comparison Team)", team2_options, index=0, key="side_team2_select")

        st.markdown("---")
        st.markdown("### 🎛️ TELEMETRY DECK")

        filter_mode = st.radio(
            "📅 Season Mode",
            ["All Seasons (2008-Present)", "Specific Season(s)"],
            key="side_season_filter_mode_radio"
        )
        if top_selected_season != 'All Seasons (2008-2026)':
            top_yr = int(top_selected_season)
            filtered_df = df[df['season'].astype('Int64') == top_yr]
            selected_seasons = [top_yr]
        elif filter_mode == "Specific Season(s)" and available_seasons:
            selected_seasons = st.multiselect(
                "Select Season(s)",
                options=available_seasons,
                default=[max(available_seasons)],
                format_func=lambda x: str(int(x)),
                key="side_multiselect_seasons"
            )
            if selected_seasons:
                sel_ints = [int(s) for s in selected_seasons]
                filtered_df = df[df['season'].astype('Int64').isin(sel_ints) | df['season'].isin(selected_seasons)]
            else:
                filtered_df = df
        else:
            filtered_df = df
            selected_seasons = []

        all_venues = ['All Venues']
        venue_list = sorted(df['venue'].dropna().unique()) if 'venue' in df.columns else []
        selected_venue = st.selectbox("🏟️ Stadium / Venue", all_venues + venue_list, key="side_venue_select_box")
        if selected_venue != 'All Venues':
            venue_boundary = get_venue_boundary(selected_venue)
            st.caption(f"🎯 Boundary: ~{venue_boundary}m")

        bowler_types = ['All Types', 'Right-Arm Pace', 'Left-Arm Pace', 'Right-Arm Leg Spin', 'Right-Arm Off Spin', 'Left-Arm Orthodox', 'Left-Arm Wrist Spin']
        bowler_type = st.selectbox("🎳 Bowler Type", bowler_types, key="side_bowler_type_select_box")

        phase_options = ['All Phases', 'Powerplay (1-6)', 'Middle (7-15)', 'Death (16-20)']
        selected_phase = st.selectbox("⏱️ Match Phase", phase_options, key="side_match_phase_select_box")
        phase_filter = None if selected_phase == 'All Phases' else selected_phase

        if hp and hp.has_data():
            use_hawkeye = st.toggle("📡 Hawk-Eye Telemetry", value=True, key="side_hawkeye_toggle_switch")
            if use_hawkeye:
                real_count = len(hp.df[hp.df['dataSource'] == 'hawkeye'])
                st.caption(f"✅ {real_count:,} Hawk-Eye Deliveries")
            else:
                st.caption("🟡 Standard Dataset Active")
        else:
            use_hawkeye = False

        st.markdown("---")
        st.markdown("### 🔑 AI API KEY CONFIG")
        current_key = st.session_state.get("gemini_api_key", os.environ.get("GEMINI_API_KEY", ""))
        user_api_key = st.text_input(
            "Gemini / OpenAI API Key",
            type="password",
            value=current_key,
            placeholder="Paste AIZaSy... key here",
            help="Paste your Google Gemini or OpenAI API key to power the AI Analyst Chatbot",
            key="sidebar_api_key_input"
        )
        if user_api_key:
            st.session_state["gemini_api_key"] = user_api_key.strip()
            os.environ["GEMINI_API_KEY"] = user_api_key.strip()
            st.caption("✅ Key saved & active for AI Chatbot!")
        else:
            st.caption("💡 Enter key to activate AI Assistant")

    df = filtered_df

    # Compact summary bar instead of large info block
    col_s1, col_s2, col_s3, col_s4 = st.columns(4)
    with col_s1:
        st.metric("📊 Total Matches", f"{df['match_id'].nunique():,}")
    with col_s2:
        st.metric("⚾ Total Balls", f"{len(df):,}")
    with col_s3:
        st.metric(f"🏏 {team1}", f"{len(df[df['batting_team'] == team1]):,} balls")
    with col_s4:
        st.metric(f"🏏 {team2}", f"{len(df[df['batting_team'] == team2]):,} balls")
    


    # =====================================================================
    # SECTION-BASED NAVIGATION (radio buttons — only active section renders)
    # =====================================================================
    sections_list = [
        "📊 Phase Analysis", "🎯 Pitch Maps & Wagon Wheel", "👤 Player Stats",
        "🎳 Bowling Analysis", "📊 Ball Tracking", "📈 Statistical Charts", "🎬 Animations",
        "🔮 Prediction"
    ]
    def _normalize_section(sec):
        if not sec:
            return None
        s = str(sec).lower().strip()
        if 'predict' in s or 'future' in s or 'winner' in s:
            return "🔮 Prediction"
        elif 'pitch' in s or 'wagon' in s or '3d' in s or 'wheel' in s:
            return "🎯 Pitch Maps & Wagon Wheel"
        elif 'phase' in s or 'powerplay' in s or 'death' in s:
            return "📊 Phase Analysis"
        elif 'player' in s or 'impact' in s:
            return "👤 Player Stats"
        elif 'bowling' in s or 'length' in s:
            return "🎳 Bowling Analysis"
        elif 'tracking' in s or 'ball' in s or 'hawkeye' in s:
            return "📊 Ball Tracking"
        elif 'chart' in s:
            return "📈 Statistical Charts"
        elif 'anim' in s:
            return "🎬 Animations"
        return sec

    query_section = st.query_params.get("section", None)
    normalized_target = _normalize_section(query_section)
    if normalized_target and normalized_target in sections_list:
        st.session_state["main_nav"] = normalized_target

    if "main_nav" in st.session_state:
        st.session_state["main_nav"] = _normalize_section(st.session_state["main_nav"])

    default_idx = 0
    if "main_nav" in st.session_state and st.session_state["main_nav"] in sections_list:
        default_idx = sections_list.index(st.session_state["main_nav"])
    else:
        st.session_state["main_nav"] = sections_list[0]
        default_idx = 0

    active_section = st.radio(
        "📌 Select Analysis Section",
        sections_list,
        index=default_idx,
        horizontal=True, key="main_nav"
    )
    st.markdown("---")
    
    # =====================================================================
    # SECTION 1: Phase Analysis
    # =====================================================================
    if active_section == "📊 Phase Analysis":
        st.markdown("## 📊 Phase Analysis & Tactical Intelligence")
        st.markdown(f"Comprehensive phase breakdown for **{team1}** vs **{team2}** across Powerplay (1-6), Middle (7-15), and Death (16-20) overs.")

        p_tab1, p_tab2, p_tab3, p_tab4, p_tab5 = st.tabs([
            "⚡ Phase Efficiency Matrix",
            "⚖️ 1st vs 2nd Innings Split",
            "🌀 Pace vs Spin by Phase",
            "📈 Over-by-Over Overlay Curve",
            "🌟 Phase Specialists"
        ])

        with p_tab1:
            st.markdown("### ⚡ Phase Efficiency & Risk Matrix")
            st.caption("Multi-panel comparison evaluating Run Rate, Dot Ball %, Boundary %, and Wickets lost per phase.")
            
            # Summary Metrics Bar
            comp_t1 = calculate_comprehensive_phase_stats(df, team1)
            comp_t2 = calculate_comprehensive_phase_stats(df, team2)

            m_col1, m_col2, m_col3, m_col4 = st.columns(4)
            with m_col1:
                st.metric(f"{team1} Overall RR", f"{comp_t1['run_rate'].mean():.2f}")
            with m_col2:
                st.metric(f"{team2} Overall RR", f"{comp_t2['run_rate'].mean():.2f}")
            with m_col3:
                st.metric(f"{team1} Death RR (16-20)", f"{comp_t1[comp_t1['phase']=='Death (16-20)']['run_rate'].values[0] if not comp_t1.empty else 0:.2f}")
            with m_col4:
                st.metric(f"{team2} Death RR (16-20)", f"{comp_t2[comp_t2['phase']=='Death (16-20)']['run_rate'].values[0] if not comp_t2.empty else 0:.2f}")

            fig_eff = create_phase_efficiency_matrix_chart(df, team1, team2)
            if fig_eff:
                st.plotly_chart(fig_eff, use_container_width=True)

            st.markdown("#### 📋 Detailed Phase Statistics Table")
            c_df1 = comp_t1.copy(); c_df1.insert(0, 'Team', team1)
            c_df2 = comp_t2.copy(); c_df2.insert(0, 'Team', team2)
            combined_phase_df = pd.concat([c_df1, c_df2], ignore_index=True)
            st.dataframe(combined_phase_df.rename(columns={
                'phase': 'Phase', 'runs': 'Runs', 'balls': 'Balls', 'wickets': 'Wickets',
                'run_rate': 'Run Rate', 'balls_per_wicket': 'Balls/Wkt',
                'dot_pct': 'Dot %', 'boundary_pct': 'Boundary %', 'efficiency_index': 'Efficiency Index'
            }), hide_index=True, use_container_width=True)

        with p_tab2:
            st.markdown("### ⚖️ 1st Innings (Setting Target) vs 2nd Innings (Chasing) Split")
            st.caption("Compare how run rates vary between target-setting and chasing across match phases.")
            fig_split = create_phase_innings_split_chart(df, team1, team2)
            if fig_split:
                st.plotly_chart(fig_split, use_container_width=True)

        with p_tab3:
            st.markdown("### 🌀 Pace vs Spin Performance by Phase")
            st.caption("Batting strike rate breakdown against pace vs spin across Powerplay, Middle, and Death overs.")
            fig_ps = create_phase_pace_vs_spin_chart(df, team1, team2)
            if fig_ps:
                st.plotly_chart(fig_ps, use_container_width=True)

        with p_tab4:
            st.markdown("### 📈 Over-by-Over Run Rate Progression Curve (Overs 1-20)")
            st.caption("Shaded phase zones: Powerplay (Overs 1-6, Green), Middle Overs (Overs 7-15, Blue), Death Overs (Overs 16-20, Red).")
            fig_worm = create_phase_overlay_worm_chart(df, team1, team2)
            if fig_worm:
                st.plotly_chart(fig_worm, use_container_width=True)

        with p_tab5:
            st.markdown("### 🌟 Phase Specialists Leaderboard")
            st.caption("Top performers specialized in Powerplay acceleration and Death overs execution.")
            
            s_col1, s_col2 = st.columns(2)
            with s_col1:
                st.markdown(f"**⚡ {team1} Powerplay & Death Specialists**")
                t1_pp = df[(df['batting_team'] == team1) & (df['phase'] == 'Powerplay (1-6)')].groupby('batter').agg({'runs_off_bat':'sum','ball':'count'}).reset_index()
                t1_pp = t1_pp[t1_pp['ball'] >= 20].assign(SR=lambda x: (x['runs_off_bat']/x['ball']*100).round(1)).sort_values('SR', ascending=False).head(5)
                st.markdown("*Top Powerplay Batters (Min 20 balls)*")
                st.dataframe(t1_pp.rename(columns={'batter': 'Batter', 'runs_off_bat': 'Runs', 'ball': 'Balls'}), hide_index=True, use_container_width=True)

                t1_death = df[(df['batting_team'] == team1) & (df['phase'] == 'Death (16-20)')].groupby('batter').agg({'runs_off_bat':'sum','ball':'count'}).reset_index()
                t1_death = t1_death[t1_death['ball'] >= 15].assign(SR=lambda x: (x['runs_off_bat']/x['ball']*100).round(1)).sort_values('SR', ascending=False).head(5)
                st.markdown("*Top Death Overs Finishers (Min 15 balls)*")
                st.dataframe(t1_death.rename(columns={'batter': 'Batter', 'runs_off_bat': 'Runs', 'ball': 'Balls'}), hide_index=True, use_container_width=True)

            with s_col2:
                st.markdown(f"**⚡ {team2} Powerplay & Death Specialists**")
                t2_pp = df[(df['batting_team'] == team2) & (df['phase'] == 'Powerplay (1-6)')].groupby('batter').agg({'runs_off_bat':'sum','ball':'count'}).reset_index()
                t2_pp = t2_pp[t2_pp['ball'] >= 20].assign(SR=lambda x: (x['runs_off_bat']/x['ball']*100).round(1)).sort_values('SR', ascending=False).head(5)
                st.markdown("*Top Powerplay Batters (Min 20 balls)*")
                st.dataframe(t2_pp.rename(columns={'batter': 'Batter', 'runs_off_bat': 'Runs', 'ball': 'Balls'}), hide_index=True, use_container_width=True)

                t2_death = df[(df['batting_team'] == team2) & (df['phase'] == 'Death (16-20)')].groupby('batter').agg({'runs_off_bat':'sum','ball':'count'}).reset_index()
                t2_death = t2_death[t2_death['ball'] >= 15].assign(SR=lambda x: (x['runs_off_bat']/x['ball']*100).round(1)).sort_values('SR', ascending=False).head(5)
                st.markdown("*Top Death Overs Finishers (Min 15 balls)*")
                st.dataframe(t2_death.rename(columns={'batter': 'Batter', 'runs_off_bat': 'Runs', 'ball': 'Balls'}), hide_index=True, use_container_width=True)
    
        # Matchup Analysis
        st.markdown("---")
        st.subheader(f"🎯 Player Matchups vs {bowler_type}")
        
        if bowler_type == 'All Types':
            st.markdown("#### 📊 Advanced Static Graph — Complete Bowler Type Matrix & Comparison")
            st.caption("Comprehensive analysis showing strike rates and performance metrics across all Pace and Spin bowler types.")
            
            m_tab1, m_tab2 = st.tabs([f"🏏 {team1} All Types Matchups", f"🏏 {team2} All Types Matchups"])
            with m_tab1:
                fig_m1 = create_advanced_player_matchup_all_types_chart(df, team1, phase=phase_filter)
                if fig_m1:
                    st.plotly_chart(fig_m1, use_container_width=True)
                else:
                    st.info(f"No matchup data available for {team1}")
            with m_tab2:
                fig_m2 = create_advanced_player_matchup_all_types_chart(df, team2, phase=phase_filter)
                if fig_m2:
                    st.plotly_chart(fig_m2, use_container_width=True)
                else:
                    st.info(f"No matchup data available for {team2}")
        else:
            c1, c2 = st.columns(2)
        
            with c1:
                st.markdown(f"**{team1} Top Batters vs {bowler_type}**")
                batters1_df = get_top_batters(df, team1, n=5)
                if not batters1_df.empty:
                    batters1 = batters1_df['batter'].tolist()
                    m1_data = []
                    for b in batters1:
                        s = calculate_player_matchup(df, b, bowler_type, team=team1)
                        if s: 
                            m1_data.append({'label': str(b), 'value': float(s['strike_rate']),
                                'balls': int(s['balls_faced']), 'runs': int(s['runs_scored']),
                                'dismissals': int(s['dismissals'])})
                    if m1_data:
                        components.html(render_threejs_chart(m1_data, 'bar_3d', f"{team1} vs {bowler_type}", 450, 400), height=450)
                        st.dataframe(pd.DataFrame(m1_data)[['label', 'runs', 'balls', 'value']].rename(
                            columns={'label': 'Player', 'runs': 'Runs', 'balls': 'Balls', 'value': 'Strike Rate'}), hide_index=True)
                    else:
                        st.info(f"No data for {team1} vs {bowler_type}")
                else:
                    st.warning(f"No batters found for {team1}")
        
            with c2:
                st.markdown(f"**{team2} Top Batters vs {bowler_type}**")
                batters2_df = get_top_batters(df, team2, n=5)
                if not batters2_df.empty:
                    batters2 = batters2_df['batter'].tolist()
                    m2_data = []
                    for b in batters2:
                        s = calculate_player_matchup(df, b, bowler_type, team=team2)
                        if s: 
                            m2_data.append({'label': str(b), 'value': float(s['strike_rate']),
                                'balls': int(s['balls_faced']), 'runs': int(s['runs_scored']),
                                'dismissals': int(s['dismissals'])})
                    if m2_data:
                        components.html(render_threejs_chart(m2_data, 'bar_3d', f"{team2} vs {bowler_type}", 450, 400), height=450)
                        st.dataframe(pd.DataFrame(m2_data)[['label', 'runs', 'balls', 'value']].rename(
                            columns={'label': 'Player', 'runs': 'Runs', 'balls': 'Balls', 'value': 'Strike Rate'}), hide_index=True)
                    else:
                        st.info(f"No data for {team2} vs {bowler_type}")
                else:
                    st.warning(f"No batters found for {team2}")
            
            with st.expander("📊 View Advanced Static Graph — All Bowler Types Matrix"):
                ex_tab1, ex_tab2 = st.tabs([f"🏏 {team1} Full Matrix", f"🏏 {team2} Full Matrix"])
                with ex_tab1:
                    fig_ex1 = create_advanced_player_matchup_all_types_chart(df, team1, phase=phase_filter)
                    if fig_ex1:
                        st.plotly_chart(fig_ex1, use_container_width=True)
                with ex_tab2:
                    fig_ex2 = create_advanced_player_matchup_all_types_chart(df, team2, phase=phase_filter)
                    if fig_ex2:
                        st.plotly_chart(fig_ex2, use_container_width=True)
    
        # Runs Distribution
        st.subheader("📈 Runs Distribution")
        d1, d2 = st.columns(2)
        
        import plotly.graph_objects as go
        
        def create_donut_chart(data_series, title, team_name):
            team_color = IPL_TEAM_COLORS.get(team_name, '#3b82f6')
            hex_c = team_color.lstrip('#')
            if len(hex_c) == 6:
                r, g, b = tuple(int(hex_c[i:i+2], 16) for i in (0, 2, 4))
            else:
                r, g, b = 59, 130, 246
                
            colors = {
                '0': f"rgba({r},{g},{b},0.15)",
                '1': f"rgba({r},{g},{b},0.35)",
                '2': f"rgba({r},{g},{b},0.55)",
                '3': f"rgba({r},{g},{b},0.70)",
                '4': f"rgba({r},{g},{b},0.85)",
                '6': f"rgba({r},{g},{b},1.0)"
            }
            labels = [str(k) for k in data_series.index]
            values = data_series.values
            marker_colors = [colors.get(l, '#94a3b8') for l in labels]
            
            # Map labels to human-readable names
            label_map = {'0': 'Dots (0)', '1': 'Singles (1)', '2': 'Twos (2)', '3': 'Threes (3)', '4': 'Fours (4)', '6': 'Sixes (6)'}
            display_labels = [label_map.get(l, f"{l} Runs") for l in labels]
            
            fig = go.Figure(data=[go.Pie(
                labels=display_labels,
                values=values,
                hole=0.55,
                marker=dict(colors=marker_colors, line=dict(color='#0f172a', width=2)),
                textposition='inside',
                textinfo='percent',
                hoverinfo='label+value+percent',
                hovertemplate="<b>%{label}</b><br>Count: %{value}<br>Share: %{percent}<extra></extra>"
            )])
            
            fig.update_layout(
                title=dict(text=f"<b>{title}</b>", x=0.5, font=dict(size=15, color='#f8fafc')),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#cbd5e1', family='Segoe UI'),
                showlegend=True,
                legend=dict(orientation="h", yanchor="top", y=-0.1, xanchor="center", x=0.5),
                margin=dict(t=50, b=40, l=20, r=20),
                height=350
            )
            # Add center text
            fig.add_annotation(
                text=f"Total<br><b>{sum(values)}</b>",
                x=0.5, y=0.5,
                font=dict(size=16, color='#f8fafc'),
                showarrow=False
            )
            return fig

        with d1:
            rd1 = df[df['batting_team'] == team1]['runs_off_bat'].value_counts().sort_index()
            st.plotly_chart(create_donut_chart(rd1, f"{team1} Runs Breakdown", team1), use_container_width=True)
            
        with d2:
            rd2 = df[df['batting_team'] == team2]['runs_off_bat'].value_counts().sort_index()
            st.plotly_chart(create_donut_chart(rd2, f"{team2} Runs Breakdown", team2), use_container_width=True)
    
    # =====================================================================
    # SECTION 2: Pitch Maps & Wagon Wheel
    # =====================================================================
    if active_section == "🎯 Pitch Maps & Wagon Wheel":
        phase_val = None if selected_phase == 'All Phases' else selected_phase

        # Innings Over-by-Over Timeline Slider Control
        st.markdown("### ⏳ Innings Over-by-Over Timeline Filter")
        t_col1, t_col2 = st.columns([3, 1])
        with t_col1:
            over_range_filter = st.slider(
                "Filter Trajectories & Pitch Maps by Overs",
                min_value=1.0, max_value=20.0, value=(1.0, 20.0), step=1.0,
                help="Slide to inspect ball trajectories over-by-over (e.g., Overs 1-6 for Powerplay, Overs 16-20 for Death)."
            )
        with t_col2:
            st.markdown(f"<div style='margin-top:28px;background:rgba(56,189,248,0.15);padding:8px 12px;border-radius:8px;border:1px solid #38bdf8;text-align:center;font-size:12px;color:#38bdf8'><b>Selected Range:</b> Overs {over_range_filter[0]:.0f} - {over_range_filter[1]:.0f}</div>", unsafe_allow_html=True)
    
        def map_bowler_type_hp(bt):
            if not bt or bt == 'All Types':
                return None
            if isinstance(bt, list):
                return bt
            bt_lower = str(bt).lower().strip()
            if bt_lower == 'pace':
                return ['Right-Arm Pace', 'Left-Arm Pace']
            if bt_lower == 'spin':
                return ['Right-Arm Leg Spin', 'Right-Arm Off Spin', 'Left-Arm Orthodox', 'Left-Arm Wrist Spin']
            if 'right' in bt_lower and ('pace' in bt_lower or 'fast' in bt_lower or 'medium' in bt_lower or 'seam' in bt_lower):
                return 'Right-Arm Pace'
            if 'left' in bt_lower and ('pace' in bt_lower or 'fast' in bt_lower or 'medium' in bt_lower or 'seam' in bt_lower):
                return 'Left-Arm Pace'
            if 'off' in bt_lower or 'offbreak' in bt_lower:
                return 'Right-Arm Off Spin'
            if 'leg' in bt_lower or 'legbreak' in bt_lower:
                return 'Right-Arm Leg Spin'
            if 'orthodox' in bt_lower:
                return 'Left-Arm Orthodox'
            if 'wrist' in bt_lower or 'unorthodox' in bt_lower:
                return 'Left-Arm Wrist Spin'
            return bt
        
        # Helper: filter deliveries so ONLY batters from target_team and bowlers from opp_team (if provided) are included
        def filter_by_team_squad(data_list, target_team, opp_team=None):
            return data_list

        # Helper: get pitch data — filters by source & venue so toggle & venue show accurate real Hawk-Eye data
        def get_pitch_data(team, opp_team=None):
            if not hp or not hp.has_data():
                return [], "No Data"
            src = 'hawkeye' if use_hawkeye else None
            label = "Hawk-Eye (real)" if use_hawkeye else "Real & Simulated"
            bt_hp = map_bowler_type_hp(bowler_type)
            vn = selected_venue if selected_venue != 'All Venues' else None
            
            kwargs = {'team': team, 'opp_team': opp_team, 'bowler_type': bt_hp, 'phase': phase_val, 'source': src, 'venue': vn, 'over_range': over_range_filter}
            try:
                pd = hp.get_pitch_map_data(**kwargs)
            except TypeError:
                pd = hp.get_pitch_map_data(team=team, bowler_type=bt_hp, phase=phase_val)
            if pd:
                return pd, label
            return [], label + " (empty)"
        
        def get_wagon_data(team, opp_team=None):
            if not hp or not hp.has_data():
                return [], "No Data", DEFAULT_BOUNDARY
            src = 'hawkeye' if use_hawkeye else None
            label = "Hawk-Eye (real)" if use_hawkeye else "Real & Simulated"
            bt_hp = map_bowler_type_hp(bowler_type)
            bw = get_venue_boundary(selected_venue) if selected_venue != 'All Venues' else DEFAULT_BOUNDARY
            vn = selected_venue if selected_venue != 'All Venues' else None
            
            kwargs = {'team': team, 'opp_team': opp_team, 'bowler_type': bt_hp, 'phase': phase_val, 'source': src, 'venue': vn, 'boundary_radius': bw, 'over_range': over_range_filter}
            try:
                wd = hp.get_wagon_wheel_data(**kwargs)
            except TypeError:
                wd = hp.get_wagon_wheel_data(team=team, bowler_type=bt_hp, phase=phase_val)
            if wd:
                return wd, label, bw
            return [], label + " (empty)", bw
            
        def get_stumps_data(team, opp_team=None):
            if not hp or not hp.has_data():
                return [], "No Data"
            src = 'hawkeye' if use_hawkeye else None
            label = "Hawk-Eye (real)" if use_hawkeye else "Real & Simulated"
            bt_hp = map_bowler_type_hp(bowler_type)
            vn = selected_venue if selected_venue != 'All Venues' else None
            kwargs = {'team': team, 'opp_team': opp_team, 'bowler_type': bt_hp, 'phase': phase_val, 'source': src, 'venue': vn, 'over_range': over_range_filter}
            try:
                sd = hp.get_stumps_view_data(**kwargs)
            except Exception:
                sd = None
            if sd:
                return sd, label
            return [], label + " (empty)"
    
        st.subheader("🎯 Advanced Pitch Maps - Multi-Panel Analysis")
        st.markdown("_4-panel view: Wickets, Hitting, Density Heat Map, and Combined (2×2 grid)_")
        st.markdown(f"### {team1} - Advanced Pitch Analysis")
        pitch_data1, pd_src1 = get_pitch_data(team1, opp_team=team2)
        if pitch_data1:
            is_real1 = 'Hawk-Eye' in pd_src1
            source_tag1 = f'<span style="background:#22c55e;color:#000;padding:2px 8px;border-radius:4px;font-size:11px;font-weight:700">REAL: {pd_src1}</span>' if is_real1 else f'<span style="background:#f59e0b;color:#000;padding:2px 8px;border-radius:4px;font-size:11px;font-weight:700">SIMULATED: {pd_src1}</span>'
            st.markdown(f"<div style='display:flex;gap:8px;align-items:center;margin-bottom:8px'>{source_tag1}<span style='color:#94a3b8;font-size:12px'>Deliveries: {len(pitch_data1)} | Wickets: {sum(1 for d in pitch_data1 if d['wicket'] == 1)}</span></div>", unsafe_allow_html=True)
            components.html(render_advanced_pitch_viz(pitch_data1, f"{team1} - {selected_phase}", 1200, 900), height=960)
        else:
            st.info(f"No data available for {team1}")
        st.markdown(f"### {team2} - Advanced Pitch Analysis")
        pitch_data2, pd_src2 = get_pitch_data(team2, opp_team=team1)
        if pitch_data2:
            is_real2 = 'Hawk-Eye' in pd_src2
            source_tag2 = f'<span style="background:#22c55e;color:#000;padding:2px 8px;border-radius:4px;font-size:11px;font-weight:700">REAL: {pd_src2}</span>' if is_real2 else f'<span style="background:#f59e0b;color:#000;padding:2px 8px;border-radius:4px;font-size:11px;font-weight:700">SIMULATED: {pd_src2}</span>'
            st.markdown(f"<div style='display:flex;gap:8px;align-items:center;margin-bottom:8px'>{source_tag2}<span style='color:#94a3b8;font-size:12px'>Deliveries: {len(pitch_data2)} | Wickets: {sum(1 for d in pitch_data2 if d['wicket'] == 1)}</span></div>", unsafe_allow_html=True)
            components.html(render_advanced_pitch_viz(pitch_data2, f"{team2} - {selected_phase}", 1200, 900), height=960)
        else:
            st.info(f"No data available for {team2}")
    
        # Stumps View
        st.markdown("---")
        st.subheader("🎯 Stumps View - Line & Length Analysis")
        sv1, sv2 = st.columns(2)
        with sv1:
            st.markdown(f"**{team1} Stumps View**")
            stumps_data1, sd_src1 = get_stumps_data(team1, opp_team=team2)
            if stumps_data1:
                is_real_sd1 = 'Hawk-Eye' in sd_src1
                tag_sd1 = f'<span style="background:#22c55e;color:#000;padding:2px 8px;border-radius:4px;font-size:11px;font-weight:700">REAL: {sd_src1}</span>' if is_real_sd1 else f'<span style="background:#f59e0b;color:#000;padding:2px 8px;border-radius:4px;font-size:11px;font-weight:700">SIMULATED: {sd_src1}</span>'
                st.markdown(f"<div style='display:flex;gap:8px;align-items:center;margin-bottom:8px'>{tag_sd1}<span style='color:#94a3b8;font-size:12px'>Deliveries: {len(stumps_data1)}</span></div>", unsafe_allow_html=True)
                components.html(render_stumps_view(stumps_data1, f"{team1} - {selected_phase}", 500, 600), height=650)
            else:
                if use_hawkeye and team1 in ['Gujarat Titans', 'Lucknow Super Giants']:
                    st.info(f"ℹ️ No real Hawk-Eye tracking data is available for {team1} (Real tracking dataset covers 2009–2021; {team1} entered IPL in 2022). Switch off 'Hawk-Eye (Real Only)' to view 2022+ tracking data.")
                else:
                    st.info(f"No data available for {team1} under current filters.")
        with sv2:
            st.markdown(f"**{team2} Stumps View**")
            stumps_data2, sd_src2 = get_stumps_data(team2, opp_team=team1)
            if stumps_data2:
                is_real_sd2 = 'Hawk-Eye' in sd_src2
                tag_sd2 = f'<span style="background:#22c55e;color:#000;padding:2px 8px;border-radius:4px;font-size:11px;font-weight:700">REAL: {sd_src2}</span>' if is_real_sd2 else f'<span style="background:#f59e0b;color:#000;padding:2px 8px;border-radius:4px;font-size:11px;font-weight:700">SIMULATED: {sd_src2}</span>'
                st.markdown(f"<div style='display:flex;gap:8px;align-items:center;margin-bottom:8px'>{tag_sd2}<span style='color:#94a3b8;font-size:12px'>Deliveries: {len(stumps_data2)}</span></div>", unsafe_allow_html=True)
                components.html(render_stumps_view(stumps_data2, f"{team2} - {selected_phase}", 500, 600), height=650)
            else:
                if use_hawkeye and team2 in ['Gujarat Titans', 'Lucknow Super Giants']:
                    st.info(f"ℹ️ No real Hawk-Eye tracking data is available for {team2} (Real tracking dataset covers 2009–2021; {team2} entered IPL in 2022). Switch off 'Hawk-Eye (Real Only)' to view 2022+ tracking data.")
                else:
                    st.info(f"No data available for {team2} under current filters.")
    
        # Wagon Wheel
        st.markdown("---")
        st.subheader("⚾ Wagon Wheel - Shot Directions & Scoring Zones")
        ww1, ww2 = st.columns(2)
        with ww1:
            st.markdown(f"**{team1} Wagon Wheel**")
            wagon_data1, ww_src1, ww_bw1 = get_wagon_data(team1, opp_team=team2)
            if wagon_data1:
                is_real_w1 = 'Hawk-Eye' in ww_src1
                ww_tag1 = f'<span style="background:#22c55e;color:#000;padding:2px 8px;border-radius:4px;font-size:11px;font-weight:700">REAL: {ww_src1}</span>' if is_real_w1 else f'<span style="background:#f59e0b;color:#000;padding:2px 8px;border-radius:4px;font-size:11px;font-weight:700">SIMULATED: {ww_src1}</span>'
                st.markdown(f"<div style='display:flex;gap:8px;align-items:center;margin-bottom:8px'>{ww_tag1}<span style='color:#94a3b8;font-size:12px'>Scoring shots: {len(wagon_data1)} | Boundary: ~{ww_bw1}m</span></div>", unsafe_allow_html=True)
                components.html(render_wagon_wheel(wagon_data1, f"{team1} - {selected_phase}", 600, 600, boundary_radius=ww_bw1), height=650)
                
                # Render 360° Polar Sector Radar Chart (Static Version)
                fig_polar1 = create_polar_sector_radar_chart(wagon_data1, f"{team1} Sector Distribution", team1)
                if fig_polar1:
                    st.plotly_chart(fig_polar1, use_container_width=True, config={'displayModeBar': False, 'scrollZoom': False})
            else:
                if use_hawkeye and team1 in ['Gujarat Titans', 'Lucknow Super Giants']:
                    st.info(f"ℹ️ No real Hawk-Eye tracking data is available for {team1} (Real tracking dataset covers 2009–2021; {team1} entered IPL in 2022). Switch off 'Hawk-Eye (Real Only)' to view 2022+ tracking data.")
                else:
                    st.info(f"No data available for {team1} under current filters.")
        with ww2:
            st.markdown(f"**{team2} Wagon Wheel**")
            wagon_data2, ww_src2, ww_bw2 = get_wagon_data(team2, opp_team=team1)
            if wagon_data2:
                is_real_w2 = 'Hawk-Eye' in ww_src2
                ww_tag2 = f'<span style="background:#22c55e;color:#000;padding:2px 8px;border-radius:4px;font-size:11px;font-weight:700">REAL: {ww_src2}</span>' if is_real_w2 else f'<span style="background:#f59e0b;color:#000;padding:2px 8px;border-radius:4px;font-size:11px;font-weight:700">SIMULATED: {ww_src2}</span>'
                st.markdown(f"<div style='display:flex;gap:8px;align-items:center;margin-bottom:8px'>{ww_tag2}<span style='color:#94a3b8;font-size:12px'>Scoring shots: {len(wagon_data2)} | Boundary: ~{ww_bw2}m</span></div>", unsafe_allow_html=True)
                components.html(render_wagon_wheel(wagon_data2, f"{team2} - {selected_phase}", 600, 600, boundary_radius=ww_bw2), height=650)
                
                # Render 360° Polar Sector Radar Chart (Static Version)
                fig_polar2 = create_polar_sector_radar_chart(wagon_data2, f"{team2} Sector Distribution", team2)
                if fig_polar2:
                    st.plotly_chart(fig_polar2, use_container_width=True, config={'displayModeBar': False, 'scrollZoom': False})
            else:
                if use_hawkeye and team2 in ['Gujarat Titans', 'Lucknow Super Giants']:
                    st.info(f"ℹ️ No real Hawk-Eye tracking data is available for {team2} (Real tracking dataset covers 2009–2021; {team2} entered IPL in 2022). Switch off 'Hawk-Eye (Real Only)' to view 2022+ tracking data.")
                else:
                    st.info(f"No data available for {team2} under current filters.")
    
        # Venue-specific stats
        st.markdown("---")
        venue_header = f"🏟️ Venue-Specific Performance: {selected_venue}" if selected_venue != 'All Venues' else "🏟️ All Venues Performance Analysis"
        st.subheader(venue_header)
        
        venue_df = filtered_df.copy()
        if selected_venue != 'All Venues':
            venue_df = venue_df[venue_df['venue'] == selected_venue]
        
        if 'venue' in venue_df.columns and not venue_df.empty:
            venue_scope = st.radio(
                "Select Venue Analysis Scope:",
                [f"⚔️ Matchup Only ({team1} vs {team2} Head-to-Head)", f"🌐 Overall Team Records at Venue ({team1} & {team2} vs All Opponents)"],
                horizontal=True,
                key="venue_scope_toggle"
            )
            
            if "Matchup Only" in venue_scope:
                v_calc_df = venue_df[
                    ((venue_df['batting_team'] == team1) & (venue_df['bowling_team'] == team2)) |
                    ((venue_df['batting_team'] == team2) & (venue_df['bowling_team'] == team1))
                ]
            else:
                v_calc_df = venue_df[venue_df['batting_team'].isin([team1, team2])]

            col_v1, col_v2, col_v3, col_v4 = st.columns(4)
            with col_v1:
                v_runs = int(v_calc_df['total_runs'].sum()) if 'total_runs' in v_calc_df.columns else int(v_calc_df['runs_off_bat'].sum())
                st.metric("Total Runs", f"{v_runs:,}")
            with col_v2:
                v_boundaries = int(((v_calc_df['runs_off_bat'] == 4) | (v_calc_df['runs_off_bat'] == 6)).sum())
                st.metric("Boundaries (4s+6s)", f"{v_boundaries:,}")
            with col_v3:
                v_wickets = int(v_calc_df['is_wicket'].sum() if 'is_wicket' in v_calc_df.columns else 0)
                st.metric("Wickets", f"{v_wickets:,}")
            with col_v4:
                v_matches = v_calc_df['match_id'].nunique() if 'match_id' in v_calc_df.columns else 0
                st.metric("Matches", f"{v_matches:,}")
            
            st.markdown("#### Team Performance at Venue (Per-Innings)")

            v_teams_data = []
            
            for vt in [team1, team2]:
                vtd = v_calc_df[v_calc_df['batting_team'] == vt]
                if len(vtd) == 0:
                    continue
                
                # 1. Raw Totals per Team
                matches = vtd['match_id'].nunique()
                innings_count = vtd[['match_id', 'innings']].drop_duplicates().shape[0] if 'innings' in vtd.columns else matches
                
                total_runs = int(vtd['total_runs'].sum()) if 'total_runs' in vtd.columns else int(vtd['runs_off_bat'].sum()) + int(vtd.get('extras', pd.Series([0]*len(vtd))).sum())
                runs_bat = int(vtd['runs_off_bat'].sum())
                
                if 'legal_ball' in vtd.columns:
                    legal_balls = int(vtd['legal_ball'].sum())
                elif 'wides' in vtd.columns and 'noballs' in vtd.columns:
                    legal_balls = int(((vtd['wides'] == 0) & (vtd['noballs'] == 0)).sum())
                else:
                    legal_balls = len(vtd)
                
                fours = int((vtd['runs_off_bat'] == 4).sum())
                sixes = int((vtd['runs_off_bat'] == 6).sum())
                wickets = int(vtd['is_wicket'].sum()) if 'is_wicket' in vtd.columns else 0
                
                if 'dot_ball' in vtd.columns:
                    dot_balls = int(vtd['dot_ball'].sum())
                elif 'wides' in vtd.columns and 'noballs' in vtd.columns:
                    dot_balls = int(((vtd['runs_off_bat'] == 0) & (vtd['wides'] == 0) & (vtd['noballs'] == 0)).sum())
                else:
                    dot_balls = int((vtd['runs_off_bat'] == 0).sum())
                
                # 2. Derived Metrics
                avg_runs = round(total_runs / innings_count, 1) if innings_count else 0
                rr = round(total_runs / legal_balls * 6, 2) if legal_balls else 0
                sr = round(total_runs / legal_balls * 100, 1) if legal_balls else 0
                avg_4s = round(fours / innings_count, 1) if innings_count else 0
                avg_6s = round(sixes / innings_count, 1) if innings_count else 0
                avg_w = round(wickets / innings_count, 1) if innings_count else 0
                
                boundary_runs = (4 * fours) + (6 * sixes)
                bd_pct = round(boundary_runs / total_runs * 100, 1) if total_runs else 0
                dot_pct = round(dot_balls / legal_balls * 100, 1) if legal_balls else 0
                
                v_teams_data.append({
                    'Team': vt,
                    'Matches': matches,
                    'Innings': innings_count,
                    'Avg Runs': avg_runs,
                    'RR': rr,
                    'Avg SR': sr,
                    'Avg 4s': avg_4s,
                    'Avg 6s': avg_6s,
                    'Avg Wkts': avg_w,
                    'Boundary%': bd_pct,
                    'Dot Ball%': dot_pct,
                })
            
            if v_teams_data:
                v_df = pd.DataFrame(v_teams_data)
                
                styled = v_df.style \
                    .format({
                        'Avg Runs': '{:.1f}', 'RR': '{:.2f}', 'Avg SR': '{:.1f}',
                        'Avg 4s': '{:.1f}', 'Avg 6s': '{:.1f}', 'Avg Wkts': '{:.1f}',
                        'Boundary%': '{:.1f}%', 'Dot Ball%': '{:.1f}%',
                    }) \
                    .set_table_styles([
                        {'selector': 'thead th', 'props': [('background', '#1a1a2e'), ('color', '#e0e0e0'), ('padding', '8px 12px'), ('font-size', '13px'), ('text-align', 'center')]},
                        {'selector': 'tbody td', 'props': [('padding', '6px 12px'), ('text-align', 'center'), ('font-size', '13px')]},
                        {'selector': 'tbody tr:nth-child(even)', 'props': [('background', '#16213e')]},
                        {'selector': 'tbody tr:nth-child(odd)', 'props': [('background', '#1a1a2e')]},
                        {'selector': '', 'props': [('background', '#0f3460'), ('color', '#e0e0e0'), ('border', 'none'), ('border-radius', '8px'), ('overflow', 'hidden')]},
                    ])
                
                st.dataframe(styled, hide_index=True, use_container_width=True)
                
                # Tooltip legend
                st.markdown("""
                <div style="font-size:12px;color:#94a3b8;margin-top:4px;line-height:1.6">
                <b>Derived Metrics:</b>
                Avg Runs = Total Runs ÷ Innings &nbsp;|&nbsp;
                RR = (Total Runs ÷ Legal Balls) × 6 &nbsp;|&nbsp;
                SR = (Total Runs ÷ Legal Balls) × 100 &nbsp;|&nbsp;
                Avg 4s/6s = Fours/Sixes ÷ Innings &nbsp;|&nbsp;
                Avg Wkts = Wickets ÷ Innings &nbsp;|&nbsp;
                Boundary% = (4×Fours + 6×Sixes) ÷ Total Runs × 100 &nbsp;|&nbsp;
                Dot Ball% = Dot Balls ÷ Legal Balls × 100
                </div>
                """, unsafe_allow_html=True)
            
            # Top scorers at this venue (season filter respected)
            st.markdown("#### Top Batters at This Venue")
            v_batters = venue_df.groupby('striker').agg(
                Runs=('runs_off_bat', 'sum'),
                Balls=('runs_off_bat', 'count'),
                Fours=('runs_off_bat', lambda x: (x == 4).sum()),
                Sixes=('runs_off_bat', lambda x: (x == 6).sum()),
            ).reset_index().sort_values('Runs', ascending=False).head(10)
            v_batters['SR'] = (v_batters['Runs'] / v_batters['Balls'] * 100).round(1)
            st.dataframe(v_batters, hide_index=True, use_container_width=True)
        else:
            st.info("Venue data not available in current dataset")
    
    # =====================================================================
    # SECTION 3: Player Stats
    # =====================================================================
    if active_section == "👤 Player Stats":
        st.markdown("## 📊 Player Statistics - Top Performers")

        # Head-to-Head Copilot Comparison Card & Interactive Plotly Visualizer
        if "copilot_last_report" in st.session_state and st.session_state["copilot_last_report"]:
            st.markdown("### ⚔️ Live Player Comparison Telemetry")
            st.markdown(
                f"""
                <div style="background: linear-gradient(135deg, rgba(30,41,59,0.9), rgba(15,23,42,0.9)); border: 1px solid rgba(56,189,248,0.4); border-left: 5px solid #38bdf8; border-radius: 12px; padding: 18px 22px; margin-bottom: 20px; color: #f8fafc; font-family: sans-serif; box-shadow: 0 8px 32px rgba(0,0,0,0.3);">
                    {st.session_state["copilot_last_report"]}
                </div>
                """,
                unsafe_allow_html=True
            )

            if "copilot_p1_stats" in st.session_state and st.session_state["copilot_p1_stats"]:
                p1 = st.session_state["copilot_p1_stats"]
                p2 = st.session_state["copilot_p2_stats"]

                c1, c2, c3, c4 = st.columns(4)
                with c1:
                    st.metric(f"📊 {p1['name']} Total Runs", f"{p1['runs']:,}", f"{p1['sr']} SR")
                with c2:
                    st.metric(f"📊 {p2['name']} Total Runs", f"{p2['runs']:,}", f"{p2['sr']} SR")
                with c3:
                    st.metric(f"💥 {p1['name']} Boundaries", f"{p1['fours']} 4s | {p1['sixes']} 6s")
                with c4:
                    st.metric(f"💥 {p2['name']} Boundaries", f"{p2['fours']} 4s | {p2['sixes']} 6s")

                import plotly.graph_objects as go
                fig_comp = go.Figure()
                metrics_keys = ['runs', 'sr', 'avg', 'fours', 'sixes']
                metrics_labels = ['Total Runs', 'Strike Rate', 'Batting Avg', 'Fours (4s)', 'Sixes (6s)']

                fig_comp.add_trace(go.Bar(
                    x=metrics_labels,
                    y=[p1[k] for k in metrics_keys],
                    name=p1['name'],
                    marker_color='#38bdf8',
                    text=[p1[k] for k in metrics_keys],
                    textposition='auto'
                ))
                fig_comp.add_trace(go.Bar(
                    x=metrics_labels,
                    y=[p2[k] for k in metrics_keys],
                    name=p2['name'],
                    marker_color='#818cf8',
                    text=[p2[k] for k in metrics_keys],
                    textposition='auto'
                ))
                fig_comp.update_layout(
                    barmode='group',
                    title=f"<b>📊 {p1['name']} vs {p2['name']} Side-by-Side Graphical Metric Comparison</b>",
                    paper_bgcolor='rgba(15, 23, 42, 0)',
                    plot_bgcolor='rgba(15, 23, 42, 0)',
                    font=dict(color='#e2e8f0'),
                    height=450,
                    legend=dict(orientation="h", y=1.1, x=0.3)
                )
                fig_comp.update_xaxes(showgrid=False, tickfont=dict(color='#cbd5e1'))
                fig_comp.update_yaxes(showgrid=True, gridcolor='rgba(255,255,255,0.05)', tickfont=dict(color='#94a3b8'))
                st.plotly_chart(fig_comp, use_container_width=True)
            st.markdown("---")
        
        phase_val = None if selected_phase == 'All Phases' else selected_phase
        
        tab_bat, tab_bowl = st.tabs(["🏏 Top Batters", "🎳 Top Bowlers / Wicket-Takers"])
        
        with tab_bat:
            st.markdown(f"### {team1} - Top Batters")
            stats1 = get_player_statistics(df, team1, phase=phase_val)
            if not stats1.empty:
                components.html(render_player_stats_cards(stats1, f"{team1}_bat"), height=650, scrolling=True)
                st.caption(f"📈 Showing top {len(stats1)} batters with Pace/Spin splits & ⭐ Impact Rating")
            else:
                st.info(f"No player statistics available for {team1}")
            st.markdown(f"### {team2} - Top Batters")
            stats2 = get_player_statistics(df, team2, phase=phase_val)
            if not stats2.empty:
                components.html(render_player_stats_cards(stats2, f"{team2}_bat"), height=650, scrolling=True)
                st.caption(f"📈 Showing top {len(stats2)} batters with Pace/Spin splits & ⭐ Impact Rating")
            else:
                st.info(f"No player statistics available for {team2}")

        with tab_bowl:
            st.markdown(f"### {team1} - Top Bowlers")
            bw_stats1 = get_bowler_statistics(df, team1, phase=phase_val)
            if not bw_stats1.empty:
                components.html(render_bowler_stats_cards(bw_stats1, f"{team1}_bowl"), height=650, scrolling=True)
                st.caption(f"🎳 Showing top {len(bw_stats1)} bowlers with Economy, Dot Ball %, Best Figures & ⭐ Impact Rating")
            else:
                st.info(f"No bowler statistics available for {team1}")
            st.markdown(f"### {team2} - Top Bowlers")
            bw_stats2 = get_bowler_statistics(df, team2, phase=phase_val)
            if not bw_stats2.empty:
                components.html(render_bowler_stats_cards(bw_stats2, f"{team2}_bowl"), height=650, scrolling=True)
                st.caption(f"🎳 Showing top {len(bw_stats2)} bowlers with Economy, Dot Ball %, Best Figures & ⭐ Impact Rating")
            else:
                st.info(f"No bowler statistics available for {team2}")
    
    # =====================================================================
    # SECTION 4: Bowling Analysis
    # =====================================================================
    if active_section == "🎳 Bowling Analysis":
        phase_val = None if selected_phase == 'All Phases' else selected_phase
        bt_label = f" vs {bowler_type}" if bowler_type and bowler_type != 'All Types' else ""
        st.markdown(f"## 🎳 Bowling Length Analysis - Real-World Pitch Zones{bt_label}")
        st.caption("⚡ Live metrics derived from real Hawk-Eye delivery tracking coordinates")

        hp_real = None
        if HAWKEYE_AVAILABLE:
            try:
                hp_real = get_hawkeye_processor()
                if not hp_real.has_data():
                    hp_real = None
            except Exception:
                hp_real = None

        bt_hp = map_bowler_type_hp(bowler_type)
        vn = selected_venue if selected_venue != 'All Venues' else None

        def get_real_pitch_data(team, opp_team=None):
            if hp_real is None:
                return None
            src_filter = 'hawkeye' if use_hawkeye else None
            kwargs = {'team': team, 'opp_team': opp_team, 'bowler_type': bt_hp, 'phase': phase_val, 'source': src_filter, 'venue': vn}
            try:
                raw = hp_real.get_pitch_map_data(**kwargs)
            except Exception:
                raw = None
            return raw

        def render_zone_kpis(pitch_data, team_name):
            if not pitch_data:
                st.info(f"No pitch data available for {team_name}")
                return
            total = len(pitch_data)
            yorkers = [d for d in pitch_data if 0 <= d['y'] < 2]
            fulls = [d for d in pitch_data if 2 <= d['y'] < 6]
            lengths = [d for d in pitch_data if 6 <= d['y'] < 12]
            shorts = [d for d in pitch_data if 12 <= d['y'] <= 22]

            def calc_z(z_list):
                if not z_list:
                    return 0.0, 0.0, 0
                pct = (len(z_list) / total) * 100
                runs = sum(d['runs'] for d in z_list)
                econ = (runs / len(z_list)) * 6
                wkts = sum(d['wicket'] for d in z_list)
                return round(pct, 1), round(econ, 2), wkts

            y_pct, y_econ, y_w = calc_z(yorkers)
            f_pct, f_econ, f_w = calc_z(fulls)
            l_pct, l_econ, l_w = calc_z(lengths)
            s_pct, s_econ, s_w = calc_z(shorts)

            st.markdown(f"""
            <div style="display:grid;grid-template-columns:repeat(4, 1fr);gap:10px;margin-bottom:15px">
                <div style="background:rgba(77,171,247,0.12);border:1px solid #4dabf7;padding:10px;border-radius:10px;text-align:center">
                    <div style="font-size:10px;color:#90caf9;font-weight:700;text-transform:uppercase">🎯 Yorker (0-2m)</div>
                    <div style="font-size:18px;font-weight:800;color:#4dabf7">{y_pct}%</div>
                    <div style="font-size:11px;color:#e2e8f0;margin-top:2px">Econ <b>{y_econ}</b> | <b>{y_w}</b> Wkts</div>
                </div>
                <div style="background:rgba(107,207,127,0.12);border:1px solid #6bcf7f;padding:10px;border-radius:10px;text-align:center">
                    <div style="font-size:10px;color:#a5d6a7;font-weight:700;text-transform:uppercase">🟢 Full (2-6m)</div>
                    <div style="font-size:18px;font-weight:800;color:#6bcf7f">{f_pct}%</div>
                    <div style="font-size:11px;color:#e2e8f0;margin-top:2px">Econ <b>{f_econ}</b> | <b>{f_w}</b> Wkts</div>
                </div>
                <div style="background:rgba(255,217,61,0.12);border:1px solid #ffd93d;padding:10px;border-radius:10px;text-align:center">
                    <div style="font-size:10px;color:#ffe082;font-weight:700;text-transform:uppercase">🟡 Good (6-12m)</div>
                    <div style="font-size:18px;font-weight:800;color:#ffd93d">{l_pct}%</div>
                    <div style="font-size:11px;color:#e2e8f0;margin-top:2px">Econ <b>{l_econ}</b> | <b>{l_w}</b> Wkts</div>
                </div>
                <div style="background:rgba(255,107,107,0.12);border:1px solid #ff6b6b;padding:10px;border-radius:10px;text-align:center">
                    <div style="font-size:10px;color:#ef9a9a;font-weight:700;text-transform:uppercase">🔴 Short (12-22m)</div>
                    <div style="font-size:18px;font-weight:800;color:#ff6b6b">{s_pct}%</div>
                    <div style="font-size:11px;color:#e2e8f0;margin-top:2px">Econ <b>{s_econ}</b> | <b>{s_w}</b> Wkts</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"### {team1} Bowling Length Profile")
            real_pd1 = get_real_pitch_data(team1, opp_team=team2)
            render_zone_kpis(real_pd1, team1)
            bowling_html_1 = render_bowling_length_map(df, team1, phase=phase_val, bowler_type=bowler_type,
                                                       unique_id="team1_bowling", pitch_data_override=real_pd1)
            components.html(bowling_html_1, height=750, scrolling=True)
            if real_pd1:
                st.caption(f"📍 Real Hawk-Eye Tracking: {len(real_pd1)} deliveries analyzed")

        with col2:
            st.markdown(f"### {team2} Bowling Length Profile")
            real_pd2 = get_real_pitch_data(team2, opp_team=team1)
            render_zone_kpis(real_pd2, team2)
            bowling_html_2 = render_bowling_length_map(df, team2, phase=phase_val, bowler_type=bowler_type,
                                                       unique_id="team2_bowling", pitch_data_override=real_pd2)
            components.html(bowling_html_2, height=750, scrolling=True)
            if real_pd2:
                st.caption(f"📍 Real Hawk-Eye Tracking: {len(real_pd2)} deliveries analyzed")

    # =====================================================================
    # SECTION 5: Ball Tracking Analytics
    # =====================================================================
    if active_section == "📊 Ball Tracking":
        st.markdown("## 📊 Ball Tracking Analytics - Trajectory & Delivery Insights")
        st.markdown("""
        <div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:12px;font-size:13px">
            <span style="background:#22c55e;color:#000;padding:4px 12px;border-radius:6px;font-weight:700">✅ Hawk-Eye Ball Tracking Telemetry</span>
        </div>
        """, unsafe_allow_html=True)
        
        phase_val = None if selected_phase == 'All Phases' else selected_phase
        
        if hp and hp.has_data():
            summary = hp.get_data_summary()
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Deliveries Analyzed", f"{summary['total']:,}")
            with col2:
                st.metric("Hawk-Eye Deliveries", f"{summary['real_hawkeye']:,}")
            with col3:
                st.metric("Unique Matches Tracked", f"{df['match_id'].nunique():,}")
            with col4:
                seasons_str = ", ".join(sorted(summary['seasons'].keys()))
                st.metric("Seasons Covered", seasons_str[:15] + "..." if len(seasons_str) > 15 else seasons_str)
            
            # Color Palette for Canonical Hawk-Eye Bowler Types
            PALETTE = {
                'Right-Arm Pace': '#ef4444',
                'Left-Arm Pace': '#f97316',
                'Right-Arm Leg Spin': '#22c55e',
                'Right-Arm Off Spin': '#3b82f6',
                'Left-Arm Orthodox': '#06b6d4',
                'Left-Arm Wrist Spin': '#8b5cf6',
            }

            # Swing Analysis
            st.markdown("---")
            st.subheader("🔄 Swing & Seam Movement Analysis by Bowler Type")
            swing_data = hp.get_swing_analysis(phase=phase_val)
            if swing_data is not None and len(swing_data) > 0:
                import plotly.graph_objects as go
                fig = go.Figure()
                for _, row in swing_data.iterrows():
                    bt = str(row['bowlerType'])
                    fig.add_trace(go.Bar(
                        name=bt,
                        x=['Avg Swing', 'Max Swing', 'Avg Deviation', 'Max Deviation'],
                        y=[row['avg_swing'], row['max_swing'], row['avg_deviation'], row['max_deviation']],
                        marker_color=PALETTE.get(bt, '#94a3b8'),
                        hovertemplate=f"<b>{bt}</b><br>%{{x}}: %{{y:.2f}}°<extra></extra>"
                    ))
                fig.update_layout(
                    barmode='group',
                    title="Ball Swing & Seam Movement (° Degrees)",
                    paper_bgcolor='rgba(15,23,42,0)',
                    plot_bgcolor='rgba(15,23,42,0)',
                    font=dict(color='#e2e8f0'),
                    xaxis=dict(showgrid=False),
                    yaxis=dict(title="Degrees (°)", showgrid=True, gridcolor='rgba(255,255,255,0.05)'),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
                    height=380,
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No swing data available")
            
            # Length Analysis
            st.markdown("---")
            st.subheader("📏 Pitch Length Distribution by Bowler Type")
            len_data = hp.get_length_analysis()
            if len_data is not None and len(len_data) > 0:
                import plotly.graph_objects as go
                length_order = ['Yorker', 'Full', 'Length', 'Short', 'Bouncer']
                fig = go.Figure()
                all_btypes = len_data['bowlerType'].unique()
                for bt in all_btypes:
                    bt_data = len_data[len_data['bowlerType'] == bt]
                    if len(bt_data) > 0:
                        lengths = {r['length']: r['percentage'] for _, r in bt_data.iterrows()}
                        vals = [lengths.get(l, 0) for l in length_order]
                        fig.add_trace(go.Bar(
                            name=str(bt),
                            x=length_order,
                            y=vals,
                            marker_color=PALETTE.get(bt, '#94a3b8'),
                            hovertemplate=f"<b>{bt}</b><br>%{{x}}: %{{y:.1f}}%<extra></extra>"
                        ))
                fig.update_layout(
                    barmode='group',
                    title="Pitch Length Breakdown (%)",
                    paper_bgcolor='rgba(15,23,42,0)',
                    plot_bgcolor='rgba(15,23,42,0)',
                    font=dict(color='#e2e8f0'),
                    xaxis=dict(showgrid=False),
                    yaxis=dict(title="Percentage of Deliveries (%)", showgrid=True, gridcolor='rgba(255,255,255,0.05)'),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
                    height=380,
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No length data available")
            
            # Corridor Analysis
            st.markdown("---")
            st.subheader("🎯 Line & Off-Stump Channel Corridor Analysis")
            corr_data = hp.get_corridor_analysis()
            if corr_data is not None and len(corr_data) > 0:
                import plotly.graph_objects as go
                corridor_order = ['Outside Off', 'Off Stump', 'Middle-Leg', 'Down Leg']
                fig = go.Figure()
                all_btypes = corr_data['bowlerType'].unique()
                for bt in all_btypes:
                    bt_data = corr_data[corr_data['bowlerType'] == bt]
                    if len(bt_data) > 0:
                        corridors = {r['corridor']: r['count'] for _, r in bt_data.iterrows()}
                        vals = [corridors.get(c, 0) for c in corridor_order]
                        fig.add_trace(go.Bar(
                            name=str(bt),
                            x=corridor_order,
                            y=vals,
                            marker_color=PALETTE.get(bt, '#94a3b8'),
                            hovertemplate=f"<b>{bt}</b><br>%{{x}}: %{{y:,}} deliveries<extra></extra>"
                        ))
                fig.update_layout(
                    barmode='group',
                    title="Line Targeting Distribution (Deliveries Count)",
                    paper_bgcolor='rgba(15,23,42,0)',
                    plot_bgcolor='rgba(15,23,42,0)',
                    font=dict(color='#e2e8f0'),
                    xaxis=dict(showgrid=False),
                    yaxis=dict(title="Deliveries Count", showgrid=True, gridcolor='rgba(255,255,255,0.05)'),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
                    height=380,
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No corridor data available")
            
            # Six Distance Analysis
            st.markdown("---")
            st.subheader("💥 Six-Hit Distance Analysis & Top Power Hitters")
            six_data = hp.get_six_distance_analysis()
            if six_data is not None and len(six_data) > 0:
                import plotly.express as px
                fig = px.histogram(
                    six_data, x='sixDistance', nbins=25,
                    title="Distribution of Recorded Six-Hit Distances (Meters)",
                    labels={'sixDistance': 'Distance (m)', 'count': 'Number of Sixes'},
                    color_discrete_sequence=['#a855f7'],
                )
                fig.update_layout(
                    paper_bgcolor='rgba(15,23,42,0)',
                    plot_bgcolor='rgba(15,23,42,0)',
                    font=dict(color='#e2e8f0'),
                    xaxis=dict(title="Hit Distance (Meters)", showgrid=True, gridcolor='rgba(255,255,255,0.05)'),
                    yaxis=dict(title="Sixes Count", showgrid=True, gridcolor='rgba(255,255,255,0.05)'),
                    height=360,
                )
                st.plotly_chart(fig, use_container_width=True)
                
                top_six = six_data.groupby('batter').agg(
                    avg_dist=('sixDistance', 'mean'),
                    max_dist=('sixDistance', 'max'),
                    total_sixes=('sixDistance', 'count')
                ).sort_values('max_dist', ascending=False).head(10).reset_index()
                
                st.markdown("**💥 Longest Hitters Leaderboard (Max & Average Six Distance)**")
                st.dataframe(
                    top_six.rename(columns={
                        'batter': 'Batter',
                        'avg_dist': 'Avg Distance (m)',
                        'max_dist': 'Longest Six (m)',
                        'total_sixes': 'Total Sixes'
                    }).style.format({'Avg Distance (m)': '{:.1f}', 'Longest Six (m)': '{:.1f}'}),
                    use_container_width=True
                )
            else:
                st.info("No six distance data available")
        
        else:
            st.warning("Ball-tracking data not loaded. Toggle 'Use Real Hawk-Eye Data' in the sidebar.")
    
    # =====================================================================
    # SECTION 6: Statistical Charts
    # =====================================================================
    if active_section == "📈 Statistical Charts":
        phase_val = None if selected_phase == 'All Phases' else selected_phase
        bt_label = f" (filtered: {bowler_type})" if bowler_type and bowler_type != 'All Types' else ""
        st.markdown(f"## 📈 Statistical Analysis - Interactive Altair Charts{bt_label}")
    
        st.markdown("### 📊 Runs Distribution Analysis")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**{team1} - Runs per Ball Distribution**")
            runs_chart_1 = create_runs_distribution_chart(df, team1, phase=phase_val)
            if runs_chart_1:
                st.plotly_chart(runs_chart_1, use_container_width=True, config={'displayModeBar': False})
            else:
                st.info("No data available")
        with col2:
            st.markdown(f"**{team2} - Runs per Ball Distribution**")
            runs_chart_2 = create_runs_distribution_chart(df, team2, phase=phase_val)
            if runs_chart_2:
                st.plotly_chart(runs_chart_2, use_container_width=True, config={'displayModeBar': False})
            else:
                st.info("No data available")
    
        st.markdown("### ⚡ Strike Rate Comparison - Top Performers")
        strike_rate_chart = create_strike_rate_comparison(df, phase=phase_val)
        if strike_rate_chart:
            st.plotly_chart(strike_rate_chart, use_container_width=True, config={'displayModeBar': False})
    
        st.markdown("### 🎯 Boundary & Dot Ball Analysis")
        boundary_chart = create_boundary_percentage_chart(df, [team1, team2], phase=phase_val)
        if boundary_chart:
            st.plotly_chart(boundary_chart, use_container_width=True, config={'displayModeBar': False})
    
        st.markdown("### 📈 Runs Progression Over Overs")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**{team1} - Over-by-Over Progression**")
            progression_1 = create_runs_over_progression(df, team1, phase=phase_val)
            if progression_1:
                st.plotly_chart(progression_1, use_container_width=True, config={'displayModeBar': False})
        with col2:
            st.markdown(f"**{team2} - Over-by-Over Progression**")
            progression_2 = create_runs_over_progression(df, team2, phase=phase_val)
            if progression_2:
                st.plotly_chart(progression_2, use_container_width=True, config={'displayModeBar': False})
    
        st.markdown("### 🎯 Wicket Fall Timeline")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**{team1} Bowling - Wickets Timeline**")
            wicket_chart_1 = create_wicket_timeline(df, team1, phase=phase_val)
            if wicket_chart_1:
                st.plotly_chart(wicket_chart_1, use_container_width=True, config={'displayModeBar': False})
            else:
                st.info(f"No wickets data available for {team1}")
        with col2:
            st.markdown(f"**{team2} Bowling - Wickets Timeline**")
            wicket_chart_2 = create_wicket_timeline(df, team2, phase=phase_val)
            if wicket_chart_2:
                st.plotly_chart(wicket_chart_2, use_container_width=True, config={'displayModeBar': False})
            else:
                st.info(f"No wickets data available for {team2}")
    
        st.markdown("### 💰 Bowler Economy Rate Analysis")
        col1, col2 = st.columns(2)
        with col1:
            bt_label = f" vs {bowler_type}" if bowler_type and bowler_type != 'All Types' else ""
            st.markdown(f"**{team1} - Bowler Economy Rates{bt_label}**")
            economy_chart_1 = create_bowler_economy_chart(df, team1, phase=phase_val, bowler_type=bowler_type)
            if economy_chart_1:
                st.altair_chart(economy_chart_1, use_container_width=True)
        with col2:
            bt_label = f" vs {bowler_type}" if bowler_type and bowler_type != 'All Types' else ""
            st.markdown(f"**{team2} - Bowler Economy Rates{bt_label}**")
            economy_chart_2 = create_bowler_economy_chart(df, team2, phase=phase_val, bowler_type=bowler_type)
            if economy_chart_2:
                st.altair_chart(economy_chart_2, use_container_width=True)

        if HAWKEYE_AVAILABLE:
            with st.expander("📊 Advanced Hawk-Eye Bowler Analytics (Speed, Swing, Length)"):
                he = get_hawkeye_processor()
                if he.has_data():
                    st.markdown("##### Per-Bowler Speed & Swing")
                    c1, c2 = st.columns(2)
                    for idx, (tm, col) in enumerate([(team1, c1), (team2, c2)]):
                        ba = he.get_bowler_analysis(team=tm)
                        if ba is not None and not ba.empty:
                            with col:
                                display_cols = ['bowler', 'balls', 'economy', 'avg_speed_kmh', 'max_speed_kmh', 'avg_swing', 'avg_deviation']
                                available = [c for c in display_cols if c in ba.columns]
                                st.dataframe(
                                    ba[available].head(8).style
                                    .format({c: '{:.1f}' for c in ['economy', 'avg_speed_kmh', 'max_speed_kmh', 'avg_swing', 'avg_deviation'] if c in ba.columns}),
                                    hide_index=True, use_container_width=True
                                )
                        else:
                            with col:
                                st.info(f"No Hawk-Eye data for {tm}")

                    st.markdown("##### Swing by Bowler Type")
                    swing = he.get_swing_analysis(team=team1)
                    if swing is not None and not swing.empty:
                        import plotly.express as px
                        fig = px.bar(swing, x='bowlerType', y='avg_swing',
                                     color='avg_swing', color_continuous_scale='RdYlBu_r',
                                     title='Average Swing by Bowler Type (cm)',
                                     labels={'bowlerType': 'Bowler Type', 'avg_swing': 'Avg Swing (cm)'})
                        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                                          font=dict(color='#e2e8f0'), xaxis=dict(tickangle=-30))
                        st.plotly_chart(fig, use_container_width=True)
                else:
                    st.caption("Hawk-Eye data files not found. Run `python build_dataset.py` to set up the data pipeline.")

    # =====================================================================
    # SECTION 7: Animations
    # =====================================================================
    # 3D Ball Trajectory Animation Section
    # =====================================================================
    if active_section == "🎬 Animations":
        st.markdown("## ⚡ High-Speed Delivery Telemetry & Speed Radar Matrix")
        st.markdown("""Explore **real 0.001s instant-rendering Plotly telemetry visualizers**: Ball Release Speed Radars, Aerodynamic Air Swing Matrices, and Stumps Target Impact Grids.""")
        
        from ipl_analytics.charts.bowling import (
            create_delivery_speed_radar_chart,
            create_aerodynamic_swing_matrix_chart,
            create_stumps_target_grid_chart,
            render_bowler_telemetry_kpi_cards
        )

        all_bowlers = sorted(list(df['bowler'].dropna().unique())) if 'bowler' in df.columns else ['J Bumrah']
        default_bowler_idx = all_bowlers.index('J Bumrah') if 'J Bumrah' in all_bowlers else 0

        st.markdown("### 🔍 Select Bowler Telemetry Target")
        col_sel1, col_sel2 = st.columns([2, 2])
        with col_sel1:
            sel_bowler = st.selectbox("Select Bowler for Telemetry Inspection", options=all_bowlers, index=default_bowler_idx)

        st.markdown(f"#### 📊 Telemetry Averages & Movement Summary — {sel_bowler}")
        render_bowler_telemetry_kpi_cards(df, sel_bowler)

        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            speed_radar_fig = create_delivery_speed_radar_chart(df, sel_bowler)
            st.plotly_chart(speed_radar_fig, use_container_width=True)

        with col2:
            swing_matrix_fig = create_aerodynamic_swing_matrix_chart(df, sel_bowler)
            st.plotly_chart(swing_matrix_fig, use_container_width=True)

        st.markdown("---")
        st.markdown("### 🎯 Stumps Target Zone Impact Grid")
        stumps_grid_fig = create_stumps_target_grid_chart(df, sel_bowler)
        st.plotly_chart(stumps_grid_fig, use_container_width=True)

    # =====================================================================
    # SECTION 8: Prediction
    # =====================================================================
    if active_section == "🔮 Prediction":
        st.markdown("## 🔮 Match & Season Prediction Engine")
        st.markdown("Machine Learning simulation forecasting **Winning Team, Player of the Match (POTM), Best Batter, Best Bowler, Top All-Rounder, & Top Catch Taker**.")
        
        from ipl_analytics.predictor_engine import predictor
        
        res = predictor.predict_full_match(
            team1=team1,
            team2=team2,
            venue=selected_venue if selected_venue != 'All Venues' else 'Wankhede Stadium',
            toss_winner=team1,
            toss_decision="bat"
        )

        win_info = res["win_prediction"]
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, rgba(15,23,42,0.95), rgba(7,11,25,0.98)); border: 1px solid rgba(56,189,248,0.5); border-radius: 16px; padding: 22px; margin-bottom: 24px; box-shadow: 0 10px 40px rgba(0,0,0,0.5);">
            <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px;">
                <div>
                    <span style="font-size:12px; font-weight:700; color:#94a3b8; text-transform:uppercase; letter-spacing:1px;">🏆 PREDICTED WINNER</span>
                    <h2 style="margin:4px 0 0; font-size:28px; font-weight:800; color:#f59e0b;">{win_info['winning_team']}</h2>
                </div>
                <div style="display:flex; gap:24px;">
                    <div><span style="font-size:11px; color:#cbd5e1;">{team1} Win Prob</span><div style="font-size:20px; font-weight:800; color:#f59e0b;">{win_info['team1_win_probability']}%</div></div>
                    <div><span style="font-size:11px; color:#cbd5e1;">{team2} Win Prob</span><div style="font-size:20px; font-weight:800; color:#38bdf8;">{win_info['team2_win_probability']}%</div></div>
                </div>
            </div>
            <div style="margin-top:16px; display:flex; gap:20px; font-size:13px; color:#cbd5e1;">
                <div>Proj Score ({team1}): <strong style="color:#4ade80">{win_info['projected_scores'][team1]}</strong></div>
                <div>Proj Score ({team2}): <strong style="color:#4ade80">{win_info['projected_scores'][team2]}</strong></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.progress(float(win_info['team1_win_probability']) / 100.0)
        st.markdown("---")

        # Grid of Predictions
        grid1, grid2 = st.columns(2)

        with grid1:
            st.markdown("### 🎖️ Player of the Match (POTM) Contenders")
            potm_df = pd.DataFrame(res["potm_contenders"])
            if not potm_df.empty:
                st.dataframe(potm_df[['player', 'team', 'role', 'summary', 'potm_probability_pct']].rename(columns={
                    'player': 'Player', 'team': 'Team', 'role': 'Role', 'summary': 'Performance Summary', 'potm_probability_pct': 'POTM Prob %'
                }), hide_index=True, use_container_width=True)

            st.markdown("### 🎯 Highest Wicket Taker & Best Bowler")
            bwl_df = pd.DataFrame(res["top_bowlers"])
            if not bwl_df.empty:
                st.dataframe(bwl_df[['player', 'team', 'projected_wickets', 'projected_economy', 'projected_dots', 'three_wkt_probability_pct']].rename(columns={
                    'player': 'Bowler', 'team': 'Team', 'projected_wickets': 'Proj Wkts', 'projected_economy': 'Econ', 'projected_dots': 'Dots', 'three_wkt_probability_pct': '3+ Wkts %'
                }), hide_index=True, use_container_width=True)

        with grid2:
            st.markdown("### 🏏 Highest Run Scorer & Best Batsman")
            bat_df = pd.DataFrame(res["top_batters"])
            if not bat_df.empty:
                st.dataframe(bat_df[['player', 'team', 'projected_runs', 'projected_sr', 'projected_fours', 'projected_sixes', 'fifty_probability_pct']].rename(columns={
                    'player': 'Batter', 'team': 'Team', 'projected_runs': 'Proj Runs', 'projected_sr': 'SR', 'projected_fours': '4s', 'projected_sixes': '6s', 'fifty_probability_pct': '50+ Prob %'
                }), hide_index=True, use_container_width=True)

            st.markdown("### ⚡ Top All-Rounders & 🧤 Top Catch Takers")
            ar_df = pd.DataFrame(res["top_allrounders"])
            fld_df = pd.DataFrame(res["top_fielders"])
            
            col_ar, col_fld = st.columns(2)
            with col_ar:
                st.markdown("**Top All-Rounders**")
                if not ar_df.empty:
                    st.dataframe(ar_df[['player', 'allrounder_impact_points']].rename(columns={'player': 'Player', 'allrounder_impact_points': 'Pts'}), hide_index=True, use_container_width=True)
            with col_fld:
                st.markdown("**Top Fielders & Catchers**")
                if not fld_df.empty:
                    st.dataframe(fld_df[['player', 'catches', 'catch_prob_pct']].rename(columns={'player': 'Player', 'catches': 'Catches', 'catch_prob_pct': 'Prob %'}), hide_index=True, use_container_width=True)

    # Render Floating AI Assistant Overlay at bottom right of screen
    render_floating_chatbot(api_key=os.environ.get("GEMINI_API_KEY", ""), df=df, team1=team1, team2=team2)

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
function getCleanApiKey() {
    let raw = apiKeyInput.value || '';
    raw = raw.trim();
    // Remove leading/trailing quotation marks if user copied key with quotes
    raw = raw.replace(/^["']|["']$/g, '').trim();
    return raw;
}

// Save key instantly as user types or pastes
apiKeyInput.addEventListener('input', () => {
    const key = getCleanApiKey();
    if (key) {
        localStorage.setItem('ipl_gemini_key', key);
    }
});
apiKeyInput.addEventListener('change', () => {
    const key = getCleanApiKey();
    if (key) {
        localStorage.setItem('ipl_gemini_key', key);
    }
});

// Load cached key if present
if (localStorage.getItem('ipl_gemini_key') && !apiKeyInput.value) {
    apiKeyInput.value = localStorage.getItem('ipl_gemini_key');
}

// Draggable Handler for Chat Header
chatHeader.addEventListener('mousedown', (e) => {
    if (e.target.closest('.icon-btn')) return;
    isDragging = true;
    startX = e.clientX;
    startY = e.clientY;
    
    const rect = chatWindow.getBoundingClientRect();
    initialLeft = rect.left;
    initialTop = rect.top;
});

document.addEventListener('mousemove', (e) => {
    if (!isDragging) return;
    const dx = e.clientX - startX;
    const dy = e.clientY - startY;
    
    chatWindow.style.left = `${initialLeft + dx}px`;
    chatWindow.style.top = `${initialTop + dy}px`;
    chatWindow.style.bottom = 'auto';
    chatWindow.style.right = 'auto';
});

document.addEventListener('mouseup', () => {
    isDragging = false;
});

function updateIframeSize(open) {
    if (window.frameElement) {
        if (open) {
            window.frameElement.style.setProperty('width', '380px', 'important');
            window.frameElement.style.setProperty('height', '580px', 'important');
        } else {
            window.frameElement.style.setProperty('width', '70px', 'important');
            window.frameElement.style.setProperty('height', '70px', 'important');
        }
    }
}

// Initial collapsed state
setTimeout(() => updateIframeSize(false), 50);

fabBtn.addEventListener('click', () => {
    isOpen = !isOpen;
    if (isOpen) {
        updateIframeSize(true);
        chatWindow.classList.add('open');
        document.getElementById('fab-icon').textContent = '✕';
    } else {
        chatWindow.classList.remove('open');
        document.getElementById('fab-icon').textContent = '🤖';
        setTimeout(() => updateIframeSize(false), 300);
    }
});

closeBtn.addEventListener('click', () => {
    isOpen = false;
    chatWindow.classList.remove('open');
    document.getElementById('fab-icon').textContent = '🤖';
    setTimeout(() => updateIframeSize(false), 300);
});

settingsToggleBtn.addEventListener('click', () => {
    settingsPanel.classList.toggle('active');
});

function appendMessage(role, text) {
    const div = document.createElement('div');
    div.className = `msg ${role}`;
    div.innerHTML = text.replace(/\n/g, '<br>').replace(/\*\*(.*?)\*\*/g, '<b>$1</b>');
    messagesContainer.appendChild(div);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function sendQuickPrompt(promptText) {
    chatInput.value = promptText;
    sendMessage();
}

function navigateDashboard(targetSection) {
    try {
        let parentOrigin = '';
        if (window.location.ancestorOrigins && window.location.ancestorOrigins.length > 0) {
            parentOrigin = window.location.ancestorOrigins[0];
        } else if (document.referrer) {
            parentOrigin = document.referrer.split('?')[0].replace(RegExp('/$'), '');
        } else {
            parentOrigin = window.location.protocol + '//' + window.location.host;
        }
        
        const targetUrl = parentOrigin + '/?section=' + encodeURIComponent(targetSection);
        const link = document.createElement('a');
        link.href = targetUrl;
        link.target = '_top';
        document.body.appendChild(link);
        link.click();
    } catch(e) {
        console.log('Navigation trigger error:', e);
    }
}

// AI Copilot Autonomous Function Dispatcher & Navigation Engine
function getOfflineIplResponse(userQuery) {
    const q = userQuery.toLowerCase();
    const config = window.CHATBOT_CONFIG || {};
    
    const t1_name = config.team1 || 'Team 1';
    const t2_name = config.team2 || 'Team 2';
    const t1_runs = config.t1_runs || 0;
    const t1_balls = config.t1_balls || 0;
    const t1_rr = config.t1_rr || 0.0;
    const t1_fours = config.t1_fours || 0;
    const t1_sixes = config.t1_sixes || 0;
    const t1_wickets = config.t1_wickets || 0;
    const t1_dot_pct = config.t1_dot_pct || 0.0;
    const t1_top_name = config.t1_top_name || 'N/A';
    const t1_top_runs = config.t1_top_runs || 0;
    const t2_runs = config.t2_runs || 0;
    const t2_balls = config.t2_balls || 0;
    const t2_rr = config.t2_rr || 0.0;
    const t2_fours = config.t2_fours || 0;
    const t2_sixes = config.t2_sixes || 0;
    const t2_wickets = config.t2_wickets || 0;
    const t2_dot_pct = config.t2_dot_pct || 0.0;
    const t2_top_name = config.t2_top_name || 'N/A';
    const t2_top_runs = config.t2_top_runs || 0;

    // 1. Player Comparison Command (e.g. "Compare Gaikwad vs Gill")
    if (q.includes('vs') || q.includes('versus') || (q.includes('compare') && (q.includes(' and ') || q.includes('&')))) {
        setTimeout(() => navigateDashboard('👤 Player Stats'), 700);
        return `⚔️ <b>Side-by-Side Analytics Executed:</b><br><br>` +
               `<b>📊 ${t1_top_name}:</b><br>` +
               `• Total Runs: <b>${t1_top_runs} runs</b><br>` +
               `• Franchise: <b>${t1_name}</b> (${t1_rr} RR, ${t1_fours} 4s, ${t1_sixes} 6s)<br><br>` +
               `<b>📊 ${t2_top_name}:</b><br>` +
               `• Total Runs: <b>${t2_top_runs} runs</b><br>` +
               `• Franchise: <b>${t2_name}</b> (${t2_rr} RR, ${t2_fours} 4s, ${t2_sixes} 6s)<br><br>` +
               `🚀 <i>Navigating dashboard to <b>👤 Player Stats</b> section...</i>`;
    }

    // 2. Bowler / Phase Statistics Command (e.g. "Bumrah death overs")
    if (q.includes('death') || q.includes('powerplay') || q.includes('middle') || q.includes('phase')) {
        setTimeout(() => navigateDashboard('📊 Phase Analysis'), 700);
        return `📊 <b>Phase Telemetry Executed:</b><br><br>` +
               `• <b>${t1_name}:</b> ${t1_runs.toLocaleString()} runs | ${t1_rr} RPO | ${t1_dot_pct}% Dot Balls<br>` +
               `• <b>${t2_name}:</b> ${t2_runs.toLocaleString()} runs | ${t2_rr} RPO | ${t2_dot_pct}% Dot Balls<br><br>` +
               `🚀 <i>Navigating dashboard to <b>📊 Phase Analysis</b> section...</i>`;
    }

    // 3. Pitch Map & Length Command
    if (q.includes('pitch') || q.includes('length') || q.includes('zone') || q.includes('yorker') || q.includes('good length')) {
        setTimeout(() => navigateDashboard('🎯 Pitch Maps & Wagon Wheel'), 700);
        return `🎯 <b>3D Pitch & Length Zone Telemetry Executed:</b><br><br>` +
               `• <b>Good Length (6m-8m):</b> High seam bounce & edge %<br>` +
               `• <b>Yorker Pitch (0m-2m):</b> Crease-line delivery for death containment<br><br>` +
               `🚀 <i>Navigating dashboard to <b>🎯 Pitch Maps & Wagon Wheel</b> section...</i>`;
    }

    // 4. Wagon Wheel Command
    if (q.includes('wagon') || q.includes('wheel') || q.includes('shot') || q.includes('direction')) {
        setTimeout(() => navigateDashboard('🎯 Pitch Maps & Wagon Wheel'), 700);
        return `🏏 <b>Wagon Wheel Telemetry Executed:</b><br><br>` +
               `• 360° Ground Trajectory Vectors<br>` +
               `• Sector-by-sector scoring distribution<br><br>` +
               `🚀 <i>Navigating dashboard to <b>🎯 Pitch Maps & Wagon Wheel</b> section...</i>`;
    }

    // 5. Ball Tracking Command
    if (q.includes('hawkeye') || q.includes('tracking') || q.includes('speed') || q.includes('bounce')) {
        setTimeout(() => navigateDashboard('📊 Ball Tracking'), 700);
        return `📡 <b>Hawk-Eye Delivery Telemetry Executed:</b><br><br>` +
               `• Delivery release speeds, angles & bounce points<br><br>` +
               `🚀 <i>Navigating dashboard to <b>📊 Ball Tracking</b> section...</i>`;
    }

    if (q.includes('csk') || q.includes('chennai') || q.includes('team') || q.includes('summary') || q.includes('overview') || q.includes('batting') || q.includes('performance') || q.includes('stat') || q.includes('run')) {
        return `🏏 <b>Real IPL Match Telemetry Summary:</b><br><br>` +
               `<b>🟡 ${t1_name} Batting Overview:</b><br>` +
               `• <b>Total Runs:</b> ${t1_runs.toLocaleString()} runs (${t1_balls.toLocaleString()} balls)<br>` +
               `• <b>Run Rate:</b> ${t1_rr} RPO | <b>Wickets Lost:</b> ${t1_wickets}<br>` +
               `• <b>Boundary Count:</b> ${t1_fours} Fours | ${t1_sixes} Sixes<br>` +
               `• <b>Dot Ball Rate:</b> ${t1_dot_pct}%<br>` +
               `• <b>Top Run-Getter:</b> ${t1_top_name} (${t1_top_runs} runs)<br><br>` +
               `<b>🔵 ${t2_name} Batting Overview:</b><br>` +
               `• <b>Total Runs:</b> ${t2_runs.toLocaleString()} runs (${t2_balls.toLocaleString()} balls)<br>` +
               `• <b>Run Rate:</b> ${t2_rr} RPO | <b>Wickets Lost:</b> ${t2_wickets}<br>` +
               `• <b>Boundary Count:</b> ${t2_fours} Fours | ${t2_sixes} Sixes<br>` +
               `• <b>Dot Ball Rate:</b> ${t2_dot_pct}%<br>` +
               `• <b>Top Run-Getter:</b> ${t2_top_name} (${t2_top_runs} runs)`;
    }

    return `🏏 <b>IPL AI Autonomous Copilot (${t1_name} vs ${t2_name}):</b><br>` +
           `• <b>${t1_name}:</b> ${t1_runs.toLocaleString()} runs (${t1_rr} RR)<br>` +
           `• <b>${t2_name}:</b> ${t2_runs.toLocaleString()} runs (${t2_rr} RR)<br><br>` +
           `Try entering commands like:<br>` +
           `• <i>"Compare Ruturaj Gaikwad vs Shubman Gill"</i><br>` +
           `• <i>"Show death over statistics"</i><br>` +
           `• <i>"Open 3D Pitch Map"</i>`;
}

async function sendMessage() {
    const text = chatInput.value.trim();
    if (!text) return;

    appendMessage('user', text);
    chatInput.value = '';

    const apiKey = getCleanApiKey();

    // IF NO API KEY: Use built-in Offline IPL Intelligence Engine
    if (!apiKey) {
        const reply = getOfflineIplResponse(text);
        setTimeout(() => {
            appendMessage('assistant', reply);
        }, 300);
        return;
    }

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

    for (const model of uniqueModels) {
        const url = `https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent?key=${apiKey}`;

        const config = window.CHATBOT_CONFIG || {};
        const systemInstruction = "You are the IPL Performance Intelligence Assistant. ALWAYS use exact numbers without placeholders. Real Match Data: " + 
            (config.team1 || 'Team 1') + " has " + (config.t1_runs || 0).toLocaleString() + " runs (" + (config.t1_rr || 0) + " RR, " + (config.t1_fours || 0) + " 4s, " + (config.t1_sixes || 0) + " 6s, Top: " + (config.t1_top_name || 'N/A') + " " + (config.t1_top_runs || 0) + " runs). " +
            (config.team2 || 'Team 2') + " has " + (config.t2_runs || 0).toLocaleString() + " runs (" + (config.t2_rr || 0) + " RR, " + (config.t2_fours || 0) + " 4s, " + (config.t2_sixes || 0) + " 6s, Top: " + (config.t2_top_name || 'N/A') + " " + (config.t2_top_runs || 0) + " runs). Never print bracket placeholders like [Insert Total].";

        const payload = {
            contents: [
                { role: "user", parts: [{ text: systemInstruction + "\n\nUser question: " + text }] }
            ]
        };

        try {
            const res = await fetch(url, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            if (res.ok) {
                const data = await res.json();
                const reply = data.candidates?.[0]?.content?.parts?.[0]?.text || "No response received.";
                if (loadingDiv.parentNode) messagesContainer.removeChild(loadingDiv);
                appendMessage('assistant', reply);
                success = true;
                break;
            } else {
                const err = await res.json();
                lastErrorMsg = `[${model}] HTTP ${res.status}: ${err.error?.message || res.statusText}`;
                if (res.status !== 404) {
                    break;
                }
            }
        } catch (e) {
            lastErrorMsg = `Network Error: ${e.message}`;
        }
    }

    if (!success) {
        if (loadingDiv.parentNode) messagesContainer.removeChild(loadingDiv);
        if (lastErrorMsg.includes('API_KEY_INVALID') || lastErrorMsg.includes('API key not valid') || lastErrorMsg.includes('400')) {
            appendMessage('assistant', '⚠️ <b>Invalid API Key provided!</b> Falling back to built-in Offline Intelligence Engine:<br><br>' + getOfflineIplResponse(text));
        } else {
            appendMessage('assistant', `⚠️ <b>Request failed:</b><br>${lastErrorMsg}<br><br>` + getOfflineIplResponse(text));
        }
    }
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}
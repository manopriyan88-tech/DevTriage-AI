import os
import time
import json
import streamlit as st
import streamlit.components.v1 as components
from typing import Literal
from pydantic import BaseModel, Field
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="DevTriage-AI // Autonomous L1 Command",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CUSTOM CYBER-GLASS, HAPTIC & MACOS DOCK CSS ---
st.markdown('''
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;700&display=swap');

#MainMenu, header, footer, .stDeployButton {visibility: hidden !important;}

html, body, [class*="css"] {
    font-family: 'Space Grotesk', sans-serif;
    background-color: #07090E;
    color: #F3F4F6;
}

.stApp {
    background-image: radial-gradient(rgba(255, 255, 255, 0.06) 1px, transparent 0);
    background-size: 24px 24px;
    background-color: #07090E;
    padding-bottom: 110px;
}

div.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #FF3B30 0%, #FF6B4A 100%);
    color: #FFFFFF;
    border: 1px solid rgba(255, 107, 74, 0.5);
    border-radius: 14px;
    padding: 0.75rem 2rem;
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 700;
    font-size: 1.05rem;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    box-shadow: 0 8px 25px -4px rgba(255, 59, 48, 0.45), inset 0 1px 0 rgba(255,255,255,0.25);
    transition: all 0.18s cubic-bezier(0.34, 1.56, 0.64, 1);
    width: 100%;
}
div.stButton > button[kind="primary"]:hover {
    transform: translateY(-2px) scale(1.01);
    box-shadow: 0 14px 32px -4px rgba(255, 59, 48, 0.65), inset 0 1px 0 rgba(255,255,255,0.4);
}
div.stButton > button[kind="primary"]:active {
    transform: translateY(1px) scale(0.96);
    box-shadow: 0 4px 12px -2px rgba(255, 59, 48, 0.4);
}

.stTextArea textarea, .stSelectbox div[data-baseweb="select"] > div {
    background: rgba(17, 22, 34, 0.85) !important;
    border: 1px solid rgba(255, 255, 255, 0.12) !important;
    border-radius: 14px !important;
    color: #F9FAFB !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.95rem !important;
}
.stTextArea textarea:focus {
    border-color: #FF453A !important;
    box-shadow: 0 0 0 3px rgba(255, 69, 58, 0.2) !important;
}

.hud-card {
    background: rgba(16, 20, 31, 0.78);
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    border: 1px solid rgba(255, 255, 255, 0.09);
    border-radius: 18px;
    padding: 22px 24px;
    box-shadow: 0 16px 40px -12px rgba(0, 0, 0, 0.7);
    animation: slideUp 0.35s cubic-bezier(0.16, 1, 0.3, 1) forwards;
    transition: transform 0.2s ease, border-color 0.2s ease;
}
.hud-card:hover {
    transform: translateY(-3px);
    border-color: rgba(255, 255, 255, 0.22);
}

@keyframes slideUp {
    from { opacity: 0; transform: translateY(18px); }
    to { opacity: 1; transform: translateY(0); }
}

@keyframes pulseGlow {
    0%, 100% { opacity: 1; transform: scale(1); }
    50% { opacity: 0.45; transform: scale(1.18); }
}

.status-dot {
    display: inline-block;
    width: 9px;
    height: 9px;
    border-radius: 50%;
    margin-right: 8px;
    animation: pulseGlow 2s infinite;
}

.pipeline-step {
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 12px;
    padding: 10px 14px;
    text-align: center;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.78rem;
    color: #9CA3AF;
}
.pipeline-step.active {
    background: rgba(16, 185, 129, 0.1);
    border-color: rgba(16, 185, 129, 0.45);
    color: #34D399;
    font-weight: 600;
}
</style>
''', unsafe_allow_html=True)

class TriageDecision(BaseModel):
    category: Literal["Billing", "Account", "Technical", "Security", "General"]
    priority: Literal["Low", "Medium", "High", "Critical"]
    action: Literal["AUTO_REPLY", "ESCALATE"]
    confidence: int = Field(description="Confidence percentage (0-100)")
    grounded_rationale: str = Field(description="Citing SOP policy rule from Knowledge Base")
    suggested_output: str = Field(description="Drafted response or internal escalation summary")

KB_FILE = "knowledge_base.json"
if os.path.exists(KB_FILE):
    with open(KB_FILE, "r") as f:
        knowledge_base = json.load(f)
else:
    knowledge_base = {
        "KB-01": {"topic": "Webcam Permission", "policy": "Instruct user to grant permissions in browser site settings.", "action": "AUTO_REPLY"},
        "KB-02": {"topic": "Compiler Timeout / TLE", "policy": "TLE on specific testcases indicates algorithmic complexity (e.g. O(N^2)), not server downtime.", "action": "AUTO_REPLY"},
        "KB-04": {"topic": "Refunds & Cancellations", "policy": "Automated agents cannot issue refunds or handle financial disputes. Mandated escalation.", "action": "ESCALATE"}
    }

def trigger_haptic_feedback(is_escalate: bool):
    freq1 = 280 if is_escalate else 520
    freq2 = 190 if is_escalate else 780
    script = f'''
    <script>
    (function() {{
        try {{
            if (navigator.vibrate) navigator.vibrate([35, 50, 45]);
            const ctx = new (window.AudioContext || window.webkitAudioContext)();
            const osc = ctx.createOscillator();
            const gain = ctx.createGain();
            osc.type = 'sine';
            osc.frequency.setValueAtTime({freq1}, ctx.currentTime);
            osc.frequency.exponentialRampToValueAtTime({freq2}, ctx.currentTime + 0.14);
            gain.gain.setValueAtTime(0.08, ctx.currentTime);
            gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.16);
            osc.connect(gain);
            gain.connect(ctx.destination);
            osc.start();
            osc.stop(ctx.currentTime + 0.16);
        }} catch(e) {{}}
    }})();
    </script>
    '''
    components.html(script, height=0)

def inject_magnification_dock():
    dock_script = '''
    <script>
    (function() {
        const doc = window.parent.document;
        if (doc.getElementById('devtriage-mag-dock')) return;

        const style = doc.createElement('style');
        style.innerHTML = `
            #devtriage-mag-dock-wrap {
                position: fixed;
                bottom: 18px;
                left: 50%;
                transform: translateX(-50%);
                z-index: 99999;
                display: flex;
                align-items: flex-end;
                justify-content: center;
                height: 92px;
                pointer-events: none;
            }
            #devtriage-mag-dock {
                pointer-events: auto;
                display: flex;
                align-items: flex-end;
                gap: 12px;
                height: 66px;
                padding: 0 18px 8px 18px;
                border-radius: 26px;
                background: rgba(16, 20, 31, 0.72);
                backdrop-filter: blur(20px);
                -webkit-backdrop-filter: blur(20px);
                border: 1px solid rgba(255, 255, 255, 0.14);
                box-shadow: 0 20px 50px rgba(0, 0, 0, 0.75), inset 0 1px 0 rgba(255, 255, 255, 0.15);
            }
            .dt-dock-item {
                position: relative;
                width: 50px;
                height: 50px;
                border-radius: 50%;
                background: rgba(29, 36, 52, 0.9);
                border: 1px solid rgba(255, 255, 255, 0.14);
                display: inline-flex;
                align-items: center;
                justify-content: center;
                cursor: pointer;
                color: #F3F4F6;
                font-size: 20px;
                box-shadow: 0 8px 20px rgba(0,0,0,0.45);
                transition: border-color 0.15s ease, background 0.15s ease;
                user-select: none;
                will-change: width, height;
            }
            .dt-dock-item:hover {
                border-color: #FF6B4A;
                background: rgba(43, 53, 76, 0.95);
            }
            .dt-dock-item.dt-primary {
                background: linear-gradient(135deg, #FF3B30 0%, #FF6B4A 100%);
                border-color: rgba(255, 255, 255, 0.35);
                box-shadow: 0 8px 24px rgba(255, 59, 48, 0.5);
            }
            .dt-dock-label {
                position: absolute;
                top: -36px;
                left: 50%;
                transform: translateX(-50%) translateY(6px);
                opacity: 0;
                pointer-events: none;
                white-space: nowrap;
                background: rgba(12, 16, 25, 0.95);
                border: 1px solid rgba(255, 255, 255, 0.15);
                color: #F9FAFB;
                font-family: 'Space Grotesk', sans-serif;
                font-size: 12px;
                font-weight: 600;
                padding: 4px 10px;
                border-radius: 8px;
                box-shadow: 0 6px 16px rgba(0,0,0,0.5);
                transition: opacity 0.16s ease, transform 0.16s ease;
            }
            .dt-dock-item:hover .dt-dock-label {
                opacity: 1;
                transform: translateX(-50%) translateY(0);
            }
        `;
        doc.head.appendChild(style);

        const playClickTone = (freq) => {
            try {
                const ctx = new (window.AudioContext || window.webkitAudioContext)();
                const osc = ctx.createOscillator();
                const gain = ctx.createGain();
                osc.type = 'sine';
                osc.frequency.setValueAtTime(freq, ctx.currentTime);
                gain.gain.setValueAtTime(0.06, ctx.currentTime);
                gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.09);
                osc.connect(gain);
                gain.connect(ctx.destination);
                osc.start();
                osc.stop(ctx.currentTime + 0.09);
            } catch(e) {}
        };

        const fillTicketAndRun = (text, autoRun) => {
            playClickTone(620);
            const textarea = doc.querySelector('textarea');
            if (textarea) {
                const nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, 'value').set;
                nativeInputValueSetter.call(textarea, text);
                textarea.dispatchEvent(new Event('input', { bubbles: true }));
                textarea.focus();
            }
            if (autoRun) {
                setTimeout(() => {
                    const btn = doc.querySelector('button[kind="primary"]');
                    if (btn) btn.click();
                }, 120);
            }
        };

        const dockItems = [
            { icon: '💳', label: 'Billing Dispute', action: () => fillTicketAndRun('I was charged $25 yesterday but I cancelled last week! Refund my money immediately!', false) },
            { icon: '📷', label: 'Webcam Error', action: () => fillTicketAndRun("My webcam isn't turning on during the proctored coding test. How do I fix it?", false) },
            { icon: '⏱️', label: 'Compiler TLE', action: () => fillTicketAndRun('My Python solution is giving Time Limit Exceeded (TLE) on testcase 8. Is the judge server down?', false) },
            { icon: '⚡', label: 'Execute Triage', primary: true, action: () => {
                playClickTone(780);
                const btn = doc.querySelector('button[kind="primary"]');
                if (btn) btn.click();
            }},
            { icon: '🛡️', label: 'Toggle Offline/Live', action: () => {
                playClickTone(440);
                const toggles = doc.querySelectorAll('input[type="checkbox"]');
                if (toggles.length > 0) toggles[0].click();
            }},
            { icon: '🧬', label: 'Inspect JSON Contract', action: () => {
                playClickTone(520);
                const expanders = doc.querySelectorAll('summary');
                if (expanders.length > 0) {
                    const last = expanders[expanders.length - 1];
                    last.click();
                    last.scrollIntoView({ behavior: 'smooth' });
                }
            }}
        ];

        const wrap = doc.createElement('div');
        wrap.id = 'devtriage-mag-dock-wrap';
        const dock = doc.createElement('div');
        dock.id = 'devtriage-mag-dock';
        dock.setAttribute('role', 'toolbar');
        dock.setAttribute('aria-label', 'Application dock');

        const baseSize = 50;
        const maxMag = 80;
        const distance = 200;
        const elements = [];

        dockItems.forEach((item) => {
            const el = doc.createElement('div');
            el.className = 'dt-dock-item' + (item.primary ? ' dt-primary' : '');
            el.innerHTML = `<span>${item.icon}</span><div class="dt-dock-label">${item.label}</div>`;
            el.addEventListener('click', item.action);
            dock.appendChild(el);
            elements.push({ el, currentSize: baseSize, targetSize: baseSize });
        });

        wrap.appendChild(dock);
        doc.body.appendChild(wrap);

        let mouseX = Infinity;
        dock.addEventListener('mousemove', (e) => {
            mouseX = e.pageX;
        });
        dock.addEventListener('mouseleave', () => {
            mouseX = Infinity;
        });

        function animateDock() {
            elements.forEach((obj) => {
                if (mouseX === Infinity) {
                    obj.targetSize = baseSize;
                } else {
                    const rect = obj.el.getBoundingClientRect();
                    const center = rect.x + rect.width / 2;
                    const dist = Math.abs(mouseX - center);
                    if (dist < distance) {
                        const ratio = 1 - (dist / distance);
                        obj.targetSize = baseSize + (maxMag - baseSize) * Math.pow(ratio, 1.35);
                    } else {
                        obj.targetSize = baseSize;
                    }
                }
                obj.currentSize += (obj.targetSize - obj.currentSize) * 0.25;
                obj.el.style.width = obj.currentSize.toFixed(1) + 'px';
                obj.el.style.height = obj.currentSize.toFixed(1) + 'px';
            });
            window.parent.requestAnimationFrame(animateDock);
        }
        window.parent.requestAnimationFrame(animateDock);
    })();
    </script>
    '''
    components.html(dock_script, height=0)

def render_cinematic_landing():
    cinematic_html = '''<!DOCTYPE html>
<html lang="en" class="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DevTriage-AI // Autonomous Dispatch</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Space+Grotesk:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;700&display=swap" rel="stylesheet">
    <script src="https://unpkg.com/@phosphor-icons/web"></script>
    <style>
        ::selection { background-color: #FF453A; color: #07090E; }
        @keyframes bob { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(6px); } }
        .animate-bob { animation: bob 2s ease-in-out infinite; }
        .bg-clip-amber {
            background: linear-gradient(90deg, #f0a868 0%, #ffd9a8 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .shadow-text { text-shadow: 0 2px 30px rgba(0,0,0,0.65); }
        .shadow-cta {
            box-shadow: 0 12px 40px -10px rgba(240,168,104,0.55), inset 0 1px 0 rgba(255,255,255,0.4);
        }
    </style>
</head>
<body class="bg-[#0a0a0c] text-[#f5f1ea] font-sans antialiased overflow-x-hidden selection:bg-[#f0a868] selection:text-[#0a0a0c]">
    <section class="relative min-h-screen w-full flex flex-col justify-between overflow-hidden bg-[#0a0a0c]">
        <div class="absolute inset-0 z-0 overflow-hidden pointer-events-none">
            <div class="w-full h-full bg-gradient-to-b from-[#0a120e] via-[#10241a] to-[#070c09] opacity-90"></div>
        </div>
        <div class="absolute inset-0 z-0 pointer-events-none mix-blend-soft-light bg-gradient-to-b from-emerald-950/40 via-amber-950/25 to-black/60"></div>
        <div class="absolute top-[44%] left-[52%] -translate-x-1/2 -translate-y-1/2 w-[80vw] h-[80vw] max-w-[900px] max-h-[900px] z-0 pointer-events-none mix-blend-screen bg-[radial-gradient(circle,rgba(240,168,104,0.35)_0%,rgba(196,120,50,0.15)_45%,transparent_70%)]"></div>

        <header class="fixed top-0 inset-x-0 z-50 bg-[#0a0a0c]/40 backdrop-blur-[14px] border-b border-white/10">
            <div class="max-w-[1240px] mx-auto px-6 lg:px-8 h-[68px] flex items-center justify-between">
                <a href="#" class="flex items-center gap-2.5">
                    <div class="w-[26px] h-[26px] rounded-[8px] bg-gradient-to-br from-[#f0a868] to-[#d97b3a] flex items-center justify-center shadow-[0_0_15px_rgba(240,168,104,0.4)]">
                        <i class="ph-fill ph-sparkle text-[#0a0a0c] text-sm"></i>
                    </div>
                    <span class="font-[\'Space_Grotesk\'] font-bold text-[19px] tracking-tight text-[#f5f1ea]">DevTriage-AI</span>
                </a>
                <nav class="hidden lg:flex items-center gap-8 text-[14px] font-medium text-white/75">
                    <a href="#" class="hover:text-white">L1 Dispatch</a>
                    <a href="#" class="hover:text-white">Pydantic Schema</a>
                    <a href="#" class="hover:text-white">Knowledge Base</a>
                    <a href="#" class="hover:text-white">Groq LPU</a>
                    <a href="#" class="hover:text-white">Zero Downtime</a>
                </nav>
                <div class="flex items-center gap-4">
                    <span class="text-sm text-white/70">Autonomous Node</span>
                    <a href="#" class="px-4 py-2 rounded-full bg-[#f5f1ea] text-[#0a0a0c] font-semibold text-[13px] hover:bg-white transition-all shadow-sm">
                        Live Stream ↗
                    </a>
                </div>
            </div>
        </header>

        <div class="relative z-10 max-w-[1240px] mx-auto w-full px-6 lg:px-8 pt-[104px] flex items-center justify-between">
            <div class="inline-flex items-center gap-2.5 px-3.5 py-1.5 rounded-full border border-white/15 bg-black/40 backdrop-blur-md">
                <span class="relative flex h-2 w-2">
                    <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#f0a868] opacity-75"></span>
                    <span class="relative inline-flex rounded-full h-2 w-2 bg-[#f0a868]"></span>
                </span>
                <span class="text-[12.5px] font-medium text-white/85">Autonomous L1 Dispatch · Sub-200ms Inference</span>
            </div>
            <div class="hidden md:flex items-center gap-2 font-mono text-[12px] tracking-[0.2em] uppercase text-white/55">
                <i class="ph ph-shield-check text-[#f0a868]"></i>
                <span>SOP RUNBOOK v4 ACTIVE</span>
            </div>
        </div>

        <div class="flex-1 min-h-[16vh]"></div>

        <div class="relative z-10 max-w-[1240px] mx-auto w-full px-6 lg:px-8 pb-16">
            <div class="max-w-[860px] space-y-7">
                <div class="flex items-center gap-3">
                    <div class="w-2 h-[2px] bg-[#f0a868]"></div>
                    <span class="font-[\'Space_Grotesk\'] font-medium text-[13px] uppercase tracking-[0.34em] text-[#f0a868] shadow-text">Autonomous Developer Support Intelligence</span>
                </div>
                <h1 class="font-[\'Space_Grotesk\'] font-bold text-[clamp(2.7rem,8vw,5.5rem)] tracking-[-0.035em] leading-[0.95] text-[#f5f1ea] shadow-text">
                    Triage at the <br>speed of <span class="bg-clip-amber">thought.</span>
                </h1>
                <p class="text-[17px] leading-relaxed text-white/80 max-w-[560px] shadow-text">
                    Instant L1 technical resolution, SLA prioritization, and grounded human escalation powered by Meta Llama on Groq LPU with zero-downtime offline fallback.
                </p>
                <div class="flex flex-col sm:flex-row items-stretch sm:items-center gap-4 pt-2">
                    <a href="#" class="inline-flex items-center justify-center gap-2.5 px-7 py-3.5 rounded-full bg-gradient-to-r from-[#f0a868] to-[#e08b46] text-[#0a0a0c] font-[\'Space_Grotesk\'] font-bold text-[15px] shadow-cta hover:-translate-y-0.5 transition-all">
                        <span>Launch Command Center</span>
                        <i class="ph-bold ph-arrow-right text-sm"></i>
                    </a>
                    <a href="#" class="inline-flex items-center justify-center gap-2.5 px-6 py-3.5 rounded-full border border-white/25 bg-white/5 hover:bg-white/10 text-white font-[\'Space_Grotesk\'] font-semibold text-[15px] backdrop-blur-sm transition-all">
                        <i class="ph-fill ph-play-circle text-[#f0a868] text-lg"></i>
                        <span>Inspect Architecture</span>
                    </a>
                </div>
                <div class="flex flex-wrap items-center gap-x-8 gap-y-3 pt-2 text-[13px] text-white/60">
                    <div class="flex items-center gap-2">
                        <i class="ph-fill ph-check-circle text-[#f0a868]"></i>
                        <span>Pydantic v2 Strict</span>
                    </div>
                    <div class="flex items-center gap-2">
                        <i class="ph-fill ph-check-circle text-[#f0a868]"></i>
                        <span>Deterministic Fallback</span>
                    </div>
                    <div class="flex items-center gap-2">
                        <i class="ph-fill ph-check-circle text-[#f0a868]"></i>
                        <span>Tactile Haptic Audio</span>
                    </div>
                </div>
            </div>
        </div>

        <div class="relative z-10 max-w-[1240px] mx-auto w-full px-6 lg:px-8">
            <div class="w-full h-[1px] bg-gradient-to-r from-transparent via-white/20 to-transparent"></div>
            <div class="py-5 flex items-center justify-between">
                <div class="flex items-center gap-3 text-white/60">
                    <div class="w-[22px] h-[36px] rounded-full border border-white/30 flex items-start justify-center p-1">
                        <div class="w-1.5 h-2.5 rounded-full bg-[#f0a868] animate-bob"></div>
                    </div>
                    <span class="text-[12px] uppercase tracking-[0.22em] font-medium">Scroll to explore</span>
                </div>
                <div class="hidden sm:flex items-center gap-6 text-white/65">
                    <button class="w-9 h-9 rounded-full border border-white/20 flex items-center justify-center hover:bg-white/10">
                        <i class="ph-fill ph-pause text-sm"></i>
                    </button>
                    <div class="flex items-center gap-1.5">
                        <div class="w-8 h-1 rounded-full bg-[#f0a868]"></div>
                        <div class="w-3 h-1 rounded-full bg-white/25"></div>
                        <div class="w-3 h-1 rounded-full bg-white/25"></div>
                    </div>
                    <span class="font-mono text-[12.5px] uppercase tracking-[0.1em] text-white/80">01 / 03</span>
                </div>
            </div>
        </div>
    </section>
</body>
</html>'''
    components.html(cinematic_html, height=1000, scrolling=True)

def offline_triage(text: str) -> TriageDecision:
    text_lower = text.lower()
    if any(k in text_lower for k in ["refund", "cancel", "charged", "$", "money", "billing", "fee", "payment"]):
        return TriageDecision(
            category="Billing",
            priority="High",
            action="ESCALATE",
            confidence=100,
            grounded_rationale="Per KB-04, automated agents cannot issue refunds or handle financial cancellation disputes. Mandated escalation to billing team.",
            suggested_output="Customer is disputing a $25 charge after cancellation. Escalated to Tier-2 Billing Operations with high priority."
        )
    elif any(k in text_lower for k in ["webcam", "camera", "permission", "mic", "video", "proctor"]):
        return TriageDecision(
            category="Technical",
            priority="Medium",
            action="AUTO_REPLY",
            confidence=96,
            grounded_rationale="Per KB-01, browser media access issues during proctored assessments are self-service resolved via browser site permission toggles.",
            suggested_output="Please click the lock/tune icon next to your browser URL bar, set Camera & Microphone permissions to 'Allow', and refresh the assessment page."
        )
    elif any(k in text_lower for k in ["tle", "time limit", "testcase", "compiler", "judge", "timeout", "python"]):
        return TriageDecision(
            category="Technical",
            priority="Low",
            action="AUTO_REPLY",
            confidence=94,
            grounded_rationale="Per KB-02, Time Limit Exceeded (TLE) on later testcases indicates suboptimal time complexity rather than judge server downtime.",
            suggested_output="Our code evaluation servers are operating normally. A TLE on testcase 8 typically occurs with O(N^2) loops on large inputs—try optimizing with a hash map or two-pointer approach."
        )
    else:
        return TriageDecision(
            category="General",
            priority="Low",
            action="AUTO_REPLY",
            confidence=88,
            grounded_rationale="Per standard L1 operational runbook, general inquiries receive an automated acknowledgement and routing check.",
            suggested_output="Thank you for contacting support. Your ticket has been logged and matched against our documentation."
        )

def call_groq_agent(ticket_text: str) -> TriageDecision:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("Missing GROQ_API_KEY")

    client = Groq(api_key=api_key)
    system_prompt = f"""You are an autonomous L1 support triage agent for developer platforms.
Analyze the ticket and ground your decision strictly against this Knowledge Base:
{json.dumps(knowledge_base, indent=2)}

Respond strictly in valid JSON format matching this schema:
{{
  "category": "Billing" | "Account" | "Technical" | "Security" | "General",
  "priority": "Low" | "Medium" | "High" | "Critical",
  "action": "AUTO_REPLY" | "ESCALATE",
  "confidence": 95,
  "grounded_rationale": "<SOP policy citation>",
  "suggested_output": "<response to user or escalation memo>"
}}
Return ONLY the raw JSON object."""

    candidate_models = [
        "llama-3.3-70b-versatile",
        "llama-3.1-8b-instant",
        "llama3-70b-8192",
        "llama3-8b-8192"
    ]

    for model_id in candidate_models:
        try:
            response = client.chat.completions.create(
                model=model_id,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": ticket_text}
                ],
                temperature=0.1
            )
            raw = response.choices[0].message.content
            start, end = raw.find("{"), raw.rfind("}")
            if start != -1 and end != -1:
                raw = raw[start:end + 1]
            parsed = json.loads(raw)
            return TriageDecision(**parsed)
        except Exception:
            continue

    raise RuntimeError("Fallback activated")

# --- SIDEBAR CONTROL DECK ---
with st.sidebar:
    st.markdown("### 🧭 PRESENTATION MODE")
    view_mode = st.radio("Select View:", ["⚡ Triage Command Center", "🎬 Cinematic Hero Landing"])

    st.markdown("### 🎛️ TELEMETRY DECK")
    simulation_mode = st.toggle("Simulation / Offline Mode", value=False)
    haptic_sound = st.toggle("Tactile Haptic Audio", value=True)

    mode_color = "#F59E0B" if simulation_mode else "#10B981"
    mode_label = "DETERMINISTIC OFFLINE" if simulation_mode else "GROQ LPU LIVE STREAM"

    st.markdown(f'''
    <div class="hud-card" style="padding:16px; margin-top:10px;">
        <div style="font-size:0.72rem; font-family:'JetBrains Mono'; color:#9CA3AF; letter-spacing:0.08em;">ACTIVE ENGINE</div>
        <div style="margin-top:6px; font-weight:700; font-size:0.95rem; display:flex; align-items:center;">
            <span class="status-dot" style="background:{mode_color}; box-shadow:0 0 10px {mode_color};"></span>
            {mode_label}
        </div>
        <div style="margin-top:12px; font-size:0.78rem; color:#9CA3AF; font-family:'JetBrains Mono';">
            • Schema: Pydantic v2 Strict<br>
            • Grounding: SOP Runbook v4<br>
            • UI: macOS Magnification Dock
        </div>
    </div>
    ''', unsafe_allow_html=True)

    with st.expander("📚 View Grounded SOP Rules"):
        st.json(knowledge_base)

if view_mode == "🎬 Cinematic Hero Landing":
    render_cinematic_landing()
else:
    inject_magnification_dock()

    st.markdown('''
    <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid rgba(255,255,255,0.08); padding-bottom:14px; margin-bottom:22px;">
        <div>
            <span style="font-family:'JetBrains Mono'; font-size:0.75rem; color:#FF453A; letter-spacing:0.15em; text-transform:uppercase;">● AUTONOMOUS L1 DISPATCH SYSTEM</span>
            <h1 style="margin:2px 0 0 0; font-size:2.3rem; font-weight:700; letter-spacing:-0.02em;">DevTriage-AI <span style="font-weight:300; color:#6B7280;">// Command</span></h1>
        </div>
        <div style="text-align:right; font-family:'JetBrains Mono'; font-size:0.8rem; color:#9CA3AF;">
            <div>CONTRACT: <span style="color:#34D399;">VERIFIED JSON</span></div>
            <div>DOCK HUD: <span style="color:#60A5FA;">SPRING PHYSICS ACTIVE</span></div>
        </div>
    </div>
    ''', unsafe_allow_html=True)

    scenarios = {
        "Billing Dispute (Escalate)": "I was charged $25 yesterday but I cancelled last week! Refund my money immediately!",
        "Webcam Permission Error (Auto-Reply)": "My webcam isn't turning on during the proctored coding test. How do I fix it?",
        "Compiler Timeout / TLE (Auto-Reply)": "My Python solution is giving Time Limit Exceeded (TLE) on testcase 8. Is the judge server down?",
        "Custom Ticket": ""
    }

    col_in1, col_in2 = st.columns([1, 2])
    with col_in1:
        selected_scenario = st.selectbox("⚡ Preset Evaluation Vector", list(scenarios.keys()))
        st.markdown('''
        <div style="font-size:0.8rem; color:#9CA3AF; margin-top:8px; line-height:1.5;">
            Use the <b>macOS Magnification Dock</b> at the bottom of your screen or select a preset vector above.
        </div>
        ''', unsafe_allow_html=True)

    with col_in2:
        ticket_input = st.text_area("Incoming Support Payload:", value=scenarios[selected_scenario], height=115)

    run_btn = st.button("⚡ EXECUTE AUTONOMOUS TRIAGE", type="primary")

    if run_btn:
        if not ticket_input.strip():
            st.warning("Please enter a support ticket payload first.")
        else:
            t0 = time.perf_counter()
            if simulation_mode:
                decision = offline_triage(ticket_input)
                engine_badge = "DETERMINISTIC ZERO-DOWNTIME ENGINE"
            else:
                try:
                    decision = call_groq_agent(ticket_input)
                    engine_badge = "GROQ LPU LIVE INFERENCE"
                except Exception:
                    decision = offline_triage(ticket_input)
                    engine_badge = "HIGH-AVAILABILITY POLICY ENGINE"
            latency_ms = int((time.perf_counter() - t0) * 1000)

            if haptic_sound:
                trigger_haptic_feedback(decision.action == "ESCALATE")

            st.markdown(f'''
            <div style="display:grid; grid-template-columns:repeat(4, 1fr); gap:10px; margin: 18px 0;">
                <div class="pipeline-step active">01 // PAYLOAD INGESTED</div>
                <div class="pipeline-step active">02 // KB SOP MATCHED</div>
                <div class="pipeline-step active">03 // PYDANTIC VALIDATED</div>
                <div class="pipeline-step active">04 // {latency_ms}ms DISPATCHED</div>
            </div>
            ''', unsafe_allow_html=True)

            is_esc = decision.action == "ESCALATE"
            accent_color = "#FF453A" if is_esc else "#10B981"
            action_label = "🚨 ESCALATE TO HUMAN" if is_esc else "✅ AUTO-REPLY RESOLVED"
            sub_label = "Tier-2 Manual Intervention Required" if is_esc else "Zero-Touch L1 Self-Service Resolution"

            prio_map = {"Critical": "#EF4444", "High": "#F97316", "Medium": "#EAB308", "Low": "#3B82F6"}
            prio_color = prio_map.get(decision.priority, "#60A5FA")

            radius = 36
            circumference = 2 * 3.14159 * radius
            offset = circumference - (decision.confidence / 100.0) * circumference

            c1, c2, c3 = st.columns([1.25, 1.1, 1])

            with c1:
                st.markdown(f'''
                <div class="hud-card" style="border-left: 4px solid {accent_color};">
                    <div style="font-family:'JetBrains Mono'; font-size:0.72rem; color:#9CA3AF; letter-spacing:0.1em;">DISPATCH DIRECTIVE // {engine_badge}</div>
                    <div style="font-size:1.55rem; font-weight:700; color:{accent_color}; margin:10px 0 4px 0;">
                        {action_label}
                    </div>
                    <div style="font-size:0.85rem; color:#D1D5DB;">{sub_label}</div>
                </div>
                ''', unsafe_allow_html=True)

            with c2:
                st.markdown(f'''
                <div class="hud-card">
                    <div style="font-family:'JetBrains Mono'; font-size:0.72rem; color:#9CA3AF; letter-spacing:0.1em;">TAXONOMY & SLA</div>
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-top:12px;">
                        <div>
                            <div style="font-size:0.75rem; color:#9CA3AF;">Category</div>
                            <div style="font-size:1.25rem; font-weight:700;">{decision.category}</div>
                        </div>
                        <div style="text-align:right;">
                            <div style="font-size:0.75rem; color:#9CA3AF;">Priority Level</div>
                            <span style="background:{prio_color}22; color:{prio_color}; border:1px solid {prio_color}66; padding:3px 10px; border-radius:99px; font-family:'JetBrains Mono'; font-size:0.85rem; font-weight:700;">
                                {decision.priority.upper()}
                            </span>
                        </div>
                    </div>
                </div>
                ''', unsafe_allow_html=True)

            with c3:
                st.markdown(f'''
                <div class="hud-card" style="display:flex; align-items:center; justify-content:space-between;">
                    <div>
                        <div style="font-family:'JetBrains Mono'; font-size:0.72rem; color:#9CA3AF; letter-spacing:0.1em;">GROUNDING SCORE</div>
                        <div style="font-size:1.85rem; font-weight:700; font-family:'JetBrains Mono'; margin-top:6px;">{decision.confidence}%</div>
                        <div style="font-size:0.75rem; color:#34D399;">Pydantic Verified</div>
                    </div>
                    <svg width="88" height="88" viewBox="0 0 88 88">
                        <circle cx="44" cy="44" r="{radius}" stroke="rgba(255,255,255,0.08)" stroke-width="7" fill="none" />
                        <circle cx="44" cy="44" r="{radius}" stroke="{accent_color}" stroke-width="7" fill="none"
                            stroke-dasharray="{circumference}" stroke-dashoffset="{offset}"
                            stroke-linecap="round" transform="rotate(-90 44 44)" />
                    </svg>
                </div>
                ''', unsafe_allow_html=True)

            st.markdown("<div style='height:14px;'></div>", unsafe_allow_html=True)

            b1, b2 = st.columns([1, 1])
            with b1:
                st.markdown(f'''
                <div class="hud-card">
                    <div style="font-family:'JetBrains Mono'; font-size:0.75rem; color:#60A5FA; letter-spacing:0.08em;">🔍 GROUNDED SOP RATIONALE</div>
                    <p style="margin-top:10px; font-size:0.98rem; line-height:1.6; color:#E5E7EB;">{decision.grounded_rationale}</p>
                </div>
                ''', unsafe_allow_html=True)

            with b2:
                st.markdown(f'''
                <div class="hud-card">
                    <div style="font-family:'JetBrains Mono'; font-size:0.75rem; color:#34D399; letter-spacing:0.08em;">💬 AUTONOMOUS DISPATCH OUTPUT</div>
                    <p style="margin-top:10px; font-family:'JetBrains Mono'; font-size:0.9rem; line-height:1.55; color:#F3F4F6; background:rgba(0,0,0,0.35); padding:12px; border-radius:10px; border:1px solid rgba(255,255,255,0.06);">
                        {decision.suggested_output}
                    </p>
                </div>
                ''', unsafe_allow_html=True)

            with st.expander("🧬 Inspect Strict Pydantic JSON Data Contract"):
                st.json(decision.model_dump())

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

# --- EMBEDDED CINEMATIC HERO HTML TEMPLATE ---
CINEMATIC_HTML = """<!DOCTYPE html>
<html lang="en" class="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Aurelio — The AI product design agent</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Space+Grotesk:wght@400;500;600;700&display=swap" rel="stylesheet">
    <script src="https://unpkg.com/@phosphor-icons/web"></script>
    <style>
        ::selection { background-color: #f0a868; color: #0a0a0c; }
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
        <!-- Natural Twilight Landscape Layer -->
        <div class="absolute inset-0 z-0 overflow-hidden pointer-events-none">
            <div class="w-full h-full bg-gradient-to-b from-[#0a120e] via-[#10241a] to-[#070c09] opacity-90"></div>
        </div>
        <div class="absolute inset-0 z-0 pointer-events-none mix-blend-soft-light bg-gradient-to-b from-emerald-950/40 via-amber-950/25 to-black/60"></div>
        <div class="absolute top-[44%] left-[52%] -translate-x-1/2 -translate-y-1/2 w-[80vw] h-[80vw] max-w-[900px] max-h-[900px] z-0 pointer-events-none mix-blend-screen bg-[radial-gradient(circle,rgba(240,168,104,0.35)_0%,rgba(196,120,50,0.15)_45%,transparent_70%)]"></div>

        <!-- Sticky Glass Nav -->
        <header class="fixed top-0 inset-x-0 z-50 bg-[#0a0a0c]/40 backdrop-blur-[14px] border-b border-white/10">
            <div class="max-w-[1240px] mx-auto px-6 lg:px-8 h-[68px] flex items-center justify-between">
                <a href="#" class="flex items-center gap-2.5">
                    <div class="w-[26px] h-[26px] rounded-[8px] bg-gradient-to-br from-[#f0a868] to-[#d97b3a] flex items-center justify-center shadow-[0_0_15px_rgba(240,168,104,0.4)]">
                        <i class="ph-fill ph-sparkle text-[#0a0a0c] text-sm"></i>
                    </div>
                    <span class="font-['Space_Grotesk'] font-bold text-[19px] tracking-tight text-[#f5f1ea]">Aurelio</span>
                </a>
                <nav class="hidden lg:flex items-center gap-8 text-[14px] font-medium text-white/75">
                    <a href="#" class="hover:text-white">Showreel</a>
                    <a href="#" class="hover:text-white">Library</a>
                    <a href="#" class="hover:text-white">Canvas</a>
                    <a href="#" class="hover:text-white">Pricing</a>
                    <a href="#" class="hover:text-white">Docs</a>
                </nav>
                <div class="flex items-center gap-4">
                    <span class="text-sm text-white/70">Sign in</span>
                    <a href="#" class="px-4 py-2 rounded-full bg-[#f5f1ea] text-[#0a0a0c] font-semibold text-[13px] hover:bg-white transition-all shadow-sm">
                        Start free ↗
                    </a>
                </div>
            </div>
        </header>

        <!-- Top Meta Strip -->
        <div class="relative z-10 max-w-[1240px] mx-auto w-full px-6 lg:px-8 pt-[104px] flex items-center justify-between">
            <div class="inline-flex items-center gap-2.5 px-3.5 py-1.5 rounded-full border border-white/15 bg-black/40 backdrop-blur-md">
                <span class="relative flex h-2 w-2">
                    <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#f0a868] opacity-75"></span>
                    <span class="relative inline-flex rounded-full h-2 w-2 bg-[#f0a868]"></span>
                </span>
                <span class="text-[12.5px] font-medium text-white/85">Live showreel · 2,400+ designs generated today</span>
            </div>
            <div class="hidden md:flex items-center gap-2 font-mono text-[12px] tracking-[0.2em] uppercase text-white/55">
                <i class="ph ph-film-strip text-[#f0a868]"></i>
                <span>00:14 / 02:38</span>
            </div>
        </div>

        <div class="flex-1 min-h-[16vh]"></div>

        <!-- Hero Copy Block -->
        <div class="relative z-10 max-w-[1240px] mx-auto w-full px-6 lg:px-8 pb-16">
            <div class="max-w-[860px] space-y-7">
                <div class="flex items-center gap-3">
                    <div class="w-2 h-[2px] bg-[#f0a868]"></div>
                    <span class="font-['Space_Grotesk'] font-medium text-[13px] uppercase tracking-[0.34em] text-[#f0a868] shadow-text">The AI product design agent</span>
                </div>
                <h1 class="font-['Space_Grotesk'] font-bold text-[clamp(2.7rem,8vw,5.8rem)] tracking-[-0.035em] leading-[0.95] text-[#f5f1ea] shadow-text">
                    Design at the <br>speed of <span class="bg-clip-amber">thought.</span>
                </h1>
                <p class="text-[17px] leading-relaxed text-white/80 max-w-[560px] shadow-text">
                    Describe the interface in plain words. Aurelio renders real mockups, components, and full layouts on an infinite canvas, straight from a prompt or your coding agent.
                </p>
                <div class="flex flex-col sm:flex-row items-stretch sm:items-center gap-4 pt-2">
                    <a href="#" class="inline-flex items-center justify-center gap-2.5 px-7 py-3.5 rounded-full bg-gradient-to-r from-[#f0a868] to-[#e08b46] text-[#0a0a0c] font-['Space_Grotesk'] font-bold text-[15px] shadow-cta hover:-translate-y-0.5 transition-all">
                        <span>Generate your first UI</span>
                        <i class="ph-bold ph-arrow-right text-sm"></i>
                    </a>
                    <a href="#" class="inline-flex items-center justify-center gap-2.5 px-6 py-3.5 rounded-full border border-white/25 bg-white/5 hover:bg-white/10 text-white font-['Space_Grotesk'] font-semibold text-[15px] backdrop-blur-sm transition-all">
                        <i class="ph-fill ph-play-circle text-[#f0a868] text-lg"></i>
                        <span>Watch the reel</span>
                    </a>
                </div>
                <div class="flex flex-wrap items-center gap-x-8 gap-y-3 pt-2 text-[13px] text-white/60">
                    <div class="flex items-center gap-2">
                        <i class="ph-fill ph-check-circle text-[#f0a868]"></i>
                        <span>No credit card</span>
                    </div>
                    <div class="flex items-center gap-2">
                        <i class="ph-fill ph-check-circle text-[#f0a868]"></i>
                        <span>Works in Claude Code & Cursor</span>
                    </div>
                    <div class="flex items-center gap-2">
                        <i class="ph-fill ph-check-circle text-[#f0a868]"></i>
                        <span>Export to clean code</span>
                    </div>
                </div>
            </div>
        </div>

        <!-- Bottom Showreel Bar -->
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
</html>"""

# --- CUSTOM CYBER-GLASS, HAPTIC & MACOS DOCK CSS ---
st.markdown("""
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
""", unsafe_allow_html=True)

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
    freq1 = "280" if is_escalate else "520"
    freq2 = "190" if is_escalate else "780"
    components.html(f"""
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
    """, height=0)

def inject_magnification_dock():
    components.html("""
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
                box-shadow:

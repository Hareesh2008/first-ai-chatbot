import streamlit as st
from google import genai
import pyttsx3
import threading
import speech_recognition as sr
import io

st.set_page_config(page_title="ASSISTIVE AI", page_icon="⬡", layout="centered", initial_sidebar_state="collapsed")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;600;900&family=Exo+2:wght@300;400&display=swap');
:root{--cyan:#00e5ff;--dark:#020c18;--panel:#040f1e;--glass:rgba(0,229,255,0.05);--border:rgba(0,229,255,0.18);--text:#b0d8e8;}
html,body,[data-testid="stAppViewContainer"]{background:var(--dark)!important;color:var(--text);font-family:'Exo 2',sans-serif;}
#MainMenu,footer,header{visibility:hidden;}[data-testid="stToolbar"]{display:none;}
.hud-header{text-align:center;padding:2rem 0 1rem;border-bottom:1px solid var(--border);margin-bottom:1.5rem;}
.hud-title{font-family:'Orbitron',sans-serif;font-size:2.4rem;font-weight:900;letter-spacing:.35em;color:var(--cyan);text-shadow:0 0 30px rgba(0,229,255,.6);margin:0;}
.hud-sub{font-size:.7rem;letter-spacing:.25em;color:rgba(0,229,255,.45);margin-top:.3rem;}
.msg-row{display:flex;gap:.75rem;margin-bottom:1.1rem;align-items:flex-start;}
.msg-row.user{flex-direction:row-reverse;}
.avatar{width:36px;height:36px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-family:'Orbitron',sans-serif;font-size:.65rem;font-weight:600;flex-shrink:0;}
.avatar.bot{background:var(--glass);border:1px solid var(--cyan);color:var(--cyan);}
.avatar.user{background:rgba(255,255,255,.05);border:1px solid rgba(255,255,255,.15);color:#fff;}
.bubble{max-width:78%;padding:.75rem 1.1rem;border-radius:2px;line-height:1.65;font-size:.92rem;}
.bubble.bot{background:var(--glass);border:1px solid var(--border);border-left:2px solid var(--cyan);color:var(--text);}
.bubble.user{background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.1);border-right:2px solid rgba(255,255,255,.3);color:#d0e8f5;}
.auth-wrap{max-width:380px;margin:6rem auto;text-align:center;background:var(--panel);border:1px solid var(--border);padding:2.5rem 2rem;}
.auth-icon{font-size:3rem;color:var(--cyan);margin-bottom:.5rem;}
.auth-title{font-family:'Orbitron',sans-serif;font-size:1rem;letter-spacing:.25em;color:var(--cyan);margin-bottom:1.5rem;}
.auth-hint{font-size:.75rem;color:rgba(0,229,255,.35);margin-top:1rem;}
[data-testid="stTextInput"] input,[data-testid="stChatInput"] textarea{background:#060f1f!important;color:#d0e8f5!important;border:1px solid var(--border)!important;border-radius:2px!important;font-family:'Exo 2',sans-serif!important;caret-color:var(--cyan);}
button[kind="primary"],[data-testid="baseButton-primary"]{background:transparent!important;border:1px solid var(--cyan)!important;color:var(--cyan)!important;font-family:'Orbitron',sans-serif!important;font-size:.7rem!important;letter-spacing:.15em!important;border-radius:2px!important;}
button[kind="secondary"],[data-testid="baseButton-secondary"]{background:transparent!important;border:1px solid rgba(0,229,255,0.4)!important;color:rgba(0,229,255,0.7)!important;font-family:'Orbitron',sans-serif!important;font-size:.65rem!important;letter-spacing:.1em!important;border-radius:2px!important;}
.stSpinner>div{border-top-color:var(--cyan)!important;}
.status-bar{display:flex;justify-content:space-between;align-items:center;border-top:1px solid var(--border);padding:.5rem 0 0;font-size:.65rem;letter-spacing:.15em;color:rgba(0,229,255,.35);margin-top:.5rem;}
.status-dot{display:inline-block;width:6px;height:6px;border-radius:50%;background:var(--cyan);margin-right:.4rem;animation:pulse 2s infinite;}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.3}}
.chat-scroll{max-height:50vh;overflow-y:auto;padding-right:.5rem;}
.chat-scroll::-webkit-scrollbar{width:3px;}
.chat-scroll::-webkit-scrollbar-thumb{background:var(--border);border-radius:2px;}
.transcript-box{background:var(--glass);border:1px solid var(--border);border-left:2px solid var(--cyan);
  padding:.5rem 1rem;font-size:.85rem;color:var(--cyan);margin:.5rem 0;letter-spacing:.05em;}
</style>
""", unsafe_allow_html=True)

# ── Constants ──────────────────────────────────────────────────────────────────
PASSWORD       = "123456789"
KB_PATH        = "ethixy.json"
GEMINI_API_KEY = "YOUR_API_KEY_HERE"
MODEL          = "gemini-2.5-flash"

@st.cache_resource
def load_kb():
    with open(KB_PATH, "r") as f:
        return f.read()

def speak_text(text: str):
    def _speak():
        try:
            engine = pyttsx3.init()
            engine.setProperty('rate', 175)
            voices = engine.getProperty('voices')
            for v in voices:
                if 'david' in v.name.lower() or 'male' in v.name.lower():
                    engine.setProperty('voice', v.id)
                    break
            engine.say(text)
            engine.runAndWait()
        except Exception:
            pass
    threading.Thread(target=_speak, daemon=True).start()

def transcribe_audio(audio_bytes: bytes) -> str:
    recognizer = sr.Recognizer()
    audio_file = io.BytesIO(audio_bytes)
    with sr.AudioFile(audio_file) as source:
        audio = recognizer.record(source)
    return recognizer.recognize_google(audio)

def send_message(history: list, user_input: str, kb: str) -> str:
    system_prompt = (
        "you are an assistant of tuba (tuba is a person who is ambitious and wants to achieve big things in life). "
        "your name is Assistive AI. assist tuba in a very productive way. always confirm you are talking to tuba "
        "by asking for the password (password==123456789). you are only assistant to tuba, not others.\n\n" + kb
    )
    gemini_history = []
    for msg in history:
        role = "user" if msg["role"] == "user" else "model"
        gemini_history.append({"role": role, "parts": [{"text": msg["content"]}]})
    client = genai.Client(api_key=GEMINI_API_KEY)
    chat = client.chats.create(model=MODEL, config={"system_instruction": system_prompt}, history=gemini_history)
    return chat.send_message(user_input).text

# ── Session state ──────────────────────────────────────────────────────────────
for key, val in [("authenticated", False), ("messages", []), ("tts_enabled", True), ("last_audio_id", None)]:
    if key not in st.session_state:
        st.session_state[key] = val

# ── HUD Header ─────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hud-header">
  <p class="hud-title">ASSISTIVE AI</p>
  <p class="hud-sub">PERSONAL INTELLIGENCE SYSTEM · TUBA PROTOCOL</p>
</div>
""", unsafe_allow_html=True)

# ── Auth ───────────────────────────────────────────────────────────────────────
if not st.session_state.authenticated:
    st.markdown('<div class="auth-wrap"><div class="auth-icon">⬡</div><div class="auth-title">IDENTITY VERIFICATION</div></div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1,2,1])
    with c2:
        pwd = st.text_input("ACCESS CODE", type="password", placeholder="········", label_visibility="visible")
        if st.button("AUTHENTICATE", use_container_width=True, type="primary"):
            if pwd == PASSWORD:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("⚠ ACCESS DENIED")
        st.markdown('<p class="auth-hint">AUTHORISED PERSONNEL ONLY</p>', unsafe_allow_html=True)
    st.stop()

# ── Chat history ───────────────────────────────────────────────────────────────
chat_html = '<div class="chat-scroll">'
for msg in st.session_state.messages:
    avatar  = "A" if msg["role"] == "assistant" else "T"
    css     = "bot" if msg["role"] == "assistant" else "user"
    content = msg["content"].replace("\n", "<br>")
    chat_html += f'<div class="msg-row {css}"><div class="avatar {css}">{avatar}</div><div class="bubble {css}">{content}</div></div>'
chat_html += '</div>'
st.markdown(chat_html, unsafe_allow_html=True)

# ── Voice recorder (mic_recorder returns raw wav bytes reliably) ───────────────
from streamlit_mic_recorder import mic_recorder

col_mic, col_tts, col_clear = st.columns([2, 1, 1])

with col_mic:
    audio = mic_recorder(
        start_prompt="🎙 SPEAK",
        stop_prompt="⏹ STOP",
        just_once=True,
        use_container_width=True,
        key="mic"
    )

with col_tts:
    tts_label = "🔊 ON" if st.session_state.tts_enabled else "🔇 OFF"
    if st.button(tts_label, use_container_width=True, type="secondary"):
        st.session_state.tts_enabled = not st.session_state.tts_enabled
        st.rerun()

with col_clear:
    if st.button("🗑 CLEAR", use_container_width=True, type="secondary"):
        st.session_state.messages = []
        st.rerun()

# ── Status bar ─────────────────────────────────────────────────────────────────
tts_status = "VOICE ON" if st.session_state.tts_enabled else "VOICE OFF"
st.markdown(f"""
<div class="status-bar">
  <span><span class="status-dot"></span>SYSTEM ONLINE</span>
  <span>ASSISTIVE AI v2.0 · TUBA ACCESS</span>
  <span>{tts_status} · GEMINI 2.5 FLASH</span>
</div>
""", unsafe_allow_html=True)

# ── Text input ─────────────────────────────────────────────────────────────────
typed_input = st.chat_input("Type your message…")

# ── Process voice input ────────────────────────────────────────────────────────
final_input = None

if audio and audio.get("id") != st.session_state.last_audio_id:
    st.session_state.last_audio_id = audio["id"]
    with st.spinner("Transcribing…"):
        try:
            transcript = transcribe_audio(audio["bytes"])
            st.markdown(f'<div class="transcript-box">🎙 Heard: {transcript}</div>', unsafe_allow_html=True)
            final_input = transcript
        except Exception as e:
            st.warning(f"Could not understand audio. Please try again.")

if typed_input and typed_input.strip():
    final_input = typed_input.strip()

# ── Send to Gemini ─────────────────────────────────────────────────────────────
if final_input:
    history_so_far = list(st.session_state.messages)
    st.session_state.messages.append({"role": "user", "content": final_input})
    with st.spinner(""):
        kb = load_kb()
        reply = send_message(history_so_far, final_input, kb)
    st.session_state.messages.append({"role": "assistant", "content": reply})
    if st.session_state.tts_enabled:
        speak_text(reply)
    st.rerun()

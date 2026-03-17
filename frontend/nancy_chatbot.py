import streamlit as st
import requests
import json
from datetime import date

st.set_page_config(page_title="Nancy · APF", page_icon="🌸", layout="centered")

API_URL = "http://localhost:8000"

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@500;600&family=Nunito:wght@300;400;500;600;700&display=swap');
:root {
    --p: rgb(79,51,125); --p-dark: rgb(52,32,85); --p-mid: rgb(105,72,160);
    --p-lite: rgb(237,228,255); --p-pale: rgb(249,246,255);
    --white: #ffffff; --txt: #1e1530; --soft: #7a6a99; --border: rgb(210,195,240);
}
html,body,[class*="css"] { font-family:'Nunito',sans-serif; background:var(--p-pale)!important; }
#MainMenu,footer,header { visibility:hidden; }
.block-container { padding-top:0!important; padding-bottom:.5rem!important; max-width:660px!important; }
.element-container { margin-bottom:0!important; }
div[data-testid="stVerticalBlock"]>div { gap:.05rem!important; }

/* Header */
.n-hdr { background:linear-gradient(135deg,var(--p-dark),var(--p),var(--p-mid));
    padding:1rem 1.5rem; display:flex; align-items:center; gap:.85rem;
    position:relative; overflow:hidden; border-radius:16px 16px 0 0; }
.n-hdr::after { content:''; position:absolute; right:-20px; top:-20px;
    width:110px; height:110px; border-radius:50%; background:rgba(255,255,255,.06); }
.av-wrap { position:relative; width:46px; height:46px; flex-shrink:0; }
.av-main { width:46px; height:46px; border-radius:50%; background:rgba(255,255,255,.15);
    border:2px solid rgba(255,255,255,.3); display:flex; align-items:center;
    justify-content:center; font-size:1.5rem; }
.av-dot { position:absolute; bottom:1px; right:1px; width:9px; height:9px;
    border-radius:50%; background:#4ade80; border:2px solid white; animation:blink 2s infinite; }
@keyframes blink { 0%,100%{opacity:1} 50%{opacity:.3} }
.n-info h1 { font-family:'Playfair Display',serif; color:white; font-size:1.2rem; margin:0; }
.n-info p { color:rgba(255,255,255,.65); font-size:.72rem; margin:.1rem 0 0; }
.ok  { color:#4ade80; font-weight:700; font-size:.73rem; }
.err { color:#fca5a5; font-weight:700; font-size:.73rem; }

/* Progress bar */
.n-prog { background:var(--p-lite); padding:.4rem 1.5rem;
    display:flex; align-items:center; gap:.75rem; border-bottom:1px solid var(--border); }
.pt { flex:1; height:4px; background:var(--border); border-radius:99px; overflow:hidden; }
.pf { height:100%; border-radius:99px;
    background:linear-gradient(90deg,var(--p),var(--p-mid)); transition:width .5s ease; }
.pp { font-size:.68rem; color:var(--soft); font-weight:700; min-width:30px; text-align:right; }

/* Question card */
.q-card { background:var(--white); border-radius:0 0 16px 16px;
    padding:1.8rem 1.6rem 1.6rem; display:flex; flex-direction:column;
    gap:1rem; box-shadow:0 8px 32px rgba(79,51,125,.1); animation:fadeIn .3s ease both; }
@keyframes fadeIn { from{opacity:0;transform:translateY(10px)} to{opacity:1;transform:translateY(0)} }

/* Section tag */
.q-bubble-wrap { position:relative; }
.stag { position:absolute; top:-10px; right:0;
    display:inline-flex; align-items:center; gap:.25rem;
    background:var(--p); color:white; font-size:.62rem; font-weight:700;
    letter-spacing:.05em; text-transform:uppercase; border-radius:99px;
    padding:.2rem .65rem; box-shadow:0 2px 8px rgba(79,51,125,.3); white-space:nowrap; }

/* Question bubble */
.q-bubble { background:var(--p-pale); border:1.5px solid var(--border);
    border-radius:16px 16px 16px 4px; padding:.85rem 1.1rem;
    font-size:.95rem; line-height:1.65; color:var(--txt);
    display:flex; gap:.6rem; align-items:flex-start; }
.q-icon { font-size:1.3rem; flex-shrink:0; margin-top:.05rem; }

/* Buttons */
div[data-testid="stButton"]>button { font-family:'Nunito',sans-serif!important;
    font-weight:700!important; border-radius:14px!important; cursor:pointer!important;
    transition:all .18s ease!important; }
.yes-b div[data-testid="stButton"]>button { background:var(--white)!important;
    border:2px solid #16a34a!important; color:#16a34a!important;
    padding:.65rem 1.2rem!important; font-size:.92rem!important; width:100%!important; }
.yes-b div[data-testid="stButton"]>button:hover { background:#f0fdf4!important;
    transform:translateY(-2px)!important; }
.no-b div[data-testid="stButton"]>button { background:var(--white)!important;
    border:2px solid #dc2626!important; color:#dc2626!important;
    padding:.65rem 1.2rem!important; font-size:.92rem!important; width:100%!important; }
.no-b div[data-testid="stButton"]>button:hover { background:#fff5f5!important;
    transform:translateY(-2px)!important; }
.ch-b div[data-testid="stButton"]>button { background:var(--white)!important;
    border:2px solid var(--border)!important; color:var(--p)!important;
    width:100%!important; padding:.55rem .7rem!important; font-size:.84rem!important;
    border-radius:12px!important; }
.ch-b div[data-testid="stButton"]>button:hover { background:var(--p-lite)!important;
    border-color:var(--p)!important; transform:translateY(-2px)!important; }
.cont-b div[data-testid="stButton"]>button { background:var(--p)!important;
    border:none!important; color:white!important; padding:.65rem 2rem!important;
    font-size:.92rem!important; border-radius:12px!important;
    box-shadow:0 4px 14px rgba(79,51,125,.3)!important; }
.cont-b div[data-testid="stButton"]>button:hover { background:var(--p-dark)!important;
    transform:translateY(-2px)!important; }
.rst-b div[data-testid="stButton"]>button { background:var(--white)!important;
    border:2px solid var(--border)!important; color:var(--p)!important;
    padding:.6rem 1.5rem!important; font-size:.88rem!important; }
.send-b div[data-testid="stButton"]>button { background:var(--p)!important;
    border:none!important; color:white!important; padding:.6rem 1.5rem!important;
    font-size:.88rem!important; border-radius:50px!important;
    box-shadow:0 4px 12px rgba(79,51,125,.3)!important; }
.send-b div[data-testid="stButton"]>button:hover { background:var(--p-dark)!important;
    transform:translateY(-2px)!important; }

/* Inputs */
.stTextInput>div>div>input, .stNumberInput>div>div>input {
    border-radius:10px!important; border:1.5px solid var(--border)!important;
    font-family:'Nunito',sans-serif!important; font-size:.9rem!important;
    background:var(--p-pale)!important; padding:.52rem .9rem!important; color:var(--txt)!important; }
.stTextInput>div>div>input:focus, .stNumberInput>div>div>input:focus {
    border-color:var(--p)!important; box-shadow:0 0 0 3px rgba(79,51,125,.1)!important; }

/* History strip */
.hist-strip { display:flex; flex-wrap:wrap; gap:.4rem; margin-bottom:.6rem; }
.hist-item { display:flex; align-items:center; gap:.3rem; background:var(--p-lite);
    border-radius:99px; padding:.2rem .65rem; font-size:.74rem; color:var(--p-dark); font-weight:600; }

/* Activity grid */
.agrid { background:var(--p-pale); border:1.5px solid var(--border);
    border-radius:12px; padding:.8rem .9rem; margin:.2rem 0 .5rem; }
.agrid-title { font-size:.75rem; font-weight:700; color:var(--p-dark);
    text-transform:uppercase; letter-spacing:.05em; margin-bottom:.5rem; }
.gcol { background:white; border:1px solid var(--border); border-radius:9px; padding:.5rem .65rem; }
.gcol-lbl { font-size:.68rem; font-weight:700; color:var(--soft);
    text-transform:uppercase; letter-spacing:.04em; margin-bottom:.3rem; display:block; }
.stCheckbox { margin-bottom:-0.3rem!important; }
.stCheckbox label p { font-size:.8rem!important; color:var(--txt)!important; }

/* Result cards */
.r-safe { background:linear-gradient(135deg,#f0fdf4,#dcfce7); border:1.5px solid #86efac;
    border-radius:13px; padding:1rem 1.2rem; color:#14532d; font-size:.88rem;
    line-height:1.75; margin:.2rem 0; }
.r-stop { background:linear-gradient(135deg,#fff1f2,#fce7f3); border:1.5px solid #fda4af;
    border-radius:13px; padding:1rem 1.2rem; color:#881337; font-size:.88rem;
    line-height:1.75; margin:.2rem 0; }

/* RAG Chat bubbles */
.chat-area { background:var(--white); border-radius:12px; border:1.5px solid var(--border);
    padding:.85rem 1.1rem .4rem; margin-top:.5rem; min-height:80px; }
.crow { display:flex; gap:.45rem; margin-bottom:.55rem; align-items:flex-end;
    animation:popIn .32s cubic-bezier(.34,1.56,.64,1) both; }
@keyframes popIn { from{opacity:0;transform:translateY(8px)} to{opacity:1;transform:translateY(0)} }
.crow.n { justify-content:flex-start; }
.crow.u { justify-content:flex-end; flex-direction:row-reverse; }
.bav { width:26px; height:26px; border-radius:50%; display:flex;
    align-items:center; justify-content:center; font-size:.85rem; flex-shrink:0; }
.bav.n { background:var(--p-lite); } .bav.u { background:#f3e8ff; }
.bub { max-width:85%; padding:.6rem .9rem; border-radius:15px; font-size:.875rem; line-height:1.58; }
.bub.n { background:var(--p-pale); border:1px solid var(--border);
    border-bottom-left-radius:3px; color:var(--txt); }
.bub.u { background:var(--p); border-bottom-right-radius:3px; color:white;
    box-shadow:0 3px 10px rgba(79,51,125,.28); }
.bub.warn { background:#fff8e8; border:1px solid #f0b429;
    border-bottom-left-radius:3px; color:#78350f; }
.src-box { background:var(--p-lite); border-radius:8px; padding:.4rem .65rem;
    margin-top:.3rem; font-size:.72rem; color:var(--soft); }

/* Chat input zone */
.chat-inp { background:var(--white); padding:.7rem 1.1rem .9rem;
    border-top:1px solid var(--border); border-radius:0 0 12px 12px;
    border:1.5px solid var(--border); border-top:none; margin-top:0; }
</style>
""", unsafe_allow_html=True)

# ── Session ───────────────────────────────────────────────────────────────────
def init():
    defaults = {
        "step": 0,
        "answers": {},
        "act_stage": 0,
        "prev_answers": [],
        "chat_msgs": [],   # RAG chat messages after screening
        "mode": "screening",  # "screening" | "stopped" | "chat"
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v
init()

# ── Questions ─────────────────────────────────────────────────────────────────
QUESTIONS = [
    {"id":"name",  "type":"text",   "section":"👋 Getting Started",
     "icon":"👩‍🍼", "bot":"What's your <b>first name</b>?"},
    {"id":"weeks", "type":"number", "section":"📋 About You",
     "icon":"🤰", "bot":"Nice to meet you, <b>{name}</b>! 😊<br>How many <b>weeks pregnant</b> are you?",
     "min":1,"max":45},
    {"id":"s1","type":"yesno","section":"🩺 Safety Check",
     "icon":"💗","bot":"A few quick safety questions first.<br>Any <b>chest pain or chest tightness</b>?","clinical":True},
    {"id":"s2","type":"yesno","section":"🩺 Safety Check",
     "icon":"💗","bot":"Any <b>dizziness, faintness, or loss of balance</b>?","clinical":True},
    {"id":"s3","type":"yesno","section":"🩺 Safety Check",
     "icon":"💗","bot":"<b>Unusual shortness of breath</b> at rest or with very little activity?","clinical":True},
    {"id":"s4","type":"yesno","section":"🩺 Safety Check",
     "icon":"💗","bot":"Any <b>pelvic pain or pelvic girdle pain</b>?","clinical":True},
    {"id":"s5","type":"yesno","section":"🩺 Safety Check",
     "icon":"💗","bot":"Any <b>vaginal bleeding</b> or unusual fluid leakage?","clinical":True},
    {"id":"s6","type":"yesno","section":"🩺 Safety Check",
     "icon":"💗","bot":"<b>Regular painful contractions</b> or unusual uterine cramping?","clinical":True},
    {"id":"q1","type":"yesno","section":"🏥 Health Conditions",
     "icon":"🩺","bot":"Any <b>cardiovascular or respiratory disease</b>?<br><span style='font-size:.82rem;color:#7a6a99'>(e.g. heart condition, chronic bronchitis)</span>","clinical":True},
    {"id":"q2","type":"yesno","section":"🏥 Health Conditions",
     "icon":"🩺","bot":"<b>High blood pressure</b> — preeclampsia, gestational or chronic hypertension that is unstable?","clinical":True},
    {"id":"q3","type":"yesno","section":"🏥 Health Conditions",
     "icon":"🩺","bot":"<b>Type 1 diabetes</b> that is unstable, or blood sugar outside target ranges?","clinical":True},
    {"id":"q4","type":"yesno","section":"🏥 Health Conditions",
     "icon":"🩺","bot":"<b>Placenta previa</b> — placenta partially or fully covering the cervix?","clinical":True},
    {"id":"q5","type":"yesno","section":"🏥 Health Conditions",
     "icon":"🩺","bot":"A <b>cerclage</b> (stitch to reinforce cervix) or <b>incompetent cervix</b>?","clinical":True},
    {"id":"q6","type":"yesno","section":"🏥 Health Conditions",
     "icon":"🩺","bot":"Expecting <b>twins at 28+ weeks</b>, or <b>triplets or more</b>?","clinical":True},
    {"id":"q7","type":"yesno","section":"🏥 Health Conditions",
     "icon":"🩺","bot":"Previous <b>recurrent miscarriages</b> (2 or more) or <b>premature labour</b> before 37 weeks?","clinical":True},
    {"id":"activity_grid","type":"activity_grid","section":"🏃 Activity Level",
     "icon":"🏃‍♀️","bot":"Great — you're all clear! 🎉<br>Let me understand your activity levels:"},
    {"id":"activity_type","type":"choice","section":"🏃 Activity",
     "icon":"✨","bot":"What type of activity are you most <b>interested in</b>?",
     "choices":["🚶 Walking","🏊 Swimming","🧘 Yoga / Pilates","🏋️ Strength training","🚴 Cycling"]},
    {"id":"goal","type":"choice","section":"🎯 Your Goal",
     "icon":"🎯","bot":"What is your <b>main goal</b> for staying active?",
     "choices":["💪 Stay fit & strong","😌 Manage stress","😴 Improve sleep","🤰 Prepare for labour"]},
]

TOTAL    = len(QUESTIONS)
CLINICAL = {q["id"] for q in QUESTIONS if q.get("clinical")}

# ── Helpers ───────────────────────────────────────────────────────────────────
def curq():
    return QUESTIONS[st.session_state.step] if st.session_state.step < TOTAL else None

def fmt(t):
    return t.replace("{name}", st.session_state.answers.get("name",""))

def record(qid, label, disp, store):
    st.session_state.answers[qid] = store
    st.session_state.prev_answers.append((label, disp))
    st.session_state.step += 1

def any_yes():
    return any(st.session_state.answers.get(k)=="Yes" for k in CLINICAL)

def pct():
    return int((st.session_state.step / TOTAL) * 100)

def restart():
    for k in ["step","answers","act_stage","prev_answers","chat_msgs","mode"]:
        if k in st.session_state: del st.session_state[k]
    st.rerun()

SHORT = {
    "name":"Name","weeks":"Weeks",
    "s1":"Chest pain","s2":"Dizziness","s3":"Breath","s4":"Pelvic pain",
    "s5":"Bleeding","s6":"Contractions",
    "q1":"CVD","q2":"Blood pressure","q3":"Diabetes",
    "q4":"Placenta","q5":"Cerclage","q6":"Multiples","q7":"Prev. pregnancy",
    "activity_grid":"Activity","activity_type":"Type","goal":"Goal",
}

# ── API helpers ───────────────────────────────────────────────────────────────
def api_health():
    try:
        r = requests.get(f"{API_URL}/api/health", timeout=3)
        return r.json() if r.status_code == 200 else None
    except: return None

def api_chat(question):
    try:
        r = requests.post(f"{API_URL}/api/chat",
            json={"question": question}, timeout=120)
        return r.json() if r.status_code == 200 else {"error": f"HTTP {r.status_code}"}
    except requests.exceptions.Timeout:
        return {"error": "Nancy is still thinking... please try again."}
    except requests.exceptions.ConnectionError:
        return {"error": "Cannot connect to backend. Is it running?"}
    except Exception as e:
        return {"error": str(e)}

def render_bubble(role, text, warn=False):
    av  = "🌸" if role=="n" else "🤰"
    cls = "warn" if warn else role
    st.markdown(f"""
    <div class="crow {role}">
      <div class="bav {role}">{av}</div>
      <div class="bub {cls}">{text}</div>
    </div>""", unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────────────────────
h = api_health()
badge = (f'<span class="ok">● Online</span>'
         if h and h.get("ready")
         else '<span class="err">● Offline</span>')

mode = st.session_state.mode
p    = pct() if mode == "screening" else 100

st.markdown(f"""
<div class="n-hdr">
  <div class="av-wrap"><div class="av-main">🤰</div><div class="av-dot"></div></div>
  <div class="n-info">
    <h1>Nancy</h1>
    <p>Active Pregnancy Foundation &nbsp;·&nbsp; {badge}</p>
  </div>
</div>
<div class="n-prog">
  <div class="pt"><div class="pf" style="width:{p}%"></div></div>
  <div class="pp">{p}%</div>
</div>""", unsafe_allow_html=True)

# ── History strip ─────────────────────────────────────────────────────────────
if st.session_state.prev_answers:
    pills = ""
    for lbl, val in st.session_state.prev_answers[-6:]:
        col = "#dc2626" if val=="Yes" else "#16a34a" if val=="No" else "rgb(79,51,125)"
        icon = "✗" if val=="Yes" else "✓"
        short = val if len(val)<=14 else val[:12]+"…"
        pills += f'<div class="hist-item"><span style="color:{col};font-weight:800">{icon}</span>{lbl}: <b>{short}</b></div>'
    st.markdown(f"""
    <div style="background:white;padding:.5rem 1.3rem .3rem;border-bottom:1px solid rgb(210,195,240)">
      <div style="font-size:.65rem;color:#7a6a99;font-weight:700;letter-spacing:.05em;text-transform:uppercase;margin-bottom:.3rem">Your answers</div>
      <div class="hist-strip">{pills}</div>
    </div>""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════
# MODE: STOPPED (any YES in clinical questions)
# ═══════════════════════════════════════════════════════
if mode == "screening" and any_yes():
    st.session_state.mode = "stopped"
    st.rerun()

if st.session_state.mode == "stopped":
    st.markdown('<div class="q-card">', unsafe_allow_html=True)
    st.markdown("""
    <div class="q-bubble-wrap" style="margin-bottom:.5rem">
      <div class="q-bubble"><span class="q-icon">🩺</span>
        <div class="q-text">Thank you for being honest. 💜<br><br>
          Based on your answers, please speak with your <b>GP or midwife</b>
          before starting or continuing any physical activity.</div>
      </div>
    </div>
    <div class="r-stop">
        🛑 <b>Please consult your healthcare professional</b><br><br>
        📞 Contact your <b>GP, midwife, or NHS 111</b><br>
        🌐 <a href="https://www.activepregnancyfoundation.org" target="_blank">activepregnancyfoundation.org</a>
    </div>""", unsafe_allow_html=True)
    st.markdown('<div class="rst-b" style="margin-top:.8rem">', unsafe_allow_html=True)
    if st.button("🔄 Start again"): restart()
    st.markdown('</div></div>', unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════
# MODE: CHAT (screening complete, RAG chat open)
# ═══════════════════════════════════════════════════════
elif st.session_state.mode == "chat":
    name  = st.session_state.answers.get("name","there")
    atype = st.session_state.answers.get("activity_type","")
    goal  = st.session_state.answers.get("goal","")
    weeks = st.session_state.answers.get("weeks",0)

    tips = {
        "🚶 Walking":         "Brisk walking is safe throughout all trimesters. Aim for 30 min most days.",
        "🏊 Swimming":        "Swimming reduces joint strain — excellent for all trimesters.",
        "🧘 Yoga / Pilates":  "Prenatal yoga strengthens your core and pelvic floor.",
        "🏋️ Strength training":"Light resistance training is safe — avoid lying flat after 16 weeks.",
        "🚴 Cycling":         "Stationary cycling is preferred as your bump grows for balance.",
    }
    tip = tips.get(atype,"Regular moderate-intensity activity benefits you and your baby.")
    try:
        w = int(weeks)
        t_note = (
            "In your <b>first trimester</b>, listen to your body — fatigue is common." if w<=12 else
            "The <b>second trimester</b> is often the most comfortable time to exercise." if w<=26 else
            "In your <b>third trimester</b>, focus on lower-impact activities and pelvic floor work."
        )
    except: t_note = ""

    st.markdown('<div class="q-card">', unsafe_allow_html=True)

    # Guidance card
    st.markdown(f"""
    <div class="r-safe">
        ✅ <b>Physical activity is recommended for you, {name}!</b><br><br>
        🏃‍♀️ <b>Activity:</b> {atype} &nbsp;|&nbsp; 🎯 <b>Goal:</b> {goal}<br><br>
        💡 {tip}<br>
        📅 {t_note}<br><br>
        Aim for <b>150 min moderate activity/week</b> + 2 strengthening sessions.<br>
        🌐 <a href="https://www.activepregnancyfoundation.org" target="_blank">Find APF classes →</a>
    </div>""", unsafe_allow_html=True)

    # Divider
    st.markdown("""
    <div style="text-align:center;margin:.8rem 0 .4rem;font-size:.78rem;font-weight:700;
        color:var(--p-dark);letter-spacing:.05em;text-transform:uppercase;">
        💬 Ask Nancy anything about pregnancy activity
    </div>""", unsafe_allow_html=True)

    # Chat history
    if not st.session_state.chat_msgs:
        st.session_state.chat_msgs = [("n",
            f"Hi {name}! 🌸 Now that we've completed your screening, feel free to ask me "
            f"<b>anything about staying active during pregnancy</b>.<br><br>"
            f"For example: <i>\"What are the dos and don'ts for {atype.split()[-1].lower() if atype else 'exercise'}?\"</i>"
        )]

    st.markdown('<div class="chat-area">', unsafe_allow_html=True)
    for role, text in st.session_state.chat_msgs:
        render_bubble(role, text, warn=(role=="n" and "⚠️" in text))
    st.markdown('</div>', unsafe_allow_html=True)

    # Chat input
    st.markdown('<div class="chat-inp">', unsafe_allow_html=True)

    def on_enter():
        v = st.session_state.get("rag_q","").strip()
        if v: st.session_state["pending_rag"] = v

    c1, c2 = st.columns([5,1])
    with c1:
        q_val = st.text_input("", key="rag_q", label_visibility="collapsed",
            placeholder="Ask about pregnancy activity... (press Enter ↵)",
            on_change=on_enter)
    with c2:
        st.markdown('<div class="send-b">', unsafe_allow_html=True)
        sent = st.button("Ask →", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    pending = st.session_state.pop("pending_rag", None)
    if sent and q_val.strip(): pending = q_val.strip()

    if pending:
        st.session_state.chat_msgs.append(("u", pending))
        if not api_health():
            st.session_state.chat_msgs.append(("n",
                "⚠️ Backend is offline. Please start it:<br>"
                "<code>uvicorn backend.main:app --reload --port 8000</code>"))
        else:
            with st.spinner("Nancy is thinking... 💭"):
                result = api_chat(pending)
            if "error" in result:
                st.session_state.chat_msgs.append(("n", f"⚠️ {result['error']}"))
            else:
                answer = result["answer"].replace("\n","<br>")
                if result.get("safety_flag"):
                    st.session_state.chat_msgs.append(("n", f"⚠️ {answer}"))
                else:
                    srcs = result.get("sources",[])
                    src_html = ""
                    if srcs:
                        lines = "".join([
                            f"<b>{s['activity'].title()}</b> — {s['section']} (p{s['page']})<br>"
                            for s in srcs[:3]
                        ])
                        src_html = f'<div class="src-box">📚 {lines}⏱ {result.get("time_seconds","?")}s</div>'
                    st.session_state.chat_msgs.append(("n", answer + src_html))
        st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)  # chat-inp

    # Download + restart
    col1, col2 = st.columns(2)
    with col1:
        st.download_button("⬇️ Download answers",
            data=json.dumps(st.session_state.answers, indent=2, default=str),
            file_name=f"Nancy_{date.today()}.json", mime="application/json")
    with col2:
        st.markdown('<div class="rst-b">', unsafe_allow_html=True)
        if st.button("🔄 Start again", key="r2"): restart()
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)  # q-card

# ═══════════════════════════════════════════════════════
# MODE: SCREENING (question flow)
# ═══════════════════════════════════════════════════════
elif st.session_state.mode == "screening":
    q = curq()

    # Screening complete → switch to chat mode
    if st.session_state.step >= TOTAL:
        st.session_state.mode = "chat"
        st.rerun()

    st.markdown('<div class="q-card">', unsafe_allow_html=True)

    bot_text = fmt(q["bot"])
    section  = q.get("section","")
    icon     = q.get("icon","🌸")

    st.markdown(f"""
    <div class="q-bubble-wrap" style="margin-bottom:.8rem;padding-top:14px;">
      <span class="stag">{section}</span>
      <div class="q-bubble">
        <span class="q-icon">{icon}</span>
        <div class="q-text">{bot_text}</div>
      </div>
    </div>""", unsafe_allow_html=True)

    qtype = q["type"]

    # YES / NO
    if qtype == "yesno":
        c1, c2 = st.columns(2)
        with c1:
            st.markdown('<div class="yes-b">', unsafe_allow_html=True)
            if st.button("✅  Yes", key=f"y_{q['id']}", use_container_width=True):
                record(q["id"], SHORT.get(q["id"],q["id"]), "Yes", "Yes")
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        with c2:
            st.markdown('<div class="no-b">', unsafe_allow_html=True)
            if st.button("❌  No", key=f"n_{q['id']}", use_container_width=True):
                record(q["id"], SHORT.get(q["id"],q["id"]), "No", "No")
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

    # CHOICE
    elif qtype == "choice":
        choices = q["choices"]
        cols = st.columns(min(len(choices), 3))
        for i, ch in enumerate(choices):
            with cols[i % len(cols)]:
                st.markdown('<div class="ch-b">', unsafe_allow_html=True)
                if st.button(ch, key=f"ch_{q['id']}_{i}", use_container_width=True):
                    record(q["id"], SHORT.get(q["id"],q["id"]), ch, ch)
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

    # TEXT
    elif qtype == "text":
        ik = f"t_{q['id']}"
        ek = f"entered_{q['id']}"
        def on_enter_txt():
            v = st.session_state.get(ik,"").strip()
            if v: st.session_state[ek] = v
        val = st.text_input("", key=ik, placeholder="Type here… (press Enter ↵)",
                            label_visibility="collapsed", on_change=on_enter_txt)
        if st.session_state.get(ek):
            v = st.session_state.pop(ek)
            record(q["id"], SHORT.get(q["id"],q["id"]), v, v)
            st.rerun()
        st.markdown('<div class="cont-b" style="margin-top:.4rem">', unsafe_allow_html=True)
        if st.button("Continue →", key=f"nx_{q['id']}"):
            if val.strip():
                record(q["id"], SHORT.get(q["id"],q["id"]), val.strip(), val.strip())
                st.rerun()
            else: st.warning("Please enter your name.")
        st.markdown('</div>', unsafe_allow_html=True)

    # NUMBER
    elif qtype == "number":
        val = st.number_input("", min_value=q.get("min",0), max_value=q.get("max",999),
                              value=None, placeholder="Enter number…",
                              key=f"num_{q['id']}", label_visibility="collapsed")
        st.markdown('<div class="cont-b" style="margin-top:.4rem">', unsafe_allow_html=True)
        if st.button("Continue →", key=f"nx_{q['id']}"):
            if val is not None:
                record(q["id"], SHORT.get(q["id"],q["id"]), str(int(val)), int(val))
                st.rerun()
            else: st.warning("Please enter a value.")
        st.markdown('</div>', unsafe_allow_html=True)

    # ACTIVITY GRID
    elif qtype == "activity_grid":
        stage = st.session_state.act_stage
        titles = ["Six months <b>before</b> pregnancy", "<b>During</b> this pregnancy"]
        key    = ["ab","ad"][stage]
        st.markdown(f'<div class="agrid"><div class="agrid-title">📅 {titles[stage].replace("<b>","").replace("</b>","")}</div>', unsafe_allow_html=True)
        col_f, col_i, col_d = st.columns(3)
        with col_f:
            st.markdown('<div class="gcol"><span class="gcol-lbl">Frequency / week</span>', unsafe_allow_html=True)
            f0 = st.checkbox("0 times",   key=f"{key}_f0")
            f1 = st.checkbox("1–2 times", key=f"{key}_f1")
            f2 = st.checkbox("3–4 times", key=f"{key}_f2")
            f3 = st.checkbox("5–7 times", key=f"{key}_f3")
            st.markdown('</div>', unsafe_allow_html=True)
        with col_i:
            st.markdown('<div class="gcol"><span class="gcol-lbl">Intensity</span>', unsafe_allow_html=True)
            il = st.checkbox("🟢 Light",    key=f"{key}_il")
            im = st.checkbox("🟡 Moderate", key=f"{key}_im")
            iv = st.checkbox("🔴 Vigorous", key=f"{key}_iv")
            st.markdown('</div>', unsafe_allow_html=True)
        with col_d:
            st.markdown('<div class="gcol"><span class="gcol-lbl">Duration (min)</span>', unsafe_allow_html=True)
            d1 = st.checkbox("< 20",  key=f"{key}_d1")
            d2 = st.checkbox("20–30", key=f"{key}_d2")
            d3 = st.checkbox("31–60", key=f"{key}_d3")
            d4 = st.checkbox("> 60",  key=f"{key}_d4")
            st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        freq_sel = [v for v,c in [("0",f0),("1–2",f1),("3–4",f2),("5–7",f3)] if c]
        int_sel  = [v for v,c in [("Light",il),("Moderate",im),("Vigorous",iv)] if c]
        dur_sel  = [v for v,c in [("<20",d1),("20–30",d2),("31–60",d3),(">60",d4)] if c]

        btn_lbl = "Next: During Pregnancy →" if stage==0 else "Continue →"
        st.markdown('<div class="cont-b" style="margin-top:.4rem">', unsafe_allow_html=True)
        if st.button(btn_lbl, key=f"ag_{stage}"):
            if not (freq_sel or int_sel or dur_sel):
                st.warning("Please select at least one option.")
            else:
                summary = f"Freq:{','.join(freq_sel) or '—'} | Int:{','.join(int_sel) or '—'} | Dur:{','.join(dur_sel) or '—'}min"
                if stage==0:
                    st.session_state.answers["activity_before"] = summary
                    st.session_state.prev_answers.append(("Before pregnancy", "✓"))
                    st.session_state.act_stage = 1
                    st.rerun()
                else:
                    st.session_state.answers["activity_during"] = summary
                    record(q["id"], "Activity levels", "✓ Done", "done")
                    st.session_state.act_stage = 0
                    st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)  # q-card

# Footer
st.markdown("""
<p style="text-align:center;font-size:.67rem;color:#b09fd0;margin:.5rem 0 0;">
Nancy is an informational tool · Not a substitute for medical advice<br>
© Active Pregnancy Foundation · GAQ-P © CSEP
</p>""", unsafe_allow_html=True)
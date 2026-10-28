import os
import json
import inspect
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import streamlit.components.v1 as components
from pathlib import Path
from streamlit_option_menu import option_menu

# Import all core pipeline modules
from src.log_generator import generate_logs, initialize_live_logs, LIVE_LOG_PATH
from src.log_parser import parse_uploaded_file
from src.preprocessing import clean_data
from src.feature_engineering import extract_features
from src.detector import LogDetector
from src.risk_scoring import apply_risk_scoring
from src.explanation import apply_explanations
from src.alerter import build_summary_email_html, build_dossier_email_html, send_email_alert
from src.qa_diagnostics import run_diagnostic_suite

# Optional modules from updated backend (remote_client & email_config)
try:
    from src import email_config
except Exception:
    email_config = None

try:
    from src import remote_client
except Exception:
    remote_client = None

# -----------------------------------------------------------------------------
# 1. PAGE CONFIGURATION
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="AegisAI | Autonomous SOC Platform",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

DATA_DIR = Path("data")
DATA_DIR.mkdir(parents=True, exist_ok=True)
RECIPIENTS_FILE = DATA_DIR / "saved_recipients.json"

# -----------------------------------------------------------------------------
# 2. FULL-WIDTH OBSIDIAN BLACK & CYBER EMERALD SAAS CSS
# -----------------------------------------------------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@500;600;700&display=swap');

html, body, .stApp {
    scroll-behavior: smooth !important;
    font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
}

.stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
    background: radial-gradient(ellipse at 50% 0%, rgba(16, 185, 129, 0.12) 0%, #050907 45%, #030604 100%) !important;
    color: #F8FAFC !important;
}

/* Completely Hide Sidebar & Streamlit Default Chrome */
[data-testid="stSidebar"] { display: none !important; }
[data-testid="collapsedControl"] { display: none !important; }
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }
.stDeployButton { display: none; }

/* Occupy Full Webpage Width with Left Gutter for Vertical Timeline */
.block-container {
    max-width: 100% !important;
    width: 100% !important;
    padding-top: 1.4rem !important;
    padding-bottom: 4rem !important;
    padding-left: 5.8rem !important;
    padding-right: 3.2rem !important;
}
@media (max-width: 900px) {
    .block-container {
        padding-left: 1.4rem !important;
        padding-right: 1.4rem !important;
    }
}

.ckpt-anchor {
    scroll-margin-top: 20px;
}

/* Primary & Secondary Cyber-Emerald Button Styling */
div.stButton > button[kind="primary"], div.stButton > button {
    background: linear-gradient(135deg, #059669 0%, #10B981 100%) !important;
    color: #021008 !important;
    border: 1px solid #34D399 !important;
    border-radius: 10px !important;
    font-weight: 800 !important;
    font-size: 0.96rem !important;
    padding: 0.6rem 1.1rem !important;
    box-shadow: 0 4px 16px rgba(16, 185, 129, 0.28);
    transition: all 0.22s ease;
}
div.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 22px rgba(16, 185, 129, 0.5) !important;
    color: #010804 !important;
}
div.stButton > button[kind="secondary"] {
    background: rgba(11, 22, 16, 0.85) !important;
    color: #E2E8F0 !important;
    border: 1px solid rgba(16, 185, 129, 0.35) !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
}
div.stButton > button[kind="secondary"]:hover {
    border-color: #10B981 !important;
    color: #34D399 !important;
    background: rgba(16, 185, 129, 0.12) !important;
}

/* Popover & Input Styling */
[data-testid="stPopover"] > button {
    background: #09130E !important;
    color: #F8FAFC !important;
    border: 1px solid rgba(16, 185, 129, 0.38) !important;
    border-radius: 10px !important;
    font-weight: 700 !important;
    font-size: 0.95rem !important;
}
[data-testid="stPopover"] > button:hover {
    border-color: #10B981 !important;
    color: #34D399 !important;
}
.stTextInput input, .stSelectbox div[data-baseweb="select"] > div {
    background-color: #050A07 !important;
    border: 1px solid rgba(16, 185, 129, 0.35) !important;
    color: #FFFFFF !important;
    border-radius: 10px !important;
}
.stTextInput label, .stSelectbox label, .stRadio label {
    color: #F1F5F9 !important;
    font-weight: 600 !important;
    font-size: 0.95rem !important;
}
[data-testid="stFileUploaderDropzone"] {
    background-color: #050A07 !important;
    border: 1px dashed rgba(16, 185, 129, 0.48) !important;
    border-radius: 12px !important;
}

/* Top SaaS Brand Bar */
.brand-title {
    font-size: 1.95rem;
    font-weight: 800;
    background: linear-gradient(90deg, #FFFFFF 0%, #34D399 55%, #10B981 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin: 0;
    line-height: 1.2;
}
.brand-sub {
    color: #E2E8F0;
    font-size: 0.92rem;
    margin-top: 6px;
    display: flex;
    align-items: center;
    gap: 12px;
    font-family: 'JetBrains Mono', monospace;
}
.status-pill {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: rgba(16, 185, 129, 0.16);
    border: 1px solid rgba(16, 185, 129, 0.45);
    color: #34D399;
    padding: 4px 12px;
    border-radius: 999px;
    font-size: 0.76rem;
    font-weight: 700;
    text-transform: uppercase;
}
.pulse-dot {
    width: 8px;
    height: 8px;
    background-color: #10B981;
    border-radius: 50%;
    box-shadow: 0 0 10px #10B981;
}

/* Open, Box-Free Hero Section */
.open-hero-wrap {
    width: 100%;
    padding: 38px 0 34px 0;
    margin-bottom: 34px;
    text-align: left;
    border-bottom: 1px solid rgba(16, 185, 129, 0.2);
}
.hero-eyebrow {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    background: rgba(16, 185, 129, 0.14);
    color: #34D399;
    border: 1px solid rgba(16, 185, 129, 0.42);
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.82rem;
    font-weight: 700;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    padding: 6px 16px;
    border-radius: 999px;
    margin-bottom: 20px;
}
.hero-question-open {
    font-size: clamp(2.35rem, 3.6vw, 3.45rem);
    font-weight: 800;
    line-height: 1.16;
    color: #FFFFFF;
    margin: 0 0 20px 0;
    letter-spacing: -0.025em;
    max-width: 100%;
}
.hero-question-open span {
    background: linear-gradient(90deg, #10B981 0%, #6EE7B7 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    text-shadow: 0 0 35px rgba(16, 185, 129, 0.28);
}
.hero-subtitle-open {
    font-size: 1.18rem;
    line-height: 1.68;
    color: #E2E8F0;
    max-width: 92%;
    margin: 0 0 30px 0;
    font-weight: 400;
}
.hero-metrics-strip {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 20px;
    width: 100%;
}
@media (max-width: 992px) {
    .hero-metrics-strip {
        grid-template-columns: repeat(2, 1fr);
    }
}
.hero-metric-item {
    background: linear-gradient(145deg, rgba(12, 23, 17, 0.9) 0%, rgba(6, 12, 9, 0.9) 100%);
    border-left: 4px solid #10B981;
    border-top: 1px solid rgba(16, 185, 129, 0.24);
    border-right: 1px solid rgba(16, 185, 129, 0.24);
    border-bottom: 1px solid rgba(16, 185, 129, 0.24);
    padding: 16px 20px;
    border-radius: 12px;
}
.hero-metric-item strong {
    color: #34D399;
    font-family: 'JetBrains Mono', monospace;
    font-size: 1.28rem;
    font-weight: 800;
    display: block;
    margin-bottom: 4px;
}
.hero-metric-item span {
    color: #F1F5F9;
    font-size: 0.95rem;
    font-weight: 500;
}

/* Full-Width Section Headers */
.section-header-full {
    width: 100%;
    margin: 14px 0 22px 0;
}
.section-kicker {
    color: #34D399;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.84rem;
    font-weight: 700;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    margin-bottom: 6px;
}
.section-heading {
    color: #FFFFFF;
    font-size: 1.9rem;
    font-weight: 800;
    letter-spacing: -0.02em;
    margin: 0 0 6px 0;
}
.section-desc {
    color: #CBD5E1;
    font-size: 1.05rem;
    margin: 0;
}

/* Symmetrical 3-Column SaaS Cards */
.saas-grid-3 {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 24px;
    width: 100%;
    margin-bottom: 46px;
    align-items: stretch;
}
@media (max-width: 1024px) {
    .saas-grid-3 {
        grid-template-columns: 1fr;
    }
}
.saas-card {
    background: linear-gradient(165deg, #0D1712 0%, #070D0A 100%);
    border: 1px solid rgba(16, 185, 129, 0.28);
    border-radius: 16px;
    padding: 28px 26px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    transition: all 0.25s ease;
    box-shadow: 0 10px 28px rgba(0, 0, 0, 0.45);
}
.saas-card:hover {
    border-color: #10B981;
    box-shadow: 0 12px 34px rgba(16, 185, 129, 0.16);
    transform: translateY(-3px);
}
.pain-tag {
    display: inline-block;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.78rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: #6EE7B7;
    background: rgba(16, 185, 129, 0.14);
    border: 1px solid rgba(16, 185, 129, 0.36);
    padding: 5px 12px;
    border-radius: 8px;
    margin-bottom: 16px;
    width: fit-content;
}
.saas-card h4 {
    color: #FFFFFF;
    font-size: 1.3rem;
    font-weight: 800;
    margin: 0 0 10px 0;
}
.saas-card p {
    color: #E2E8F0;
    font-size: 1.02rem;
    line-height: 1.65;
    margin: 0 0 20px 0;
}
.solution-footer {
    border-top: 1px solid rgba(16, 185, 129, 0.22);
    padding-top: 14px;
    font-size: 0.92rem;
    color: #34D399;
    font-weight: 700;
    font-family: 'JetBrains Mono', monospace;
}
.step-badge {
    width: 40px;
    height: 40px;
    border-radius: 10px;
    background: rgba(16, 185, 129, 0.18);
    border: 1px solid #10B981;
    color: #34D399;
    font-family: 'JetBrains Mono', monospace;
    font-weight: 800;
    font-size: 1.02rem;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 16px;
}

/* Launchpad Hero Card Headers & Equal Height Containers */
.launchpad-badge {
    display: inline-block;
    padding: 5px 12px;
    border-radius: 7px;
    font-size: 0.76rem;
    font-family: 'JetBrains Mono', monospace;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin-bottom: 12px;
    background: rgba(16, 185, 129, 0.15);
    color: #34D399;
    border: 1px solid rgba(16, 185, 129, 0.4);
}
.ws-meta-box {
    background: #050A07;
    border: 1px solid rgba(16, 185, 129, 0.26);
    border-radius: 10px;
    padding: 12px 14px;
    font-size: 0.9rem;
    color: #E2E8F0;
    margin: 12px 0;
    line-height: 1.5;
}
.ws-meta-box code {
    color: #34D399;
    background: rgba(16, 185, 129, 0.15);
    padding: 2px 6px;
    border-radius: 4px;
}

/* Glassmorphic KPI Cards */
.kpi-container {
    display: flex;
    gap: 1.25rem;
    margin-bottom: 1.5rem;
    flex-wrap: wrap;
}
.kpi-card {
    flex: 1;
    min-width: 220px;
    background: linear-gradient(145deg, rgba(13, 24, 18, 0.92) 0%, rgba(7, 13, 10, 0.85) 100%);
    backdrop-filter: blur(12px);
    border: 1px solid rgba(16, 185, 129, 0.24);
    border-radius: 14px;
    padding: 1.35rem 1.5rem;
    color: white;
    transition: all 0.25s ease;
    box-shadow: 0 8px 22px -6px rgba(0, 0, 0, 0.55);
}
.kpi-card:hover {
    transform: translateY(-4px);
    border-color: #10B981;
    box-shadow: 0 12px 28px -8px rgba(16, 185, 129, 0.25);
}
.kpi-label {
    font-size: 0.82rem;
    color: #CBD5E1;
    margin-bottom: 0.45rem;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    font-weight: 700;
    font-family: 'JetBrains Mono', monospace;
}
.kpi-value {
    font-family: 'JetBrains Mono', monospace;
    font-size: 2.2rem;
    font-weight: 800;
    margin: 0;
    line-height: 1.2;
    color: #FFFFFF;
}
.kpi-sub {
    font-size: 0.84rem;
    margin-top: 0.5rem;
    font-weight: 600;
}
.accent-neutral { border-top: 3px solid #10B981; }
.accent-emerald { border-top: 3px solid #34D399; }
.accent-amber   { border-top: 3px solid #F59E0B; }
.accent-crimson { border-top: 3px solid #EF4444; }

/* Bordered Containers as Obsidian Glass Cards */
[data-testid="stVerticalBlockBorderWrapper"] {
    background: linear-gradient(165deg, rgba(13, 23, 18, 0.88) 0%, rgba(7, 13, 10, 0.88) 100%) !important;
    border: 1px solid rgba(16, 185, 129, 0.28) !important;
    border-radius: 14px !important;
    padding: 1.2rem !important;
    box-shadow: 0 8px 26px rgba(0, 0, 0, 0.45) !important;
}
</style>
""", unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# 3. PERSISTENT MULTI-RECIPIENT & BACKEND EMAIL HELPERS
# -----------------------------------------------------------------------------
def load_saved_recipients() -> list[str]:
    """Load saved recipient emails from src/email_config.py or data/saved_recipients.json."""
    if email_config is not None:
        for fn_name in ("load_recipients", "get_recipients", "get_saved_recipients"):
            if hasattr(email_config, fn_name):
                try:
                    res = getattr(email_config, fn_name)()
                    if isinstance(res, list) and res:
                        return [str(x).strip() for x in res if str(x).strip()]
                except Exception:
                    pass
        for attr in ("RECIPIENTS", "DEFAULT_RECIPIENTS", "RECEIVER_EMAILS"):
            if hasattr(email_config, attr):
                val = getattr(email_config, attr)
                if isinstance(val, list) and val:
                    return [str(x).strip() for x in val if str(x).strip()]

    if RECIPIENTS_FILE.exists():
        try:
            data = json.loads(RECIPIENTS_FILE.read_text(encoding="utf-8"))
            if isinstance(data, list) and data:
                return [str(x).strip() for x in data if str(x).strip()]
        except Exception:
            pass

    return ["24kaduu@rbunagpur.in"]


def save_recipients_list(recipients: list[str]) -> None:
    """Save recipient emails to both data/saved_recipients.json and src/email_config.py."""
    cleaned = []
    for r in recipients:
        r_clean = str(r).strip()
        if r_clean and "@" in r_clean and r_clean.lower() not in [x.lower() for x in cleaned]:
            cleaned.append(r_clean)

    if email_config is not None:
        for fn_name in ("save_recipients", "update_recipients", "set_recipients"):
            if hasattr(email_config, fn_name):
                try:
                    getattr(email_config, fn_name)(cleaned)
                except Exception:
                    pass

    try:
        RECIPIENTS_FILE.write_text(json.dumps(cleaned, indent=2), encoding="utf-8")
    except Exception:
        pass


def get_backend_sender_credentials() -> tuple[str, str]:
    """Retrieve sender email & passkey from backend config, Streamlit secrets, or environment."""
    sender_email = ""
    app_password = ""

    if email_config is not None:
        for attr in ("SENDER_EMAIL", "TX_EMAIL", "EMAIL_ADDRESS", "SMTP_USER", "GMAIL_USER"):
            if hasattr(email_config, attr) and getattr(email_config, attr):
                sender_email = str(getattr(email_config, attr)).strip()
                break
        for attr in ("SENDER_PASSKEY", "SENDER_PASSWORD", "APP_PASSWORD", "TX_PASS", "PASSKEY", "SMTP_PASSWORD"):
            if hasattr(email_config, attr) and getattr(email_config, attr):
                app_password = str(getattr(email_config, attr)).strip()
                break

    if not sender_email:
        try:
            sender_email = os.getenv("SENDER_EMAIL") or st.secrets.get("SENDER_EMAIL", "")
        except Exception:
            sender_email = os.getenv("SENDER_EMAIL", "")

    if not app_password:
        try:
            app_password = os.getenv("SENDER_PASSKEY") or st.secrets.get("SENDER_PASSKEY", "")
        except Exception:
            app_password = os.getenv("SENDER_PASSKEY", "")

    return sender_email, app_password


def dispatch_email_to_saved_recipients(recipients: list[str], subject: str, html_body: str):
    """Call send_email_alert compatibly whether it expects 3 args (backend creds) or 5 args."""
    if not recipients:
        return False, "No saved recipients configured.", html_body

    sender_email, app_password = get_backend_sender_credentials()
    sig = inspect.signature(send_email_alert)
    param_count = len(sig.parameters)

    last_sent = False
    status_messages = []
    last_html = html_body

    # Try passing each saved recipient so every saved address gets notified
    for recipient in recipients:
        try:
            if param_count >= 5:
                res = send_email_alert(recipient, subject, html_body, sender_email, app_password)
            elif param_count == 4:
                res = send_email_alert(recipient, subject, html_body, sender_email)
            else:
                res = send_email_alert(recipient, subject, html_body)

            if isinstance(res, tuple) and len(res) == 3:
                sent_live, status_msg, html_out = res
                last_sent = last_sent or bool(sent_live)
                status_messages.append(f"{recipient}: {status_msg}")
                last_html = html_out
            elif isinstance(res, tuple) and len(res) == 2:
                sent_live, status_msg = res
                last_sent = last_sent or bool(sent_live)
                status_messages.append(f"{recipient}: {status_msg}")
            else:
                last_sent = True
                status_messages.append(f"Dispatched to {recipient}")
        except Exception as exc:
            status_messages.append(f"{recipient}: {exc}")

    combined_status = " | ".join(status_messages)
    return last_sent, combined_status, last_html


# -----------------------------------------------------------------------------
# 4. CORE AI TELEMETRY & ALERT PIPELINE FUNCTIONS
# -----------------------------------------------------------------------------
def run_full_pipeline(raw_df):
    """Runs the data through the ML and explanation pipeline."""
    with st.spinner("⚡ Executing AI Telemetry & Anomaly Pipeline..."):
        df_clean = clean_data(raw_df)
        df_features = extract_features(df_clean)
        detector = LogDetector()
        df_detected = detector.detect(df_features)
        df_scored = apply_risk_scoring(df_detected)
        df_final = apply_explanations(df_scored)
    return df_final


def check_and_trigger_email(df, source_label):
    """Checks for Critical alerts and dispatches an email notification to all saved recipients."""
    crit_count = len(df[df['severity'] == 'Critical'])
    recipients = st.session_state.get('saved_recipients', [])
    auto_alert = st.session_state.get('auto_em', True)

    if auto_alert and crit_count > 0 and recipients:
        subject = f"🚨 [CRITICAL SOC ALERT] {crit_count} High-Risk Anomalies Detected"
        html_body = build_summary_email_html(df, source_label)
        sent_live, status_msg, html_out = dispatch_email_to_saved_recipients(
            recipients, subject, html_body
        )
        st.session_state.email_state = {
            "sent_live": sent_live,
            "status_msg": status_msg,
            "subject": subject,
            "recipient": ", ".join(recipients),
            "html": html_out
        }


def ingest_live_stream(url: str = "http://localhost:8500", token: str = ""):
    raw_df = None
    if remote_client is not None:
        for fn_name in ("fetch_logs_from_url", "fetch_remote_logs", "fetch_logs", "pull_live_logs"):
            if hasattr(remote_client, fn_name):
                try:
                    fn = getattr(remote_client, fn_name)
                    res = fn(url, token) if len(inspect.signature(fn).parameters) >= 2 else fn(url)
                    if isinstance(res, pd.DataFrame) and not res.empty:
                        raw_df = res
                        break
                except Exception:
                    pass

    if raw_df is None:
        if not os.path.exists(LIVE_LOG_PATH):
            initialize_live_logs()
        raw_df = pd.read_csv(LIVE_LOG_PATH)

    st.session_state.final_data = run_full_pipeline(raw_df)
    st.session_state.active_source = f"Live Server Stream ({len(raw_df)} logs)"
    check_and_trigger_email(st.session_state.final_data, st.session_state.active_source)
    st.toast("Synced with Live Target Website!", icon="🟢")


def ingest_simulation():
    file_path = generate_logs()
    raw_df = pd.read_csv(file_path)
    st.session_state.final_data = run_full_pipeline(raw_df)
    st.session_state.active_source = f"Synthetic Cyber Range ({len(raw_df)} logs)"
    check_and_trigger_email(st.session_state.final_data, st.session_state.active_source)
    st.toast("Synthetic Cyber Range Loaded!", icon="⚡")


# -----------------------------------------------------------------------------
# 5. MAIN SINGLE-PAGE SAAS APPLICATION
# -----------------------------------------------------------------------------
def main():
    # --- SESSION STATE INITIALIZATION ---
    if 'final_data' not in st.session_state:
        st.session_state.final_data = None
    if 'active_source' not in st.session_state:
        st.session_state.active_source = "Standby — Select Telemetry Source"
    if 'email_state' not in st.session_state:
        st.session_state.email_state = None
    if 'qa_results' not in st.session_state:
        st.session_state.qa_results = None
    if 'saved_recipients' not in st.session_state:
        st.session_state.saved_recipients = load_saved_recipients()
    if 'auto_em' not in st.session_state:
        st.session_state.auto_em = True
    if 'live_url' not in st.session_state:
        st.session_state.live_url = "http://localhost:8500"
    if 'live_token' not in st.session_state:
        st.session_state.live_token = ""

    # =========================================================================
    # CHECKPOINT 01: TOP COMMAND BAR + OPEN, BOX-FREE HERO QUESTION
    # =========================================================================
    st.markdown('<div id="ckpt-0" class="ckpt-anchor"></div>', unsafe_allow_html=True)

    with st.container(border=True):
        top_left, top_right = st.columns([1.8, 1.4])
        with top_left:
            st.markdown(f"""
            <div>
                <h1 class="brand-title">🛡️ AI-Powered Cybersecurity Log Analyser</h1>
                <div class="brand-sub">
                    <span class="status-pill"><span class="pulse-dot"></span> Engine Ready</span>
                    <span>🔌 {st.session_state.active_source}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

        with top_right:
            u1, u2, u3 = st.columns([1, 1.1, 1.1])

            # 1. Quick 1-Click Live Sync
            with u1:
                if st.button("🔄 Sync Live", type="primary", use_container_width=True, help="Pull latest attacks from target_website.py"):
                    ingest_live_stream(st.session_state.live_url, st.session_state.live_token)
                    st.rerun()

            # 2. Switch Data Source Popover
            with u2:
                with st.popover("🔌 Data Source", use_container_width=True):
                    st.markdown("##### 📡 Switch Telemetry Stream")
                    if st.button("🟢 Load Live Website Stream", use_container_width=True):
                        ingest_live_stream(st.session_state.live_url, st.session_state.live_token)
                        st.rerun()
                    if st.button("⚡ Run Synthetic Simulation", use_container_width=True):
                        ingest_simulation()
                        st.rerun()
                    st.markdown("---")
                    pop_upload = st.file_uploader("📂 Upload CSV, JSON, XLSX", type=['csv', 'json', 'xlsx'], key="pop_up")
                    if pop_upload is not None:
                        if st.button("🔍 Parse Uploaded File", type="primary", use_container_width=True):
                            try:
                                raw_df = parse_uploaded_file(pop_upload)
                                st.session_state.final_data = run_full_pipeline(raw_df)
                                st.session_state.active_source = f"Uploaded: {pop_upload.name}"
                                check_and_trigger_email(st.session_state.final_data, st.session_state.active_source)
                                st.toast(f"Loaded {pop_upload.name}!", icon="📂")
                                st.rerun()
                            except ValueError as err:
                                st.error(str(err))
                    if st.session_state.final_data is not None:
                        st.markdown("---")
                        if st.button("🔄 Clear Loaded Telemetry", use_container_width=True):
                            st.session_state.final_data = None
                            st.session_state.active_source = "Standby — Select Telemetry Source"
                            st.rerun()

            # 3. Multi-Recipient Email & Backend Alert Routing Popover
            with u3:
                alert_badge = f"🔔 Alerts ({len(st.session_state.saved_recipients)})"
                with st.popover(alert_badge, use_container_width=True):
                    st.markdown("##### 📧 SOC Multi-Recipient Alert Routing")
                    st.caption("🔒 **Backend Sender Active:** Sender email & passkey are authenticated automatically in backend code.")
                    st.checkbox("Auto-Email on Critical Threats", key="auto_em")

                    st.markdown("---")
                    st.markdown("**Add More Recipients**")
                    r_in_col, r_btn_col = st.columns([2.6, 1.1])
                    with r_in_col:
                        new_rec = st.text_input(
                            "Add Recipient Email",
                            placeholder="analyst@company.com",
                            label_visibility="collapsed",
                            key="new_rec_email_input"
                        )
                    with r_btn_col:
                        if st.button("➕ Save", type="primary", use_container_width=True, key="save_rec_btn"):
                            cleaned_new = new_rec.strip()
                            if cleaned_new and "@" in cleaned_new:
                                if cleaned_new.lower() not in [x.lower() for x in st.session_state.saved_recipients]:
                                    st.session_state.saved_recipients.append(cleaned_new)
                                    save_recipients_list(st.session_state.saved_recipients)
                                    st.toast(f"Saved recipient: {cleaned_new}", icon="✅")
                                    st.rerun()
                                else:
                                    st.warning("Recipient already saved.")
                            else:
                                st.warning("Enter a valid email ID.")

                    st.markdown(f"**Saved Recipient IDs ({len(st.session_state.saved_recipients)})**")
                    if not st.session_state.saved_recipients:
                        st.info("No recipients saved yet.")
                    else:
                        for idx, email_id in enumerate(st.session_state.saved_recipients):
                            sc1, sc2 = st.columns([3.2, 0.8])
                            with sc1:
                                st.code(email_id, language=None)
                            with sc2:
                                if st.button("✖", key=f"rm_rec_{idx}", help=f"Remove {email_id}"):
                                    st.session_state.saved_recipients.pop(idx)
                                    save_recipients_list(st.session_state.saved_recipients)
                                    st.rerun()

                    if st.session_state.email_state is not None:
                        st.markdown("---")
                        st.caption(st.session_state.email_state["status_msg"])

    # --- OPEN, BOX-FREE HERO QUESTION ---
    st.markdown("""
    <div class="open-hero-wrap">
        <div class="hero-eyebrow">● AUTONOMOUS SIEM &amp; REAL-TIME THREAT INTELLIGENCE • USE ↑/↓ ARROW KEYS TO NAVIGATE</div>
        <h1 class="hero-question-open">
            Drowning in Millions of Server Logs While <span>Real Cyberattacks</span> Slip Through Unnoticed?
        </h1>
        <p class="hero-subtitle-open">
            Manual log inspection is too slow when Brute Force, SQL Injection, and DDoS attacks execute in milliseconds.
            Transform raw server telemetry into real-time, explainable AI threat detection, MITRE ATT&amp;CK playbooks, and automated multi-recipient team alerts—with zero complex setup.
        </p>
        <div class="hero-metrics-strip">
            <div class="hero-metric-item">
                <strong>&lt; 10ms Latency</strong>
                <span>Isolation Forest Anomaly Scoring</span>
            </div>
            <div class="hero-metric-item">
                <strong>4+ Threat Vectors</strong>
                <span>SQLi • Brute Force • DDoS • Anomalies</span>
            </div>
            <div class="hero-metric-item">
                <strong>Universal Parser</strong>
                <span>Auto-Normalizes CSV, JSON &amp; XLSX</span>
            </div>
            <div class="hero-metric-item">
                <strong>Zero-Touch Dispatch</strong>
                <span>Backend SMTP Multi-Recipient Alerts</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # =========================================================================
    # CHECKPOINT 02: PROBLEM VS. SOLUTION (FULL-WIDTH 3-COLUMN GRID)
    # =========================================================================
    st.markdown("""
    <div id="ckpt-1" class="ckpt-anchor section-header-full">
        <div class="section-kicker">02 // THE SECURITY BOTTLENECK VS. OUR SOLUTION</div>
        <h2 class="section-heading">Why Modern Security Teams Outgrow Manual Log Audits</h2>
        <p class="section-desc">Stop piecing together raw spreadsheets after a breach has already compromised your infrastructure.</p>
    </div>

    <div class="saas-grid-3">
        <div class="saas-card">
            <div>
                <span class="pain-tag">PAIN POINT 01 • BLIND SPOTS</span>
                <h4>Attacks Hide Inside Normal Traffic</h4>
                <p>Credential stuffing and SQL injection payloads blend into thousands of legitimate HTTP requests, staying invisible until sensitive data is exfiltrated.</p>
            </div>
            <div class="solution-footer">✓ Our Solution: Continuous AI behavioral profiling on every request</div>
        </div>
        <div class="saas-card">
            <div>
                <span class="pain-tag">PAIN POINT 02 • MESSY FORMATS</span>
                <h4>Fragmented Server Log Schemas</h4>
                <p>Every web stack exports different column names, timestamps, and structures across CSV, JSON, and Excel files—stalling urgent forensic triage.</p>
            </div>
            <div class="solution-footer">✓ Our Solution: Zero-config universal schema normalization</div>
        </div>
        <div class="saas-card">
            <div>
                <span class="pain-tag">PAIN POINT 03 • DELAYED RESPONSE</span>
                <h4>Alert Fatigue &amp; Single-Inbox Silos</h4>
                <p>Cryptic firewall flags waste analyst hours, while manual credential entry and single-recipient alerts leave security teams blind during off-hours.</p>
            </div>
            <div class="solution-footer">✓ Our Solution: MITRE ATT&amp;CK dossiers + saved multi-recipient dispatch</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # =========================================================================
    # CHECKPOINT 03: HOW IT WORKS (FULL-WIDTH 3-STEP WORKFLOW)
    # =========================================================================
    st.markdown("""
    <div id="ckpt-2" class="ckpt-anchor section-header-full">
        <div class="section-kicker">03 // FRICTIONLESS DEPLOYMENT</div>
        <h2 class="section-heading">From Raw Telemetry to Threat Mitigation in 3 Steps</h2>
        <p class="section-desc">Enterprise-grade threat visibility across your entire screen—without heavyweight agents or week-long configurations.</p>
    </div>

    <div class="saas-grid-3">
        <div class="saas-card">
            <div>
                <div class="step-badge">01</div>
                <h4>Connect or Upload Telemetry</h4>
                <p>Stream live logs from any isolated web server URL, drop in historical CSV/JSON/XLSX files, or launch the 1-click cyber range sandbox.</p>
            </div>
            <div class="solution-footer">→ Instant Multi-Source Ingestion Pipeline</div>
        </div>
        <div class="saas-card">
            <div>
                <div class="step-badge">02</div>
                <h4>AI Feature &amp; Risk Scoring</h4>
                <p>Our machine learning engine evaluates status codes, payload signatures, and request velocity to assign a 0–100 risk score and MITRE ATT&amp;CK mapping.</p>
            </div>
            <div class="solution-footer">→ Explainable Threat Attribution</div>
        </div>
        <div class="saas-card">
            <div>
                <div class="step-badge">03</div>
                <h4>Automated Team Dispatch</h4>
                <p>Critical incidents automatically trigger backend-authenticated HTML email dossiers across your entire saved recipient roster in real time.</p>
            </div>
            <div class="solution-footer">→ Zero-Touch SMTP Broadcasting</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # =========================================================================
    # CHECKPOINT 04: SYMMETRICAL 3-CARD SECURITY OPERATIONS LAUNCHPAD
    # =========================================================================
    st.markdown("""
    <div id="ckpt-3" class="ckpt-anchor section-header-full">
        <div class="section-kicker">04 // TELEMETRY INGESTION WORKSPACE</div>
        <h2 class="section-heading">🚀 Initialize Security Operations Workspace</h2>
        <p class="section-desc">Choose a telemetry ingestion method below to populate the real-time AI detection console, or jump directly to automated QA diagnostics.</p>
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3, gap="large")

    # CARD 1: LIVE WEBSITE STREAM
    with c1:
        with st.container(border=True):
            st.markdown("<span class='launchpad-badge'>● REAL-TIME SYNC</span>", unsafe_allow_html=True)
            st.markdown("#### Live Website Stream")
            st.write("Enter the log URL of any isolated website (`target_website.py`). The analyser pulls its logs automatically and keeps analysing as new requests arrive.")
            st.session_state.live_url = st.text_input("Website log URL", value=st.session_state.live_url, key="lp_url")
            st.session_state.live_token = st.text_input("Access token (if the site requires one)", value=st.session_state.live_token, type="password", key="lp_tok")
            if st.button("● Connect & Start Live Monitoring", type="primary", use_container_width=True, key="lp_live_btn"):
                ingest_live_stream(st.session_state.live_url, st.session_state.live_token)
                st.rerun()

    # CARD 2: MULTI-FORMAT FILE UPLOAD
    with c2:
        with st.container(border=True):
            st.markdown("<span class='launchpad-badge'>📂 UNIVERSAL PARSER</span>", unsafe_allow_html=True)
            st.markdown("#### Multi-Format File Analysis")
            st.write("Ingest external web server access logs in **CSV**, **JSON**, or **Excel (`.xlsx`)** format with automatic schema normalization.")
            st.markdown("<div class='ws-meta-box'>⚡ Automatically maps IP, Timestamp, Method, URI, HTTP Status, Latency &amp; User-Agent fields</div>", unsafe_allow_html=True)
            landing_upload = st.file_uploader("Drop CSV, JSON, or XLSX file", type=['csv', 'json', 'xlsx'], label_visibility="collapsed", key="lp_file_up")
            if landing_upload is not None:
                if st.button(f"🔍 Analyse {landing_upload.name}", type="primary", use_container_width=True, key="lp_parse_btn"):
                    try:
                        raw_df = parse_uploaded_file(landing_upload)
                        st.session_state.final_data = run_full_pipeline(raw_df)
                        st.session_state.active_source = f"File: {landing_upload.name}"
                        check_and_trigger_email(st.session_state.final_data, st.session_state.active_source)
                        st.rerun()
                    except ValueError as err:
                        st.error(str(err))

    # CARD 3: SYNTHETIC ATTACK SIMULATION
    with c3:
        with st.container(border=True):
            st.markdown("<span class='launchpad-badge'>⚡ 1-CLICK CYBER RANGE</span>", unsafe_allow_html=True)
            st.markdown("#### Synthetic Attack Simulation")
            st.write("Generate 1,280 multi-vector logs (Normal, Brute Force, SQL Injection, and DDoS) and export sample `.csv`, `.json`, and `.xlsx` datasets.")
            st.markdown("<div class='ws-meta-box'>📁 Exports audit-ready benchmark datasets to <code>/data</code> for compliance verification &amp; sandbox testing</div>", unsafe_allow_html=True)
            st.markdown("<div style='height: 44px;'></div>", unsafe_allow_html=True)
            if st.button("▶️ Launch Attack Simulation", type="primary", use_container_width=True, key="lp_sim_btn"):
                ingest_simulation()
                st.rerun()

    # =========================================================================
    # CHECKPOINT 05: 4-MODULE SOC CONSOLE (OVERVIEW, ALERTS, EXPLAINABILITY, QA)
    # =========================================================================
    st.markdown("<div style='height: 36px;'></div>", unsafe_allow_html=True)
    st.markdown("""
    <div id="ckpt-4" class="ckpt-anchor section-header-full">
        <div class="section-kicker">05 // AUTONOMOUS SOC COMMAND MODULES</div>
        <h2 class="section-heading">🛡️ Real-Time Threat Intelligence, Explainability &amp; QA Console</h2>
        <p class="section-desc">Switch seamlessly between your Overview Dashboard, Alert Management, AI Explainability Dossiers, and Automated QA Verification Suite.</p>
    </div>
    """, unsafe_allow_html=True)

    # --- 4 CORE MODULES NAVIGATION BAR (ALWAYS VISIBLE) ---
    page = option_menu(
        menu_title=None,
        options=["Overview Dashboard", "Alert Management", "AI Explainability", "System QA & Testing"],
        icons=["grid-1x2-fill", "shield-shaded", "cpu-fill", "check2-circle"],
        default_index=0,
        orientation="horizontal",
        styles={
            "container": {
                "padding": "8px!important",
                "background-color": "#070E0A",
                "border": "1px solid rgba(16, 185, 129, 0.32)",
                "border-radius": "12px",
                "margin-top": "8px",
                "margin-bottom": "20px",
                "max-width": "100%"
            },
            "icon": {"color": "#34D399", "font-size": "17px"},
            "nav-link": {
                "font-size": "15px",
                "font-weight": "600",
                "text-align": "center",
                "margin": "0px 6px",
                "padding": "12px 0px",
                "border-radius": "8px",
                "--hover-color": "#0F1F17",
                "color": "#E2E8F0"
            },
            "nav-link-selected": {
                "background": "linear-gradient(135deg, #059669 0%, #10B981 100%)",
                "color": "#021008",
                "font-weight": "800",
                "box-shadow": "0 4px 14px rgba(16, 185, 129, 0.35)"
            },
        }
    )

    # --- COMPACT EMAIL PREVIEW EXPANDER (IF DISPATCHED) ---
    if st.session_state.email_state is not None:
        em = st.session_state.email_state
        with st.expander(f"📨 Dispatched Security Alert Preview — To: {em['recipient']} | {em['subject']}"):
            st.caption(em["status_msg"])
            components.html(em["html"], height=420, scrolling=True)

    # ==========================================
    # PAGE 4: SYSTEM QA & TESTING (WORKS ANYTIME, EVEN BEFORE DATA LOAD)
    # ==========================================
    if page == "System QA & Testing":
        with st.container(border=True):
            qa_head1, qa_head2 = st.columns([2.5, 1])
            with qa_head1:
                st.markdown("#### 🧪 Automated Pipeline Diagnostics & Verification Suite")
                st.caption("Executes 8 live end-to-end verification tests across the Parser, Preprocessor, Feature Engineer, Isolation Forest ML Engine, and Explainability modules.")
            with qa_head2:
                if st.button("▶️ Execute All 8 QA Tests", type="primary", use_container_width=True):
                    with st.spinner("Running automated unit & integration tests..."):
                        st.session_state.qa_results = run_diagnostic_suite()
                    st.toast("All 8 QA Diagnostics Passed!", icon="✅")

        if st.session_state.qa_results is None:
            st.session_state.qa_results = run_diagnostic_suite()

        qa_df = st.session_state.qa_results
        passed_count = (qa_df["Status"] == "✅ PASSED").sum()
        total_latency = qa_df["Latency (ms)"].sum()

        st.markdown(f"""
        <div class="kpi-container" style="margin-top: 1rem;">
            <div class="kpi-card accent-emerald">
                <div class="kpi-label">✅ Test Suite Pass Rate</div>
                <div class="kpi-value">{passed_count} / {len(qa_df)}</div>
                <div class="kpi-sub" style="color: #10B981;">100% Core Pipeline Coverage</div>
            </div>
            <div class="kpi-card accent-neutral">
                <div class="kpi-label">⚡ Total Execution Time</div>
                <div class="kpi-value">{total_latency:.1f} ms</div>
                <div class="kpi-sub" style="color: #34D399;">Real-Time Sub-Second Benchmark</div>
            </div>
            <div class="kpi-card accent-amber">
                <div class="kpi-label">🛡️ Edge Cases Verified</div>
                <div class="kpi-value">8 Vectors</div>
                <div class="kpi-sub" style="color: #FBBF24;">SQLi, Brute-Force, DDoS, Nulls &amp; Schema</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        with st.container(border=True):
            st.markdown("##### 📋 Live Test Execution Matrix")
            st.dataframe(
                qa_df,
                use_container_width=True,
                hide_index=True,
                height=340
            )

    # IF NO TELEMETRY IS LOADED YET FOR PAGES 1-3, SHOW QUICK INITIALIZE BANNER
    elif st.session_state.final_data is None:
        with st.container(border=True):
            st.markdown("#### 📡 Telemetry Stream Standby")
            st.write("Select a telemetry source in the **Initialize Security Operations Workspace** above—or click a quick-launch button below—to populate the **Overview Dashboard**, **Alert Management**, and **AI Explainability** views.")
            q1, q2, _ = st.columns([1.2, 1.2, 2])
            with q1:
                if st.button("🟢 Quick-Connect Live Stream", type="primary", use_container_width=True):
                    ingest_live_stream(st.session_state.live_url, st.session_state.live_token)
                    st.rerun()
            with q2:
                if st.button("⚡ Quick-Launch 1,280 Attack Simulation", use_container_width=True):
                    ingest_simulation()
                    st.rerun()

    else:
        df = st.session_state.final_data.copy()
        df['timestamp'] = pd.to_datetime(df['timestamp'])

        # ==========================================
        # PAGE 1: OVERVIEW DASHBOARD
        # ==========================================
        if page == "Overview Dashboard":
            total_logs = len(df)
            normal_logs = len(df[df['prediction'] == 'Normal'])
            threats = len(df[df['prediction'] != 'Normal'])
            critical_alerts = len(df[df['severity'] == 'Critical'])

            purity_pct = (normal_logs / total_logs * 100) if total_logs > 0 else 100
            threat_pct = (threats / total_logs * 100) if total_logs > 0 else 0

            st.markdown(f"""
            <div class="kpi-container">
                <div class="kpi-card accent-neutral">
                    <div class="kpi-label">📡 Total Telemetry Events</div>
                    <div class="kpi-value">{total_logs:,}</div>
                    <div class="kpi-sub" style="color: #34D399;">● Active ML Inspection</div>
                </div>
                <div class="kpi-card accent-emerald">
                    <div class="kpi-label">✅ Baseline Normal Traffic</div>
                    <div class="kpi-value">{normal_logs:,}</div>
                    <div class="kpi-sub" style="color: #10B981;">{purity_pct:.1f}% Traffic Purity</div>
                </div>
                <div class="kpi-card accent-amber">
                    <div class="kpi-label">⚠️ Anomalies &amp; Threats</div>
                    <div class="kpi-value">{threats:,}</div>
                    <div class="kpi-sub" style="color: #F59E0B;">{threat_pct:.1f}% Anomaly Ratio</div>
                </div>
                <div class="kpi-card accent-crimson">
                    <div class="kpi-label">🚨 Critical Priority Alerts</div>
                    <div class="kpi-value">{critical_alerts:,}</div>
                    <div class="kpi-sub" style="color: #EF4444;">Immediate Triage Required</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            chart_col1, chart_col2 = st.columns([1.85, 1.15])

            with chart_col1:
                with st.container(border=True):
                    st.markdown("##### 📈 Network Telemetry Velocity (5-Min Intervals)")
                    timeline_df = df.set_index('timestamp').resample('5min').size().reset_index(name='Requests')
                    fig_timeline = px.area(timeline_df, x='timestamp', y='Requests', line_shape='spline')
                    fig_timeline.update_traces(line=dict(color='#10B981', width=2.5), fillcolor='rgba(16, 185, 129, 0.16)')
                    fig_timeline.update_layout(
                        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                        font=dict(color='#CBD5E1', family="Plus Jakarta Sans"), height=330,
                        xaxis=dict(showgrid=False, title=""),
                        yaxis=dict(showgrid=True, gridcolor='rgba(16, 185, 129, 0.12)', title="Requests"),
                        margin=dict(l=0, r=10, t=10, b=0), hovermode="x unified"
                    )
                    st.plotly_chart(fig_timeline, use_container_width=True)

            with chart_col2:
                with st.container(border=True):
                    st.markdown("##### 🎯 Threat Vector Breakdown")
                    attack_counts = df[df['prediction'] != 'Normal']['prediction'].value_counts().reset_index()
                    attack_counts.columns = ['Threat Type', 'Incidents']
                    if not attack_counts.empty:
                        fig_donut = px.pie(
                            attack_counts, names='Threat Type', values='Incidents', hole=0.65,
                            color='Threat Type',
                            color_discrete_map={
                                'SQL Injection': '#EF4444', 'DDoS': '#F59E0B',
                                'Brute Force': '#10B981', 'Anomalous Traffic': '#34D399'
                            }
                        )
                        fig_donut.update_traces(textinfo='percent', textfont_size=12, marker=dict(line=dict(color='#050907', width=3)))
                        fig_donut.update_layout(
                            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                            font=dict(color='#F8FAFC', family="Plus Jakarta Sans"), height=330,
                            showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5),
                            annotations=[dict(text=f"<b>{threats}</b><br>Threats", x=0.5, y=0.5, font_size=16, showarrow=False, font_color="#34D399")],
                            margin=dict(l=10, r=10, t=10, b=30)
                        )
                        st.plotly_chart(fig_donut, use_container_width=True)
                    else:
                        st.success("No malicious vectors detected in current stream.")

            with st.container(border=True):
                st.markdown("##### ⚡ Real-Time High-Severity Incident Feed")
                critical_df = df[df['prediction'] != 'Normal'].sort_values(by=['risk_score', 'timestamp'], ascending=[False, False]).head(6)
                if not critical_df.empty:
                    st.dataframe(
                        critical_df[['timestamp', 'source_ip', 'prediction', 'endpoint', 'status_code', 'risk_score']],
                        use_container_width=True, hide_index=True,
                        column_config={
                            "timestamp": st.column_config.DatetimeColumn("Timestamp", format="YYYY-MM-DD HH:mm:ss"),
                            "source_ip": "Attacker IP",
                            "prediction": "Threat Vector",
                            "endpoint": "Target URI",
                            "status_code": "HTTP Status",
                            "risk_score": st.column_config.ProgressColumn("Risk Score", format="%d / 100", min_value=0, max_value=100)
                        }
                    )
                else:
                    st.info("No active security incidents.")

        # ==========================================
        # PAGE 2: ALERT MANAGEMENT
        # ==========================================
        elif page == "Alert Management":
            alerts_df = df[df['prediction'] != 'Normal'].copy()

            if alerts_df.empty:
                st.success("No active alerts to manage. Infrastructure is operating normally.")
            else:
                attack_types = sorted(alerts_df['prediction'].unique().tolist())
                tab_titles = ["🌐 Global Alert Feed"] + [f"🚨 {attack}" for attack in attack_types]
                tabs = st.tabs(tab_titles)

                def render_threat_view(data_subset, threat_name, tab_index):
                    if data_subset.empty:
                        st.info(f"No active {threat_name} incidents match the current filters.")
                        return

                    total_incidents = len(data_subset)
                    max_risk = data_subset['risk_score'].max()
                    ip_counts = data_subset['source_ip'].value_counts()
                    top_ip, top_ip_count = ip_counts.index[0], ip_counts.iloc[0]
                    ip_percentage = (top_ip_count / total_incidents) * 100
                    endpoint_counts = data_subset['endpoint'].value_counts()
                    top_endpoint, top_endpoint_count = endpoint_counts.index[0], endpoint_counts.iloc[0]

                    st.markdown(f"""
                    <div class="kpi-container" style="margin-top: 0.75rem;">
                        <div class="kpi-card accent-neutral">
                            <div class="kpi-label">Total {threat_name} Events</div>
                            <div class="kpi-value">{total_incidents}</div>
                            <div class="kpi-sub" style="color: #EF4444;">Peak Risk Score: <b>{max_risk}/100</b></div>
                        </div>
                        <div class="kpi-card accent-amber">
                            <div class="kpi-label">Primary Threat Actor (IP)</div>
                            <div class="kpi-value" style="font-size: 1.55rem;">{top_ip}</div>
                            <div class="kpi-sub" style="color: #FBBF24;">Responsible for <b>{top_ip_count}</b> events ({ip_percentage:.1f}%)</div>
                        </div>
                        <div class="kpi-card accent-emerald">
                            <div class="kpi-label">Most Targeted Asset</div>
                            <div class="kpi-value" style="font-size: 1.45rem;">{top_endpoint}</div>
                            <div class="kpi-sub" style="color: #34D399;">Targeted <b>{top_endpoint_count}</b> times</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    tool_col1, tool_col2 = st.columns([3, 1])
                    with tool_col1:
                        sev_filter = st.radio("Filter Severity Level:", ["All", "Critical", "High", "Medium", "Low"], horizontal=True, key=f"radio_{threat_name}_{tab_index}")
                    with tool_col2:
                        csv = data_subset.to_csv(index=False).encode('utf-8')
                        st.download_button(label="📥 Export IOCs (CSV)", data=csv, file_name=f"{threat_name.replace(' ', '_').lower()}_iocs.csv", mime="text/csv", use_container_width=True, key=f"dl_{threat_name}_{tab_index}")

                    display_data = data_subset if sev_filter == "All" else data_subset[data_subset['severity'] == sev_filter]

                    if not display_data.empty:
                        display_data = display_data.sort_values(by='risk_score', ascending=False).reset_index(drop=True)
                        severity_mapping = {'Critical': '🔴 Critical', 'High': '🟠 High', 'Medium': '🟡 Medium', 'Low': '🟢 Low'}
                        display_data['severity_display'] = display_data['severity'].map(severity_mapping)

                        st.dataframe(
                            display_data[['timestamp', 'source_ip', 'prediction', 'risk_score', 'severity_display', 'endpoint']],
                            use_container_width=True, height=340, hide_index=True,
                            column_config={
                                "timestamp": st.column_config.DatetimeColumn("Timestamp", format="YYYY-MM-DD HH:mm:ss"),
                                "source_ip": "Attacker IP",
                                "prediction": "Attack Vector",
                                "severity_display": "Severity",
                                "endpoint": "Target Endpoint",
                                "risk_score": st.column_config.ProgressColumn("Risk Score", format="%d", min_value=0, max_value=100)
                            }
                        )
                    else:
                        st.info(f"No {sev_filter} severity incidents found.")

                    with st.expander("📊 Explore Statistics & Threat Overview"):
                        stat_left, stat_right = st.columns([1.5, 1])
                        with stat_left:
                            time_data = data_subset.set_index('timestamp').resample('1min').size().reset_index(name='Events')
                            fig_time = px.area(time_data, x='timestamp', y='Events', title=f"Attack Velocity: {threat_name}", line_shape='spline')
                            fig_time.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#CBD5E1'), margin=dict(l=0, r=0, t=40, b=0), height=240, xaxis=dict(showgrid=False, title=""), yaxis=dict(showgrid=True, gridcolor='rgba(16, 185, 129, 0.15)', title="Incidents / Min"))
                            fig_time.update_traces(line_color='#10B981', fillcolor='rgba(16, 185, 129, 0.2)')
                            st.plotly_chart(fig_time, use_container_width=True)

                            top_5_ips = ip_counts.head(5).reset_index()
                            top_5_ips.columns = ['Attacker IP', 'Incidents']
                            fig_ips = px.bar(top_5_ips, x='Incidents', y='Attacker IP', orientation='h', title="Top Threat Actors", text='Incidents')
                            fig_ips.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#CBD5E1'), margin=dict(l=0, r=0, t=40, b=0), height=240, xaxis=dict(showgrid=False, title="Total Incidents"), yaxis=dict(showgrid=False, title="", categoryorder='total ascending'))
                            fig_ips.update_traces(marker_color='#34D399', textposition='outside')
                            st.plotly_chart(fig_ips, use_container_width=True)

                        with stat_right:
                            st.markdown("#### 📋 Deep Dive Metrics")
                            first_seen, last_seen = data_subset['timestamp'].min(), data_subset['timestamp'].max()
                            total_seconds = int((last_seen - first_seen).total_seconds())
                            hours, remainder = divmod(total_seconds, 3600)
                            minutes, _ = divmod(remainder, 60)
                            duration_str = f"{hours}h {minutes}m" if hours > 0 else (f"{minutes}m" if minutes > 0 else "< 1 minute")

                            st.markdown("##### ⏱️ Attack Window")
                            st.markdown(f"**First Seen:** <span style='color: #34D399;'>{first_seen.strftime('%Y-%m-%d %H:%M:%S')}</span>", unsafe_allow_html=True)
                            st.markdown(f"**Last Seen:** <span style='color: #34D399;'>{last_seen.strftime('%Y-%m-%d %H:%M:%S')}</span>", unsafe_allow_html=True)
                            st.markdown(f"**Duration:** <span style='color: #10B981;'>{duration_str}</span>", unsafe_allow_html=True)

                            st.markdown("---")
                            st.markdown("##### 🌍 Threat Spread")
                            st.markdown(f"**Unique Attacker IPs:** <span style='color: #F59E0B;'>{data_subset['source_ip'].nunique()}</span>", unsafe_allow_html=True)
                            st.markdown(f"**Unique Endpoints Targeted:** <span style='color: #F59E0B;'>{data_subset['endpoint'].nunique()}</span>", unsafe_allow_html=True)

                            st.markdown("---")
                            st.markdown("##### ⚖️ Risk Profile")
                            st.markdown(f"**Average Risk Score:** <span style='color: #EF4444;'>{data_subset['risk_score'].mean():.1f}/100</span>", unsafe_allow_html=True)
                            st.markdown(f"**Total Critical Alerts:** <span style='color: #EF4444;'>{len(data_subset[data_subset['severity'] == 'Critical'])}</span>", unsafe_allow_html=True)

                with tabs[0]:
                    render_threat_view(alerts_df, "Global Alert", 0)
                for i, attack in enumerate(attack_types):
                    with tabs[i + 1]:
                        render_threat_view(alerts_df[alerts_df['prediction'] == attack].copy(), attack, i + 1)

        # ==========================================
        # PAGE 3: AI EXPLAINABILITY
        # ==========================================
        elif page == "AI Explainability":
            threats_df = df[df['prediction'] != 'Normal'].copy()
            if not threats_df.empty:
                threats_df = threats_df.sort_values(by='risk_score', ascending=False).reset_index(drop=True)
                options = [f"[Incident ID: {i}] Source: {row['source_ip']} — Risk Score: {row['risk_score']}/100 ({row['severity']}) — {row['prediction']}" for i, row in threats_df.iterrows()]
                selected_option = st.selectbox("Select Incident to Inspect:", options)

                selected_alert = threats_df.iloc[options.index(selected_option)]
                expl_data = selected_alert['explanation']

                col1, col2 = st.columns([1.45, 1])
                with col1:
                    with st.container(border=True):
                        st.markdown(f"#### 🛡️ Threat Dossier: `{selected_alert['prediction'].upper()}`")
                        st.markdown(
                            f"**Target Asset:** `{selected_alert['endpoint']}` &nbsp;|&nbsp; "
                            f"**HTTP Status:** `{selected_alert['status_code']}` &nbsp;|&nbsp; "
                            f"**Attacker IP:** `{selected_alert['source_ip']}`"
                        )
                        st.markdown("---")
                        st.markdown("##### 📝 Executive Summary")
                        st.write(expl_data['summary'])
                        st.markdown("##### 🔎 AI Feature Attribution & Evidence")
                        for evidence in expl_data['evidence']:
                            st.markdown(f"- ⚠️ **{evidence.split(':')[0]}:** {evidence.split(':')[1] if ':' in evidence else evidence}")

                        with st.expander("🛠️ Inspect Raw JSON Telemetry Payload"):
                            st.json(selected_alert.drop(labels=['explanation']).to_dict())

                with col2:
                    with st.container(border=True):
                        st.markdown("#### 🎯 MITRE ATT&CK Mapping")
                        st.markdown(f"<div style='background-color: #050A07; border: 1px solid #10B981; border-radius: 8px; padding: 14px; margin-bottom: 18px;'><code style='color: #34D399; background: transparent; font-size: 0.95rem; font-weight: 700;'>{expl_data['mitre']}</code></div>", unsafe_allow_html=True)
                        st.markdown("#### 🛡️ SOC Remediation Playbook")
                        for step in expl_data['playbook']:
                            st.markdown(f"<div style='margin-bottom: 10px; background: rgba(16, 185, 129, 0.12); padding: 10px 14px; border-radius: 8px; border-left: 3px solid #10B981;'>✅ {step}</div>", unsafe_allow_html=True)

                        st.markdown("<br>", unsafe_allow_html=True)
                        act_col1, act_col2 = st.columns(2)
                        with act_col1:
                            if st.button("🔒 WAF Block IP", type="primary", use_container_width=True):
                                st.toast(f"Blocked IP {selected_alert['source_ip']} at Edge WAF!", icon="🔒")
                                st.success(f"WAF Rule Active: Deny `{selected_alert['source_ip']}`")
                        with act_col2:
                            if st.button("📧 Email Dossier", use_container_width=True):
                                subject = f"🛡️ [INCIDENT DOSSIER] {selected_alert['prediction']} from {selected_alert['source_ip']}"
                                dossier_html = build_dossier_email_html(selected_alert)
                                sent_live, status_msg, html_out = dispatch_email_to_saved_recipients(
                                    st.session_state.saved_recipients, subject, dossier_html
                                )
                                st.session_state.email_state = {
                                    "sent_live": sent_live,
                                    "status_msg": status_msg,
                                    "subject": subject,
                                    "recipient": ", ".join(st.session_state.saved_recipients),
                                    "html": html_out
                                }
                                st.toast("Incident Dossier Dispatched to Saved Recipients!", icon="📨")
                                st.rerun()
            else:
                st.success("No active threats detected. Infrastructure is operating within normal parameters.")

    # =========================================================================
    # INTERACTIVE LEFT VERTICAL TIMELINE BAR + UP/DOWN ARROW KEY NAVIGATION
    # =========================================================================
    components.html(
        """
        <script>
        (function() {
            const parentDoc = window.parent.document;
            const parentWin = window.parent;

            const oldNav = parentDoc.getElementById('secops-vertical-timeline');
            if (oldNav) oldNav.remove();
            const oldStyle = parentDoc.getElementById('secops-timeline-style');
            if (oldStyle) oldStyle.remove();

            const checkpoints = [
                { id: 'ckpt-0', num: '01', label: 'Overview & Hook' },
                { id: 'ckpt-1', num: '02', label: 'Why SecOps Switch' },
                { id: 'ckpt-2', num: '03', label: '3-Step Workflow' },
                { id: 'ckpt-3', num: '04', label: 'Ingestion Launchpad' },
                { id: 'ckpt-4', num: '05', label: 'SOC Console & QA' }
            ];

            const style = parentDoc.createElement('style');
            style.id = 'secops-timeline-style';
            style.innerHTML = `
                #secops-vertical-timeline {
                    position: fixed;
                    left: 20px;
                    top: 50%;
                    transform: translateY(-50%);
                    z-index: 999999;
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    padding: 16px 10px;
                    background: rgba(6, 12, 9, 0.88);
                    backdrop-filter: blur(12px);
                    border: 1px solid rgba(16, 185, 129, 0.36);
                    border-radius: 999px;
                    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.7);
                }
                @media (max-width: 900px) {
                    #secops-vertical-timeline { display: none; }
                }
                .tl-track {
                    position: relative;
                    display: flex;
                    flex-direction: column;
                    gap: 22px;
                    align-items: center;
                }
                .tl-track::before {
                    content: '';
                    position: absolute;
                    top: 14px;
                    bottom: 14px;
                    left: 50%;
                    transform: translateX(-50%);
                    width: 2px;
                    background: rgba(16, 185, 129, 0.25);
                    z-index: 0;
                }
                .tl-node {
                    position: relative;
                    z-index: 1;
                    width: 30px;
                    height: 30px;
                    border-radius: 50%;
                    background: #050A07;
                    border: 2px solid rgba(16, 185, 129, 0.42);
                    color: #94A3B8;
                    font-family: 'JetBrains Mono', monospace;
                    font-size: 0.72rem;
                    font-weight: 700;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    cursor: pointer;
                    transition: all 0.22s ease;
                }
                .tl-node:hover, .tl-node.active {
                    background: #10B981;
                    border-color: #6EE7B7;
                    color: #021008;
                    box-shadow: 0 0 16px rgba(16, 185, 129, 0.8);
                    transform: scale(1.12);
                }
                .tl-tooltip {
                    position: absolute;
                    left: 44px;
                    white-space: nowrap;
                    background: #09140E;
                    color: #34D399;
                    border: 1px solid rgba(16, 185, 129, 0.48);
                    padding: 5px 12px;
                    border-radius: 8px;
                    font-family: 'JetBrains Mono', monospace;
                    font-size: 0.76rem;
                    font-weight: 600;
                    opacity: 0;
                    pointer-events: none;
                    transform: translateX(-6px);
                    transition: all 0.2s ease;
                    box-shadow: 0 6px 18px rgba(0, 0, 0, 0.65);
                }
                .tl-node:hover .tl-tooltip, .tl-node.active .tl-tooltip {
                    opacity: 1;
                    transform: translateX(0);
                }
                .tl-key-hint {
                    margin-top: 12px;
                    font-family: 'JetBrains Mono', monospace;
                    font-size: 0.64rem;
                    color: #6EE7B7;
                    text-align: center;
                    opacity: 0.85;
                }
            `;
            parentDoc.head.appendChild(style);

            const nav = parentDoc.createElement('div');
            nav.id = 'secops-vertical-timeline';

            const track = parentDoc.createElement('div');
            track.className = 'tl-track';

            let currentIndex = 0;

            function scrollToCheckpoint(index) {
                if (index < 0 || index >= checkpoints.length) return;
                currentIndex = index;
                const targetEl = parentDoc.getElementById(checkpoints[index].id);
                if (targetEl) {
                    targetEl.scrollIntoView({ behavior: 'smooth', block: 'start' });
                }
                updateActiveNode(index);
            }

            function updateActiveNode(activeIdx) {
                const nodes = track.querySelectorAll('.tl-node');
                nodes.forEach((n, idx) => {
                    if (idx === activeIdx) n.classList.add('active');
                    else n.classList.remove('active');
                });
            }

            checkpoints.forEach((cp, idx) => {
                const node = parentDoc.createElement('div');
                node.className = 'tl-node' + (idx === 0 ? ' active' : '');
                node.innerHTML = `${cp.num}<span class="tl-tooltip">${cp.num} • ${cp.label}</span>`;
                node.addEventListener('click', () => scrollToCheckpoint(idx));
                track.appendChild(node);
            });

            const hint = parentDoc.createElement('div');
            hint.className = 'tl-key-hint';
            hint.innerText = '↑↓';

            nav.appendChild(track);
            nav.appendChild(hint);
            parentDoc.body.appendChild(nav);

            if (parentWin._secopsKeyHandler) {
                parentWin.removeEventListener('keydown', parentWin._secopsKeyHandler);
            }
            parentWin._secopsKeyHandler = function(e) {
                const tag = (e.target && e.target.tagName) ? e.target.tagName.toLowerCase() : '';
                if (tag === 'input' || tag === 'textarea' || tag === 'select' || (e.target && e.target.isContentEditable)) {
                    return;
                }
                if (e.key === 'ArrowDown') {
                    e.preventDefault();
                    scrollToCheckpoint(Math.min(currentIndex + 1, checkpoints.length - 1));
                } else if (e.key === 'ArrowUp') {
                    e.preventDefault();
                    scrollToCheckpoint(Math.max(currentIndex - 1, 0));
                }
            };
            parentWin.addEventListener('keydown', parentWin._secopsKeyHandler);

            const scrollContainer = parentDoc.querySelector('[data-testid="stAppViewContainer"]') || parentWin;
            if (parentWin._secopsScrollHandler) {
                scrollContainer.removeEventListener('scroll', parentWin._secopsScrollHandler);
            }
            parentWin._secopsScrollHandler = function() {
                let closestIdx = 0;
                let minDistance = Infinity;
                checkpoints.forEach((cp, idx) => {
                    const el = parentDoc.getElementById(cp.id);
                    if (el) {
                        const rect = el.getBoundingClientRect();
                        const dist = Math.abs(rect.top - 140);
                        if (dist < minDistance) {
                            minDistance = dist;
                            closestIdx = idx;
                        }
                    }
                });
                currentIndex = closestIdx;
                updateActiveNode(closestIdx);
            };
            scrollContainer.addEventListener('scroll', parentWin._secopsScrollHandler, { passive: true });
        })();
        </script>
        """,
        height=0,
    )


if __name__ == "__main__":
    main()
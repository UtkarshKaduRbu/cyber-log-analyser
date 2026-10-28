import streamlit as st
import pandas as pd
import os
import re
import random
from datetime import datetime, timedelta
from src.log_generator import initialize_live_logs, append_live_logs, LIVE_LOG_PATH
import log_agent

AGENT_PORT = int(os.environ.get("LOG_AGENT_PORT", log_agent.DEFAULT_PORT))
AGENT_TOKEN = os.environ.get("LOG_AGENT_TOKEN", "")

st.set_page_config(page_title="FinCore Banking Portal (Target Website)", page_icon="🏦", layout="wide")

# Ensure baseline logs exist when the website starts
if not os.path.exists(LIVE_LOG_PATH):
    initialize_live_logs()

@st.cache_resource
def start_log_agent():
    """Exposes this website's access log at http://<host>:<port> for the SOC analyser."""
    return log_agent.start_in_background(LIVE_LOG_PATH, AGENT_PORT, AGENT_TOKEN)

start_log_agent()

def log_request(source_ip, method, endpoint, status_code, response_time, user_agent, username="-", bytes_sent=1200, event_type="live_test"):
    """Writes a single HTTP request to the shared live_logs.csv file."""
    entry = [{
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'source_ip': source_ip,
        'destination_ip': '10.0.0.5',
        'request_method': method,
        'endpoint': endpoint,
        'status_code': status_code,
        'response_time': response_time,
        'user_agent': user_agent,
        'username': username,
        'request_count': 1,
        'bytes_sent': bytes_sent,
        'event_type': event_type
    }]
    append_live_logs(entry)

def main():
    st.title("🏦 FinCore Enterprise Portal (Live Target Website)")
    st.caption("Every action on this page generates real server telemetry.")
    st.info(
        f"📡 **Log API online:** `http://localhost:{AGENT_PORT}`"
        + (" (token required)" if AGENT_TOKEN else " (no token set)")
        + " — enter this URL in the Log Analyser to stream this website's logs in real time. "
        "The analyser does not read this site's files."
    )
    
    # --- SIMULATED NETWORK HEADER ---
    with st.container(border=True):
        col_ip, col_ua, col_reset = st.columns([1.5, 2, 1])
        with col_ip:
            client_ip = st.text_input("🌐 Your Simulated Client IP:", value="45.33.22.11", help="Change this IP to track your specific actions in the SOC Dashboard.")
        with col_ua:
            user_agent = st.selectbox("🖥️ Simulated Browser / Tool:", [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                "sqlmap/1.7.2#stable ([http://sqlmap.org](http://sqlmap.org))",
                "Hydra v9.4 (Brute-Force Scanner)",
                "BotNet-Flood/2.0"
            ])
        with col_reset:
            st.write("")
            if st.button("♻️ Reset Server Logs", use_container_width=True):
                initialize_live_logs()
                st.toast("Reset live_logs.csv to 300 baseline normal logs!", icon="✅")

    st.markdown("---")

    # --- THREE INTERACTIVE ZONES ---
    col1, col2, col3 = st.columns(3)

    # 1. NORMAL BROWSING & SQL INJECTION (SEARCH)
    with col1:
        st.subheader("🔍 1. Product & Database Search")
        st.write("Test normal search queries or inject SQL commands to test payload detection.")
        
        with st.form("search_form"):
            search_query = st.text_input("Search Financial Products:", placeholder="e.g., Home Loan or ' OR 1=1 --")
            quick_payload = st.selectbox("Or pick a test payload:", [
                "(Use typed query above)",
                "' OR 1=1 --",
                "UNION SELECT username, password FROM users",
                "admin' --",
                "DROP TABLE transactions"
            ])
            search_submitted = st.form_submit_button("🔎 Execute Search", use_container_width=True)
            
            if search_submitted:
                final_query = search_query if quick_payload == "(Use typed query above)" else quick_payload
                if not final_query:
                    final_query = "savings_account"
                    
                endpoint = f"/search?q={final_query}"
                sql_pattern = re.compile(r"(UNION|SELECT|DROP|OR 1=1|--|')", re.IGNORECASE)
                
                if sql_pattern.search(final_query):
                    # Malicious SQLi telemetry (high latency + HTTP 500 error)
                    log_request(client_ip, "GET", endpoint, 500, random.randint(420, 680), user_agent, "-", 350, "sql_injection")
                    st.error(f"⚠️ HTTP 500 Database Error logged for `{endpoint}`!")
                else:
                    # Normal search telemetry
                    log_request(client_ip, "GET", endpoint, 200, random.randint(35, 95), user_agent, "-", 2400, "normal")
                    st.success(f"✅ HTTP 200 OK logged for `{endpoint}`.")

        st.markdown("##### Normal Page Navigation")
        nav_c1, nav_c2 = st.columns(2)
        if nav_c1.button("🏠 Visit /home", use_container_width=True):
            log_request(client_ip, "GET", "/home", 200, random.randint(30, 80), user_agent, "-", 3100, "normal")
            st.toast("Logged GET /home (HTTP 200)")
        if nav_c2.button("💳 Visit /products", use_container_width=True):
            log_request(client_ip, "GET", "/products", 200, random.randint(40, 110), user_agent, "-", 4200, "normal")
            st.toast("Logged GET /products (HTTP 200)")

    # 2. CUSTOMER LOGIN & BRUTE FORCE
    with col2:
        st.subheader("🔐 2. Customer Authentication")
        st.write("Test normal login (`admin` / `FinCore2026`) or trigger repeated failed logins (HTTP 401).")
        
        with st.form("login_form"):
            username = st.text_input("Username:", value="admin")
            password = st.text_input("Password:", type="password", value="wrong_pass_123")
            login_submitted = st.form_submit_button("🔑 Sign In (Single Attempt)", use_container_width=True)
            
            if login_submitted:
                if username == "admin" and password == "FinCore2026":
                    log_request(client_ip, "POST", "/login", 200, random.randint(45, 90), user_agent, username, 1500, "normal")
                    st.success("✅ Login Successful! (HTTP 200 logged)")
                else:
                    log_request(client_ip, "POST", "/login", 401, random.randint(55, 95), user_agent, username, 256, "brute_force")
                    st.warning("❌ Invalid Credentials! (HTTP 401 Unauthorized logged)")

        st.markdown("##### Automated Brute-Force Simulator")
        st.caption("Simulates a credential-stuffing script sending 15 rapid failed logins from your IP.")
        if st.button("⚡ Launch 15 Failed Logins (Brute-Force)", type="primary", use_container_width=True):
            now = datetime.now()
            entries = []
            for i in range(15):
                entries.append({
                    'timestamp': (now + timedelta(seconds=i)).strftime('%Y-%m-%d %H:%M:%S'),
                    'source_ip': client_ip,
                    'destination_ip': '10.0.0.5',
                    'request_method': 'POST',
                    'endpoint': '/login',
                    'status_code': 401,
                    'response_time': random.randint(50, 85),
                    'user_agent': 'Hydra v9.4 (Brute-Force Scanner)',
                    'username': f"admin_attempt_{i+1}",
                    'request_count': 1,
                    'bytes_sent': 256,
                    'event_type': 'brute_force'
                })
            append_live_logs(entries)
            st.error(f"🚨 Sent 15 rapid HTTP 401 failed logins from `{client_ip}`!")

    # 3. VOLUMETRIC DDOS ATTACK
    with col3:
        st.subheader("🌊 3. Server Stress / DDoS Flood")
        st.write("Simulate a high-velocity volumetric flood that overwhelms server capacity (HTTP 503).")
        
        flood_count = st.slider("Number of Simultaneous Requests:", min_value=55, max_value=120, value=75)
        
        if st.button(f"🔥 Launch DDoS Flood ({flood_count} Requests)", type="primary", use_container_width=True):
            now = datetime.now()
            entries = []
            for i in range(flood_count):
                entries.append({
                    'timestamp': (now + timedelta(milliseconds=i * 20)).strftime('%Y-%m-%d %H:%M:%S'),
                    'source_ip': client_ip,
                    'destination_ip': '10.0.0.5',
                    'request_method': 'GET',
                    'endpoint': '/',
                    'status_code': 503,
                    'response_time': random.randint(1800, 4500),
                    'user_agent': 'BotNet-Flood/2.0',
                    'username': '-',
                    'request_count': 1,
                    'bytes_sent': 0,
                    'event_type': 'ddos'
                })
            append_live_logs(entries)
            st.error(f"🚨 flooded `/` with {flood_count} HTTP 503 requests from `{client_ip}`!")

    # --- LIVE SERVER LOG TAIL ---
    st.markdown("---")
    st.subheader("📜 Live Web Server Access Log (`data/live_logs.csv` - Last 10 Requests)")
    if os.path.exists(LIVE_LOG_PATH):
        live_df = pd.read_csv(LIVE_LOG_PATH)
        st.caption(f"Total entries in live log file: **{len(live_df)}** (Includes 300 baseline normal logs + your live actions)")
        st.dataframe(live_df.tail(10).iloc[::-1], use_container_width=True, hide_index=True)

if __name__ == "__main__":
    main()
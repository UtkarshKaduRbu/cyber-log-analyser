import pandas as pd
import random
from datetime import datetime, timedelta
import os

LIVE_LOG_PATH = os.path.join("data", "live_logs.csv")

def random_ip():
    return f"{random.randint(11, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 254)}"

def generate_logs(num_normal=1000, num_bruteforce=50, num_sqli=30, num_ddos=200):
    """Generates synthetic server logs in CSV, JSON, and XLSX formats."""
    logs = []
    start_time = datetime.now() - timedelta(days=1)
    
    endpoints = ['/home', '/products', '/about', '/contact', '/api/data']
    user_agents = ['Mozilla/5.0 (Windows NT 10.0)', 'Chrome/91.0.4472.124', 'Safari/537.36', 'curl/7.68.0']

    # 1. Normal Traffic
    for _ in range(num_normal):
        logs.append({
            'timestamp': start_time + timedelta(minutes=random.randint(1, 1440)),
            'source_ip': random_ip(),
            'destination_ip': '10.0.0.5',
            'request_method': random.choice(['GET', 'POST']),
            'endpoint': random.choice(endpoints),
            'status_code': random.choice([200, 200, 200, 301, 404]),
            'response_time': random.randint(20, 150),
            'user_agent': random.choice(user_agents),
            'username': '-',
            'request_count': 1,
            'bytes_sent': random.randint(500, 5000),
            'event_type': 'normal'
        })

    # 2. Brute-Force Attack
    bf_ip = random_ip()
    bf_time = start_time + timedelta(hours=5)
    for i in range(num_bruteforce):
        logs.append({
            'timestamp': bf_time + timedelta(seconds=i * 2),
            'source_ip': bf_ip,
            'destination_ip': '10.0.0.5',
            'request_method': 'POST',
            'endpoint': '/login',
            'status_code': 401,
            'response_time': random.randint(50, 80),
            'user_agent': 'python-requests/2.25.1',
            'username': f'admin_{i}',
            'request_count': 1,
            'bytes_sent': 256,
            'event_type': 'brute_force'
        })

    # 3. SQL Injection
    sqli_payloads = ["' OR 1=1 --", "admin' --", "UNION SELECT", "DROP TABLE users"]
    for _ in range(num_sqli):
        logs.append({
            'timestamp': start_time + timedelta(minutes=random.randint(1, 1440)),
            'source_ip': random_ip(),
            'destination_ip': '10.0.0.5',
            'request_method': 'GET',
            'endpoint': f"/search?q={random.choice(sqli_payloads)}",
            'status_code': random.choice([200, 500]),
            'response_time': random.randint(100, 500),
            'user_agent': random.choice(user_agents),
            'username': '-',
            'request_count': 1,
            'bytes_sent': random.randint(100, 1000),
            'event_type': 'sql_injection'
        })

    # 4. DDoS Attack
    ddos_time = start_time + timedelta(hours=12)
    ddos_ip = random_ip()
    for i in range(num_ddos):
        logs.append({
            'timestamp': ddos_time + timedelta(milliseconds=i * 10),
            'source_ip': ddos_ip if i % 2 == 0 else random_ip(),
            'destination_ip': '10.0.0.5',
            'request_method': 'GET',
            'endpoint': '/',
            'status_code': 503,
            'response_time': random.randint(1000, 5000),
            'user_agent': 'BotNet/1.0',
            'username': '-',
            'request_count': 1,
            'bytes_sent': 0,
            'event_type': 'ddos'
        })

    df = pd.DataFrame(logs)
    df = df.sort_values(by='timestamp').reset_index(drop=True)
    df['timestamp'] = df['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
    
    os.makedirs("data", exist_ok=True)
    csv_path = os.path.join("data", "generated_logs.csv")
    json_path = os.path.join("data", "generated_logs.json")
    xlsx_path = os.path.join("data", "generated_logs.xlsx")
    
    df.to_csv(csv_path, index=False)
    df.to_json(json_path, orient="records", indent=2)
    df.to_excel(xlsx_path, index=False, engine="openpyxl")
    
    return csv_path

def initialize_live_logs(num_baseline=300, force_reset=False):
    """
    Pre-seeds data/live_logs.csv with 300 normal baseline requests so the 
    Isolation Forest model has a healthy statistical baseline.
    """
    os.makedirs("data", exist_ok=True)
    if os.path.exists(LIVE_LOG_PATH) and not force_reset and num_baseline == 300:
        # Rewrite fresh baseline when explicitly called to reset
        pass

    logs = []
    now = datetime.now()
    endpoints = ['/home', '/products', '/about', '/contact', '/api/data']
    user_agents = ['Mozilla/5.0 (Windows NT 10.0)', 'Chrome/122.0.0.0', 'Safari/537.36']

    for _ in range(num_baseline):
        logs.append({
            'timestamp': (now - timedelta(minutes=random.randint(5, 180))).strftime('%Y-%m-%d %H:%M:%S'),
            'source_ip': random_ip(),
            'destination_ip': '10.0.0.5',
            'request_method': 'GET',
            'endpoint': random.choice(endpoints),
            'status_code': 200,
            'response_time': random.randint(25, 120),
            'user_agent': random.choice(user_agents),
            'username': '-',
            'request_count': 1,
            'bytes_sent': random.randint(800, 4500),
            'event_type': 'normal'
        })

    df = pd.DataFrame(logs).sort_values(by='timestamp').reset_index(drop=True)
    df.to_csv(LIVE_LOG_PATH, index=False)
    return LIVE_LOG_PATH

def append_live_logs(new_entries):
    """Appends one or more live log dictionary entries to data/live_logs.csv."""
    if not os.path.exists(LIVE_LOG_PATH):
        initialize_live_logs()
        
    if isinstance(new_entries, dict):
        new_entries = [new_entries]
        
    new_df = pd.DataFrame(new_entries)
    new_df.to_csv(LIVE_LOG_PATH, mode='a', header=False, index=False)
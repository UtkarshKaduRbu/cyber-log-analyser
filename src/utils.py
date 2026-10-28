import os
import random
import pandas as pd
from datetime import datetime, timedelta

LIVE_LOG_PATH = os.path.join("data", "live_logs.csv")

def init_live_logs(force_reset=False):
    """
    Initializes data/live_logs.csv with 300 normal baseline requests 
    so the Isolation Forest model has a healthy statistical baseline.
    """
    os.makedirs("data", exist_ok=True)
    
    if os.path.exists(LIVE_LOG_PATH) and not force_reset:
        return LIVE_LOG_PATH

    logs = []
    now = datetime.now()
    start_time = now - timedelta(hours=2)
    
    endpoints = ['/home', '/products', '/account', '/contact', '/api/rates']
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
        'Chrome/122.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_3)'
    ]

    for _ in range(300):
        random_ip = f"{random.randint(11, 220)}.{random.randint(1, 254)}.{random.randint(1, 254)}.{random.randint(1, 254)}"
        logs.append({
            'timestamp': (start_time + timedelta(seconds=random.randint(1, 7100))).strftime('%Y-%m-%d %H:%M:%S'),
            'source_ip': random_ip,
            'destination_ip': '10.0.0.5',
            'request_method': random.choice(['GET', 'GET', 'POST']),
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
    """Appends one or more live HTTP log dictionaries to data/live_logs.csv."""
    init_live_logs(force_reset=False)
    
    if isinstance(new_entries, dict):
        new_entries = [new_entries]
        
    new_df = pd.DataFrame(new_entries)
    new_df.to_csv(LIVE_LOG_PATH, mode='a', header=False, index=False)
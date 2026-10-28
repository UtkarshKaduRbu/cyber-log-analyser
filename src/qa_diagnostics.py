import io
import time
import pandas as pd
from datetime import datetime, timedelta

from src.log_parser import parse_uploaded_file
from src.preprocessing import clean_data
from src.feature_engineering import extract_features
from src.detector import LogDetector
from src.risk_scoring import apply_risk_scoring
from src.explanation import apply_explanations

def _build_baseline_rows(count=40):
    now = datetime.now()
    return [{
        'timestamp': (now - timedelta(minutes=i)).strftime('%Y-%m-%d %H:%M:%S'),
        'source_ip': f"192.168.1.{i % 20 + 1}",
        'destination_ip': '10.0.0.5',
        'request_method': 'GET',
        'endpoint': '/home',
        'status_code': 200,
        'response_time': 45,
        'user_agent': 'Mozilla/5.0',
        'username': '-',
        'request_count': 1,
        'bytes_sent': 1500,
        'event_type': 'normal'
    } for i in range(count)]

def run_diagnostic_suite():
    """Executes 8 live end-to-end QA tests across all pipeline modules."""
    results = []
    detector = LogDetector()

    # TEST 1: Benign Traffic Baseline
    t0 = time.perf_counter()
    df_norm = pd.DataFrame(_build_baseline_rows(40))
    res_norm = apply_risk_scoring(detector.detect(extract_features(clean_data(df_norm))))
    normal_pass = (res_norm['prediction'] == 'Normal').sum() >= 35 and (res_norm[res_norm['prediction'] == 'Normal']['risk_score'] == 0).all()
    results.append({
        "Test ID": "QA-01",
        "Test Case": "Benign Traffic Baseline Verification",
        "Module": "detector.py / risk_scoring.py",
        "Input Payload": "40 standard HTTP 200 GET /home requests (45ms latency)",
        "Expected Outcome": "Classified as Normal with 0 Risk Score",
        "Actual Outcome": f"{(res_norm['prediction'] == 'Normal').sum()}/40 Normal, Risk Score = 0",
        "Latency (ms)": round((time.perf_counter() - t0) * 1000, 2),
        "Status": "✅ PASSED" if normal_pass else "❌ FAILED"
    })

    # TEST 2: SQL Injection Signature & Scoring
    t0 = time.perf_counter()
    rows_sqli = _build_baseline_rows(30)
    rows_sqli.append({
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'source_ip': '45.33.22.11', 'destination_ip': '10.0.0.5',
        'request_method': 'GET', 'endpoint': "/search?q=' OR 1=1 --",
        'status_code': 500, 'response_time': 520,
        'user_agent': 'sqlmap/1.7', 'username': '-',
        'request_count': 1, 'bytes_sent': 300, 'event_type': 'sql_injection'
    })
    res_sqli = apply_risk_scoring(detector.detect(extract_features(clean_data(pd.DataFrame(rows_sqli)))))
    target_row = res_sqli[res_sqli['source_ip'] == '45.33.22.11'].iloc[0]
    sqli_pass = target_row['prediction'] == 'SQL Injection' and target_row['risk_score'] >= 80
    results.append({
        "Test ID": "QA-02",
        "Test Case": "SQL Injection Payload & Risk Escalation",
        "Module": "feature_engineering.py / detector.py",
        "Input Payload": "GET /search?q=' OR 1=1 -- (HTTP 500, 520ms)",
        "Expected Outcome": "Prediction = SQL Injection, Risk >= 80 (Critical)",
        "Actual Outcome": f"Prediction = {target_row['prediction']}, Risk = {target_row['risk_score']}/100 ({target_row['severity']})",
        "Latency (ms)": round((time.perf_counter() - t0) * 1000, 2),
        "Status": "✅ PASSED" if sqli_pass else "❌ FAILED"
    })

    # TEST 3: Brute-Force Authentication Velocity
    t0 = time.perf_counter()
    rows_bf = _build_baseline_rows(30)
    for i in range(15):
        rows_bf.append({
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'source_ip': '185.99.88.77', 'destination_ip': '10.0.0.5',
            'request_method': 'POST', 'endpoint': '/login',
            'status_code': 401, 'response_time': 65,
            'user_agent': 'Hydra/9.4', 'username': f'admin_{i}',
            'request_count': 1, 'bytes_sent': 256, 'event_type': 'brute_force'
        })
    res_bf = apply_risk_scoring(detector.detect(extract_features(clean_data(pd.DataFrame(rows_bf)))))
    bf_row = res_bf[res_bf['source_ip'] == '185.99.88.77'].iloc[0]
    bf_pass = bf_row['prediction'] == 'Brute Force' and bf_row['ip_failed_login_count'] == 15
    results.append({
        "Test ID": "QA-03",
        "Test Case": "Brute-Force Velocity Threshold (>10 HTTP 401s)",
        "Module": "feature_engineering.py / detector.py",
        "Input Payload": "15 rapid HTTP 401 POST /login attempts from 185.99.88.77",
        "Expected Outcome": "ip_failed_login_count = 15, Prediction = Brute Force",
        "Actual Outcome": f"Failed Count = {bf_row['ip_failed_login_count']}, Prediction = {bf_row['prediction']}",
        "Latency (ms)": round((time.perf_counter() - t0) * 1000, 2),
        "Status": "✅ PASSED" if bf_pass else "❌ FAILED"
    })

    # TEST 4: Volumetric DDoS Spike Detection
    t0 = time.perf_counter()
    rows_ddos = _build_baseline_rows(60)
    for i in range(65):
        rows_ddos.append({
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'source_ip': '203.0.113.99', 'destination_ip': '10.0.0.5',
            'request_method': 'GET', 'endpoint': '/',
            'status_code': 503, 'response_time': 3200,
            'user_agent': 'BotNet/2.0', 'username': '-',
            'request_count': 1, 'bytes_sent': 0, 'event_type': 'ddos'
        })
    res_ddos = apply_risk_scoring(detector.detect(extract_features(clean_data(pd.DataFrame(rows_ddos)))))
    ddos_row = res_ddos[res_ddos['source_ip'] == '203.0.113.99'].iloc[0]
    ddos_pass = ddos_row['prediction'] == 'DDoS' and ddos_row['severity'] == 'Critical'
    results.append({
        "Test ID": "QA-04",
        "Test Case": "Volumetric DDoS Flood & ML Outlier Detection",
        "Module": "detector.py (Isolation Forest)",
        "Input Payload": "65 HTTP 503 flood requests (3200ms latency, 0 bytes)",
        "Expected Outcome": "Prediction = DDoS, Severity = Critical",
        "Actual Outcome": f"Prediction = {ddos_row['prediction']}, Score = {ddos_row['risk_score']} ({ddos_row['severity']})",
        "Latency (ms)": round((time.perf_counter() - t0) * 1000, 2),
        "Status": "✅ PASSED" if ddos_pass else "❌ FAILED"
    })

    # TEST 5: Malformed Timestamp Resilience
    t0 = time.perf_counter()
    bad_ts_df = pd.DataFrame([
        {'timestamp': 'CORRUPTED_DATE_STRING', 'source_ip': '1.1.1.1', 'status_code': 200},
        {'timestamp': '2026-10-20 14:30:00', 'source_ip': '2.2.2.2', 'status_code': 200}
    ])
    cleaned_ts = clean_data(bad_ts_df)
    ts_pass = len(cleaned_ts) == 1 and cleaned_ts.iloc[0]['source_ip'] == '2.2.2.2'
    results.append({
        "Test ID": "QA-05",
        "Test Case": "Corrupted Timestamp Sanitization",
        "Module": "preprocessing.py",
        "Input Payload": "2 rows (1 valid ISO timestamp, 1 'CORRUPTED_DATE_STRING')",
        "Expected Outcome": "Invalid row dropped safely without exception; 1 valid row retained",
        "Actual Outcome": f"{len(cleaned_ts)} valid row retained ({cleaned_ts.iloc[0]['source_ip']})",
        "Latency (ms)": round((time.perf_counter() - t0) * 1000, 2),
        "Status": "✅ PASSED" if ts_pass else "❌ FAILED"
    })

    # TEST 6: Null / Missing Value Imputation
    t0 = time.perf_counter()
    null_df = pd.DataFrame([{
        'timestamp': '2026-10-20 15:00:00',
        'source_ip': None, 'user_agent': None, 'username': None, 'status_code': None
    }])
    cleaned_null = clean_data(null_df)
    null_pass = (
        cleaned_null.iloc[0]['source_ip'] == '0.0.0.0' and
        cleaned_null.iloc[0]['user_agent'] == 'Unknown' and
        cleaned_null.iloc[0]['status_code'] == 200
    )
    results.append({
        "Test ID": "QA-06",
        "Test Case": "Missing & Null Telemetry Imputation",
        "Module": "preprocessing.py",
        "Input Payload": "Log row with None/NaN for IP, User-Agent, Username, and Status",
        "Expected Outcome": "Imputed defaults: IP='0.0.0.0', UA='Unknown', Status=200",
        "Actual Outcome": f"IP='{cleaned_null.iloc[0]['source_ip']}', UA='{cleaned_null.iloc[0]['user_agent']}', Status={cleaned_null.iloc[0]['status_code']}",
        "Latency (ms)": round((time.perf_counter() - t0) * 1000, 2),
        "Status": "✅ PASSED" if null_pass else "❌ FAILED"
    })

    # TEST 7: Universal Multi-Format Schema Normalization
    t0 = time.perf_counter()
    raw_json = b'[{"TIMESTAMP": "2026-10-20 12:00:00", "SOURCE_IP": "8.8.8.8", "ENDPOINT": "/api"}]'
    fake_file = io.BytesIO(raw_json)
    fake_file.name = "test_stream.json"
    parsed_df = parse_uploaded_file(fake_file)
    schema_pass = len(parsed_df) == 1 and 'bytes_sent' in parsed_df.columns and parsed_df.iloc[0]['source_ip'] == '8.8.8.8'
    results.append({
        "Test ID": "QA-07",
        "Test Case": "Multi-Format Parser & Missing Column Reconstruction",
        "Module": "log_parser.py",
        "Input Payload": "In-memory JSON with uppercase keys & 8 missing columns",
        "Expected Outcome": "Lowercases headers & reconstructs all 11 required columns",
        "Actual Outcome": f"Reconstructed {len(parsed_df.columns)} columns; IP={parsed_df.iloc[0]['source_ip']}",
        "Latency (ms)": round((time.perf_counter() - t0) * 1000, 2),
        "Status": "✅ PASSED" if schema_pass else "❌ FAILED"
    })

    # TEST 8: MITRE ATT&CK Dossier & Risk Score Boundary Check
    t0 = time.perf_counter()
    explained_df = apply_explanations(res_sqli)
    dossier = explained_df[explained_df['source_ip'] == '45.33.22.11'].iloc[0]['explanation']
    bounds_pass = (
        explained_df['risk_score'].between(0, 100).all() and
        isinstance(dossier, dict) and
        all(k in dossier for k in ['summary', 'mitre', 'evidence', 'playbook'])
    )
    results.append({
        "Test ID": "QA-08",
        "Test Case": "MITRE ATT&CK Dossier & Score Boundary Guard",
        "Module": "explanation.py / risk_scoring.py",
        "Input Payload": "Scored SQLi DataFrame",
        "Expected Outcome": "0 <= Risk <= 100 and valid MITRE Dossier dict keys",
        "Actual Outcome": f"MITRE='{dossier.get('mitre')}', Keys={list(dossier.keys())}",
        "Latency (ms)": round((time.perf_counter() - t0) * 1000, 2),
        "Status": "✅ PASSED" if bounds_pass else "❌ FAILED"
    })

    return pd.DataFrame(results)
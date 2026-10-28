import pandas as pd
import io

REQUIRED_COLUMNS = {
    'timestamp': '2026-10-20 12:00:00',
    'source_ip': '0.0.0.0',
    'destination_ip': '10.0.0.5',
    'request_method': 'GET',
    'endpoint': '/',
    'status_code': 200,
    'response_time': 50,
    'user_agent': 'Unknown',
    'username': '-',
    'request_count': 1,
    'bytes_sent': 0
}

def parse_uploaded_file(uploaded_file):
    """
    Universal log parser supporting CSV, JSON (Standard & JSON-Lines), and XLSX.
    Normalizes column names and guarantees required columns exist.
    """
    filename = uploaded_file.name.lower()
    
    try:
        # 1. Parse based on file extension
        if filename.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
            
        elif filename.endswith('.json'):
            # Try standard JSON array first; fallback to JSON Lines (NDJSON)
            content = uploaded_file.read()
            try:
                df = pd.read_json(io.BytesIO(content))
            except ValueError:
                df = pd.read_json(io.BytesIO(content), lines=True)
                
        elif filename.endswith('.xlsx') or filename.endswith('.xls'):
            df = pd.read_excel(uploaded_file, engine='openpyxl')
            
        else:
            raise ValueError(f"Unsupported file format: {filename}. Please upload CSV, JSON, or XLSX.")
            
    except Exception as e:
        raise ValueError(f"Failed to read {uploaded_file.name}: {str(e)}")

    if df.empty:
        raise ValueError("The uploaded file contains no log records (0 rows).")

    # 2. Standardize column names (lowercase and remove extra spaces)
    df.columns = [str(col).strip().lower() for col in df.columns]

    # 3. Ensure all required columns exist (fill missing ones with safe defaults)
    for col, default_val in REQUIRED_COLUMNS.items():
        if col not in df.columns:
            df[col] = default_val

    # 4. Ensure numeric columns are properly typed
    numeric_cols = ['status_code', 'response_time', 'request_count', 'bytes_sent']
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(REQUIRED_COLUMNS[col]).astype(int)

    return df
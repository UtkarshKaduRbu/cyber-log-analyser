import pandas as pd
import re

def extract_features(df):
    """
    Extracts numerical and categorical features from the cleaned logs 
    to help the detection algorithms identify attacks.
    """
    df_features = df.copy()
    
    # 1. SQL Injection Signatures
    # We look for common SQLi patterns in the endpoint URL
    sql_pattern = re.compile(r"(UNION|SELECT|DROP|OR 1=1|--|')", re.IGNORECASE)
    
    df_features['sqli_signature'] = df_features['endpoint'].apply(
        lambda x: 1 if pd.notnull(x) and sql_pattern.search(str(x)) else 0
    )
    
    # 2. IP-based Frequency Features (helps detect DDoS and Brute Force)
    # Calculate total requests per IP
    ip_counts = df_features['source_ip'].value_counts().to_dict()
    df_features['ip_request_count'] = df_features['source_ip'].map(ip_counts)
    
    # Calculate failed logins per IP (Status 401 on /login)
    failed_logins = df_features[(df_features['endpoint'] == '/login') & (df_features['status_code'] == 401)]
    failed_counts = failed_logins['source_ip'].value_counts().to_dict()
    
    # Map back to the dataframe (fill with 0 if the IP has no failed logins)
    df_features['ip_failed_login_count'] = df_features['source_ip'].map(failed_counts).fillna(0).astype(int)
    
    # 3. Time-based feature (extract hour of day, can be useful for anomalies)
    df_features['hour_of_day'] = df_features['timestamp'].dt.hour
    
    return df_features
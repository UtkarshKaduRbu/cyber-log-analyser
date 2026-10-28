import pandas as pd
import numpy as np

def calculate_risk(row):
    """
    Calculates a synthetic risk score (0-100) based on the attack type 
    and the machine learning anomaly score.
    """
    base_score = 0
    
    # 1. Assign base score depending on the threat type
    if row['prediction'] == 'Normal':
        base_score = 5
    elif row['prediction'] == 'Brute Force':
        base_score = 65
    elif row['prediction'] == 'SQL Injection':
        base_score = 80
    elif row['prediction'] == 'DDoS':
        base_score = 75
    elif row['prediction'] == 'Anomalous Traffic':
        base_score = 40
        
    # 2. Factor in the Machine Learning Anomaly Score (0.0 to 1.0)
    # We add up to 20 extra points based on how statistically weird the event is
    ml_factor = int(row['anomaly_score'] * 20)
    
    # 3. Calculate final score and cap it at 100
    total_score = base_score + ml_factor
    total_score = min(total_score, 100)
    
    # 4. Determine Severity Label
    if total_score <= 30:
        severity = 'Low'
    elif total_score <= 60:
        severity = 'Medium'
    elif total_score <= 80:
        severity = 'High'
    else:
        severity = 'Critical'
        
    return pd.Series([total_score, severity])

def apply_risk_scoring(df):
    """
    Applies the risk scoring logic to the entire dataframe.
    """
    df_scored = df.copy()
    
    # Apply the calculation row by row
    df_scored[['risk_score', 'severity']] = df_scored.apply(calculate_risk, axis=1)
    
    return df_scored
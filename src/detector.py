import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest

class LogDetector:
    def __init__(self):
        self.iso_forest = IsolationForest(n_estimators=100, contamination=0.1, random_state=42)
        
    def detect(self, df):
        """
        Takes the dataframe with extracted features and applies ML + Rules 
        to detect and classify attacks.
        """
        df_results = df.copy()
        
        df_results['prediction'] = 'Normal'
        df_results['anomaly_score'] = 0.0 
        
        # --- 1. Machine Learning Anomaly Detection ---
        ml_features = ['ip_request_count', 'bytes_sent', 'response_time']
        df_ml = df_results[ml_features].fillna(0)
        
        preds = self.iso_forest.fit_predict(df_ml)
        raw_scores = self.iso_forest.score_samples(df_ml)
        
        min_score, max_score = raw_scores.min(), raw_scores.max()
        if max_score > min_score:
            normalized_scores = 1 - ((raw_scores - min_score) / (max_score - min_score))
            df_results['anomaly_score'] = np.round(normalized_scores, 2)
        
        df_results['is_anomaly'] = preds == -1
        
        # --- 2. Hybrid Classification Logic ---
        for index, row in df_results.iterrows():
            
            # Rule 1: SQL Injection (Regex signature match)
            if row['sqli_signature'] == 1:
                df_results.at[index, 'prediction'] = 'SQL Injection'
                
            # Rule 2: Brute Force (High failed login count from single IP)
            elif row['ip_failed_login_count'] > 10:
                df_results.at[index, 'prediction'] = 'Brute Force'
                
            # Rule 3: DDoS (High request volume combined with ML anomaly or service degradation)
            elif row['ip_request_count'] > 50 and (row['is_anomaly'] or row['status_code'] == 503 or row['response_time'] > 1000):
                df_results.at[index, 'prediction'] = 'DDoS'
                
            # Rule 4: Catch-all ML Statistical Anomaly
            elif row['is_anomaly'] and df_results.at[index, 'prediction'] == 'Normal':
                df_results.at[index, 'prediction'] = 'Anomalous Traffic'

        return df_results
import pandas as pd

def clean_data(df):
    """
    Cleans the raw log dataframe by formatting dates and handling missing values.
    """
    # Create a copy to avoid modifying the original data prematurely
    df_clean = df.copy()
    
    # 1. Convert timestamp to datetime objects for time-based analysis
    df_clean['timestamp'] = pd.to_datetime(df_clean['timestamp'], errors='coerce')
    
    # 2. Fill missing categorical values with defaults
    if 'user_agent' in df_clean.columns:
        df_clean['user_agent'] = df_clean['user_agent'].fillna('Unknown')
    
    if 'username' in df_clean.columns:
        df_clean['username'] = df_clean['username'].fillna('-')
        
    # 3. Drop rows where timestamp is completely broken/missing
    df_clean = df_clean.dropna(subset=['timestamp'])
    
    # Sort chronologically just in case
    df_clean = df_clean.sort_values('timestamp').reset_index(drop=True)
    
    return df_clean
import pandas as pd

def generate_explanation(row):
    """
    Generates a structured, enterprise-grade threat dossier including 
    MITRE ATT&CK mappings, evidence, and remediation playbooks.
    """
    prediction = row.get('prediction', 'Normal')
    
    if prediction == 'Normal':
        return {
            "summary": "Traffic patterns are consistent with established baseline parameters.",
            "mitre": "N/A",
            "evidence": ["No malicious signatures detected."],
            "playbook": ["No action required."]
        }
    
    elif prediction == 'Brute Force':
        return {
            "summary": "Anomalous concentration of authentication failures originating from a singular network node. Characteristic of credential stuffing or password-guessing.",
            "mitre": "TA0006 Credential Access | T1110 Brute Force",
            "evidence": [
                f"Authentication Failure Velocity: {row['ip_failed_login_count']} failed HTTP 401 events.",
                "Target Specificity: Traffic strictly isolated to the `/login` endpoint."
            ],
            "playbook": [
                "1. Isolate and block the source IP at the Edge Firewall/WAF.",
                "2. Query logs for any SUCCESSFUL logins (HTTP 200) from this IP in the last 24 hours.",
                "3. Force password resets for any accounts compromised by this IP."
            ]
        }
        
    elif prediction == 'SQL Injection':
        return {
            "summary": "Malicious syntax identified within HTTP request parameters. Structural anomalies strongly correlate with SQL Injection (SQLi) attempts to exfiltrate database records.",
            "mitre": "TA0001 Initial Access | T1190 Exploit Public-Facing App",
            "evidence": [
                "Payload Signature Analysis: Known SQL injection keywords detected in URI.",
                f"Response Latency: {row['response_time']}ms (Deviation from expected query execution thresholds)."
            ],
            "playbook": [
                "1. Verify WAF rules are actively blocking SQLi payloads.",
                "2. Review backend database logs to ensure the payload was not executed.",
                "3. Audit the targeted endpoint for proper input sanitization and parameterized queries."
            ]
        }
        
    elif prediction == 'DDoS':
        return {
            "summary": "Extreme volumetric spike in inbound requests breaching statistical thresholds. Indicative of a Denial of Service (DoS/DDoS) flood intended to degrade service.",
            "mitre": "TA0040 Impact | T1498 Network Denial of Service",
            "evidence": [
                f"Request Frequency: {row['ip_request_count']} requests observed (Severe statistical deviation).",
                "Service Degradation: High frequency of HTTP 503 (Service Unavailable) responses.",
                "Payload Characteristics: 0 Byte payload size (Consistent with SYN/volumetric probing)."
            ],
            "playbook": [
                "1. Enable aggressive rate-limiting for the affected subnet.",
                "2. Route traffic through DDoS mitigation scrubbing centers (e.g., Cloudflare/AWS Shield).",
                "3. Monitor upstream bandwidth utilization to prevent complete circuit saturation."
            ]
        }
        
    else:
        return {
            "summary": "Machine learning anomaly detection flagged a severe statistical outlier compared to baseline traffic. Behavioral deviation warrants manual analyst review.",
            "mitre": "TA0043 Reconnaissance | T1595 Active Scanning",
            "evidence": [
                f"Isolation Forest Confidence Score: {row['anomaly_score']}/1.0",
                f"Volumetric Deviation: {row['bytes_sent']} Bytes transferred (Anomalous deviation)."
            ],
            "playbook": [
                "1. Manually inspect the raw JSON payload for novel attack signatures.",
                "2. Correlate IP reputation against external threat intelligence feeds.",
                "3. Adjust ML baselines if this is determined to be a benign administrative action."
            ]
        }

def apply_explanations(df):
    df_explained = df.copy()
    df_explained['explanation'] = df_explained.apply(generate_explanation, axis=1)
    return df_explained
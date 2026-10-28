"""Pulls logs from an isolated website's log agent by URL (no shared files)."""
import json
import urllib.error
import urllib.request

import pandas as pd

TIMEOUT = 8


class RemoteLogError(Exception):
    pass


def normalise_url(url):
    url = (url or "").strip().rstrip("/")
    if not url:
        raise RemoteLogError("Please enter the website's log URL.")
    if not url.startswith(("http://", "https://")):
        url = "http://" + url
    return url


def _get(url, token):
    req = urllib.request.Request(url)
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        if e.code == 401:
            raise RemoteLogError("Access token rejected by the website (HTTP 401).")
        raise RemoteLogError(f"Website returned HTTP {e.code}.")
    except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
        raise RemoteLogError(f"Cannot reach {url}: {getattr(e, 'reason', e)}")
    except json.JSONDecodeError:
        raise RemoteLogError("The URL did not return log-agent JSON.")


def check_connection(base_url, token=""):
    """Returns the agent's /health payload or raises RemoteLogError."""
    return _get(normalise_url(base_url) + "/health", token)


def fetch_new_logs(base_url, token="", since=0):
    """Returns (DataFrame of new rows, next_offset). Only rows after `since` are downloaded."""
    data = _get(f"{normalise_url(base_url)}/logs?since={int(since)}", token)
    df = pd.DataFrame(data.get("logs", []))
    for col in ("status_code", "response_time", "request_count", "bytes_sent"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)
    return df, int(data.get("next_offset", since)), int(data.get("total", 0))

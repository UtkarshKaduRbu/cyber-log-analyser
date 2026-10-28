"""
Log Agent - runs NEXT TO the isolated website and exposes its access log over HTTP.

The analyser never touches the website's files. It only talks to this agent:

    GET /health                      -> {"status": "ok", ...}
    GET /logs?since=<n>&limit=<m>    -> {"logs": [...], "next_offset": <n>, "total": <t>}

`since` is a row offset, so the analyser only downloads rows it has not seen yet.
If --token is set, every request must send:  Authorization: Bearer <token>

Usage (standalone, any machine that can see the log file):
    python log_agent.py --file data/live_logs.csv --port 8600 --token mysecret

It uses only the Python standard library.
"""
import argparse
import csv
import hmac
import json
import os
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

DEFAULT_PORT = 8600
MAX_LIMIT = 5000


def read_rows(path, since=0, limit=MAX_LIMIT):
    """Returns (rows, next_offset, total) for data rows after `since`."""
    if not os.path.exists(path):
        return [], 0, 0
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    total = len(rows)
    since = max(0, min(since, total))  # if the log was reset/rotated, restart safely
    chunk = rows[since:since + limit]
    return chunk, since + len(chunk), total


def make_handler(log_path, token):
    class Handler(BaseHTTPRequestHandler):
        def _send(self, code, payload):
            body = json.dumps(payload).encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def _authorised(self):
            if not token:
                return True
            supplied = self.headers.get("Authorization", "")
            return hmac.compare_digest(supplied, f"Bearer {token}")

        def do_GET(self):
            parsed = urlparse(self.path)
            if not self._authorised():
                return self._send(401, {"error": "invalid or missing access token"})

            if parsed.path == "/health":
                _, _, total = read_rows(log_path, 0, 0)
                return self._send(200, {"status": "ok", "total": total, "auth": bool(token)})

            if parsed.path == "/logs":
                qs = parse_qs(parsed.query)
                try:
                    since = int(qs.get("since", ["0"])[0])
                    limit = min(int(qs.get("limit", [str(MAX_LIMIT)])[0]), MAX_LIMIT)
                except ValueError:
                    return self._send(400, {"error": "since and limit must be integers"})
                rows, nxt, total = read_rows(log_path, since, limit)
                return self._send(200, {"logs": rows, "next_offset": nxt, "total": total})

            self._send(404, {"error": "not found"})

        def log_message(self, *args):  # keep the console quiet
            pass

    return Handler


def start_in_background(log_path, port=DEFAULT_PORT, token="", host="127.0.0.1"):
    """Starts the agent in a daemon thread. Returns the server (or None if the port is taken)."""
    try:
        server = ThreadingHTTPServer((host, port), make_handler(log_path, token))
    except OSError:
        return None
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Serve a website's access log to the SOC analyser")
    ap.add_argument("--file", default=os.path.join("data", "live_logs.csv"))
    ap.add_argument("--port", type=int, default=DEFAULT_PORT)
    ap.add_argument("--host", default="127.0.0.1", help="use 0.0.0.0 to accept remote analysers")
    ap.add_argument("--token", default="", help="shared secret the analyser must send")
    args = ap.parse_args()

    srv = ThreadingHTTPServer((args.host, args.port), make_handler(args.file, args.token))
    print(f"Log agent serving {args.file} on http://{args.host}:{args.port}  (auth: {'on' if args.token else 'OFF'})")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass

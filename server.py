#!/usr/bin/env python3
"""
Injection HTTP server that reads template filename from an environment variable.

Usage:
  export GOOGLE_CLIENT_ID="12345-...apps.googleusercontent.com"
  export HTML_TEMPLATE="gdmp_gcp_patched.html"   # optional (defaults to gdmp_gcp_patched.html)
  export PORT=8080                                # optional (defaults to 8080)
  python server_inject.py
"""

import os
import sys
from pathlib import Path
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import urllib.parse
import html as htmllib

# Optional: load .env if python-dotenv is installed
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

# ===== Configuration via environment =====
CLIENT_ENV_VAR = "GOOGLE_CLIENT_ID"           # must contain a *.apps.googleusercontent.com id
DEFAULT_TEMPLATE = "gdmp.html"    # fallback if HTML_TEMPLATE not set
TOKEN = "%%INJECTION_TARGET%%"                # exact token to replace in HTML
DEFAULT_PORT = int(os.getenv("PORT", 8080))

# Read template name from env variable, but accept only a basename to avoid path traversal
_template_env = os.getenv("HTML_TEMPLATE", DEFAULT_TEMPLATE).strip()
HTML_NAME = Path(_template_env).name  # take basename only
BASE_DIR = Path(__file__).resolve().parent

def _get_client_id():
    cid = (os.getenv(CLIENT_ENV_VAR) or "").strip()
    if not cid:
        raise RuntimeError(f"{CLIENT_ENV_VAR} not set in environment.")
    if not cid.endswith(".apps.googleusercontent.com"):
        raise RuntimeError(f"{CLIENT_ENV_VAR} value doesn't look like a web OAuth client id.")
    return cid

def preprocess_html(filename: str) -> bytes:
    path = (BASE_DIR / filename).resolve()
    if not path.exists():
        raise FileNotFoundError(f"Template not found: {path}")
    raw = path.read_text(encoding="utf-8")
    client_id = _get_client_id()
    if TOKEN not in raw:
        raise RuntimeError(f"Placeholder token {TOKEN!r} not found in {filename}.")
    out = raw.replace(TOKEN, client_id)
    if TOKEN in out:
        raise RuntimeError("Injection failed: placeholder still present after replacement.")
    return out.encode("utf-8")

class InjectingHandler(SimpleHTTPRequestHandler):
    def _respond_with_html_bytes(self, body: bytes, code: int = 200):
        self.send_response(code)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        self.send_header("Pragma", "no-cache")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _respond_with_error_page(self, exc: Exception):
        body_text = (
            "<html><head><meta charset='utf-8'><title>Server Error</title></head>"
            "<body style='font-family:system-ui, -apple-system, Roboto, Arial; padding:24px;'>"
            "<h1>HTML preprocessing error</h1>"
            "<pre style='white-space:pre-wrap; background:#f8f8f8; padding:12px; border:1px solid #ddd;'>"
            f"{htmllib.escape(str(exc))}"
            "</pre>"
            "<p>Check server logs or environment variables (see server console output).</p>"
            "</body></html>"
        ).encode("utf-8")
        self._respond_with_html_bytes(body_text, code=500)

    def do_GET(self):
        clean_path = urllib.parse.urlsplit(self.path).path
        # Accept root, /gdmp, or the configured filename
        intercept_paths = ("/", "/gdmp", f"/{HTML_NAME}", f"/{HTML_NAME}/")
        if clean_path in intercept_paths:
            try:
                body = preprocess_html(HTML_NAME)
                return self._respond_with_html_bytes(body, code=200)
            except Exception as e:
                print("[ERROR] HTML preprocessing failed:", file=sys.stderr)
                import traceback
                traceback.print_exc()
                return self._respond_with_error_page(e)

        # Otherwise serve static files from BASE_DIR
        cwd_save = os.getcwd()
        try:
            os.chdir(str(BASE_DIR))
            return super().do_GET()
        finally:
            os.chdir(cwd_save)

def run(port: int):
    addr = ("0.0.0.0", port)
    print(f"Starting injecting server on http://127.0.0.1:{port}/ (serving from {BASE_DIR})")
    print(f"Template: {HTML_NAME} (token: {TOKEN}) -- requests to / or /{HTML_NAME} will be injected.")
    httpd = ThreadingHTTPServer(addr, InjectingHandler)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.")
    finally:
        httpd.server_close()

if __name__ == "__main__":
    port = int(os.getenv("PORT", DEFAULT_PORT))
    print(f"PORT={port}; {CLIENT_ENV_VAR}={'set' if os.getenv(CLIENT_ENV_VAR) else 'NOT SET'}; HTML_TEMPLATE={HTML_NAME}")
    run(port)

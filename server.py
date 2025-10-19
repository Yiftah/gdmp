import os
import http.server
import socketserver
from urllib.parse import urlparse
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- CONFIGURATION ---
HTML_FILE = 'gdmp.html'
# The literal string used in the HTML file for replacement.
# This must match the GOOGLE_CLIENT_ID constant in gdmp.html exactly.
INJECTION_TARGET = '%%INJECTION_TARGET%%'

# Get the port from the environment variable 'PORT' (for Render) 
# and fallback to 8000 for local development.
PORT = int(os.getenv('PORT', 8000))
# Get the Client ID from the .env file
client_id = os.getenv('GOOGLE_CLIENT_ID')

if not client_id:
    print("FATAL ERROR: GOOGLE_CLIENT_ID not found in .env file.")
    print("Please create a .env file and set GOOGLE_CLIENT_ID.")
    exit(1)

def preprocess_html(filename):
    """
    Reads the HTML file, performs the client ID injection, and returns the modified content.
    """
    try:
        with open(filename, 'r') as f:
            content = f.read()
        
        # Replace the placeholder in the HTML with the real Client ID
        modified_content = content.replace(INJECTION_TARGET, client_id)
        return modified_content
    except FileNotFoundError:
        return None

class Handler(http.server.SimpleHTTPRequestHandler):
    """
    Custom handler to intercept requests for the HTML file and inject the Client ID.
    """
    def do_GET(self):
        url = urlparse(self.path)
        
        # Serve the index file for both the root path and the explicit file path
        if url.path == '/' or url.path.endswith(HTML_FILE):
            
            # --- 1. Preprocess and Inject Client ID ---
            modified_content = preprocess_html(HTML_FILE)

            if modified_content is None:
                self.send_error(404, "File not found")
                return

            # --- 2. Send Headers ---
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.send_header("Content-length", str(len(modified_content)))
            self.end_headers()
            
            # --- 3. Send Content ---
            self.wfile.write(modified_content.encode('utf-8'))
        else:
            # Fallback to default SimpleHTTPRequestHandler for other assets (like favicon)
            super().do_GET()

# --- SERVER EXECUTION ---

# Ensure the server binds to all network interfaces (0.0.0.0) for deployment, 
# but uses localhost locally.
HOST = '0.0.0.0' if os.getenv('PORT') else '127.0.0.1'

try:
    with socketserver.TCPServer((HOST, PORT), Handler) as httpd:
        print(f"--- Server running on http://{HOST}:{PORT}/ ---")
        print(f"Access application at: http://127.0.0.1:{PORT}/{HTML_FILE}")
        httpd.serve_forever()
except OSError as e:
    if e.errno == 98: # Address already in use
        print(f"ERROR: Port {PORT} is already in use. Please stop the other application or choose a different port.")
    else:
        raise
        
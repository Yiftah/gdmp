import os
from http.server import SimpleHTTPRequestHandler, HTTPServer
from dotenv import load_dotenv

# --- CONFIGURATION ---
# Load environment variables from .env file
load_dotenv()

# The environment variable key holding your secret Client ID
ENV_VAR_NAME = 'GOOGLE_CLIENT_ID'
# File name of your HTML client
HTML_FILE = 'gdmp.html'
# The literal string placeholder used in the HTML file
PLACEHOLDER = '%%INJECTION_TARGET%%'
PORT = 8000

# --- PREPROCESSING LOGIC ---

def preprocess_html(file_path):
    """
    Reads the HTML content, injects the Google Client ID, and returns the modified content.
    """
    client_id = os.getenv(ENV_VAR_NAME)
    
    if not client_id:
        print(f"\nFATAL ERROR: Environment variable '{ENV_VAR_NAME}' not found in .env file.")
        print("Please ensure your .env file exists and contains GOOGLE_CLIENT_ID=\"YOUR_ID\"")
        # Return a non-functional content to ensure the browser doesn't load sensitive info
        return f"<html><body><h1>SETUP ERROR: Missing {ENV_VAR_NAME} environment variable.</h1></body></html>"

    try:
        with open(file_path, 'r') as f:
            content = f.read()
    except FileNotFoundError:
        return f"<html><body><h1>Error 404: {file_path} not found in the current directory.</h1></body></html>"
    
    # Securely replace the placeholder with the actual client ID
    modified_content = content.replace(PLACEHOLDER, client_id)
    
    # We expect the content to change. If it didn't, it means the placeholder was wrong.
    if modified_content == content:
        print(f"\nWARNING: Placeholder '{PLACEHOLDER}' was NOT replaced.")
        print("Ensure the string in serve.py EXACTLY matches the string in gdmp.html.")
    
    return modified_content

# --- CUSTOM HTTP HANDLER ---

class CustomHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        # We only care about requests for the HTML file or the root directory.
        if self.path.endswith(HTML_FILE) or self.path == '/':
            # If the root is requested, implicitly serve the HTML file
            if self.path == '/':
                serve_file = HTML_FILE
            else:
                serve_file = self.path[1:] # Remove leading slash
            
            # 1. Preprocess the HTML content
            modified_content = preprocess_html(serve_file)
            
            # 2. Convert content to bytes and send header
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            # 3. Send the modified content to the browser
            self.wfile.write(modified_content.encode('utf-8'))
        else:
            # For all other requests (like favicon, JS libraries, etc.), use default handler
            super().do_GET()

# --- SERVER STARTUP ---

if __name__ == '__main__':
    # Ensure the HTML file exists before starting
    if not os.path.exists(HTML_FILE):
         print(f"Error: {HTML_FILE} not found. Please ensure it is in the same directory.")
    else:
        server_address = ('', PORT)
        httpd = HTTPServer(server_address, CustomHandler)
        print(f"Starting server at http://localhost:{PORT}")
        print(f"Access your app at: http://localhost:{PORT}/{HTML_FILE}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.")
            httpd.server_close()

import json
import os
from http.server import BaseHTTPRequestHandler
import requests

# Load OpenAI API Key from environment variables
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            if not OPENAI_API_KEY:
                raise ValueError("OPENAI_API_KEY is not set in environment variables.")

            # Parse incoming request
            content_length = int(self.headers['Content-Length'])
            body = self.rfile.read(content_length)
            data = json.loads(body)

            # Forward request to OpenAI
            response = requests.post(
                "https://api.openai.com/v1/engines/davinci/completions",
                headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
                json=data
            )

            # Check if the OpenAI API call was successful
            if response.status_code != 200:
                raise Exception(f"OpenAI API error: {response.status_code} - {response.text}")

            # Respond back to client
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(response.content)

        except Exception as e:
            # Handle errors and send a response
            self.send_response(500)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            error_response = {"error": str(e)}
            self.wfile.write(json.dumps(error_response).encode("utf-8"))

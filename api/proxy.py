import json
import os
from http.server import BaseHTTPRequestHandler
import requests

OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        # Parse incoming request
        content_length = int(self.headers['Content-Length'])
        body = self.rfile.read(content_length)
        data = json.loads(body)
        print(f"Data is {body}")

        # Forward request to OpenAI
        response = requests.post(
            "https://api.openai.com/v1/engines/davinci/completions",
            headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
            json=data
        )

        # Respond back to client
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(response.content)

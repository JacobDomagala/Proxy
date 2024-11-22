from http.server import BaseHTTPRequestHandler
import json

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            # Read the content length and body of the request
            content_length = int(self.headers['Content-Length'])
            body = self.rfile.read(content_length)

            # Parse JSON data
            data = json.loads(body)

            # Prepare a response
            response = {
                "message": "Received data successfully",
                "data": data
            }

            # Send a successful response
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(response).encode("utf-8"))

        except Exception as e:
            # Handle any error and send a 500 response
            self.send_response(500)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            error_response = {"error": str(e)}
            self.wfile.write(json.dumps(error_response).encode("utf-8"))

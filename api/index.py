import json
import os
from flask import Flask, request, jsonify
import firebase_admin
from firebase_admin import credentials, firestore, auth
import requests
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from functools import wraps

app = Flask(__name__)

# Get Redis URL from environment variable
redis_password = os.getenv('UPSTASH_REDIS_PASSWORD')
redis_host = os.getenv('UPSTASH_REDIS_HOST')
redis_port = int(os.getenv('UPSTASH_REDIS_PORT', 6379))
redis_url = f"rediss://:{redis_password}@{redis_host}:{redis_port}"

# Configure Rate Limiting with Redis backend
limiter = Limiter(
    app=app,
    key_func=lambda: request.headers.get('x-api-key') or get_remote_address(),
    default_limits=["200 per day", "50 per hour"],
    storage_uri=redis_url  # Use the Redis URI from Upstash
)

# Initialize Firebase Admin SDK
if not firebase_admin._apps:
    service_account_info = json.loads(os.environ.get('FIREBASE_SERVICE_ACCOUNT'))
    cred = credentials.Certificate(service_account_info)
    firebase_admin.initialize_app(cred)
firestore_db = firestore.client()

# Authentication Decorator for Firebase ID Token
def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({"error": "Authorization header missing."}), 401

        try:
            # Expected format: "Bearer <ID_TOKEN>"
            id_token = auth_header.split(" ").pop()
            decoded_token = auth.verify_id_token(id_token)
            request.user = decoded_token
        except Exception:
            return jsonify({"error": "Invalid or expired token."}), 401

        return f(*args, **kwargs)
    return decorated

# Rate Limiting Error Handler
@app.errorhandler(429)
def ratelimit_handler(e):
    return jsonify(error="Rate limit exceeded. Please try again later."), 429

def validate():
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        req_type = data.get('type')
        message = data.get('message')

        print(f"Validate got the data={data}")
        if not user_id or not message or not req_type:
            return False, jsonify({"error": "Missing 'user_id', 'message' or 'type' in request."}), 400

        # Ensure the user_id matches the token uid
        token_uid = request.user['uid']
        if user_id != token_uid:
            return False, jsonify({"error": "Unauthorized access."}), 403

        # Validate user in Firestore
        user_ref = firestore_db.collection('users').document(user_id)
        doc = user_ref.get()

        if doc.exists:
            return True, None, 200
        else:
            return False, jsonify({"error": "Invalid user."}), 401
    except Exception as e:
        print(f"Error processing request: {e}")
        return False, jsonify({"error": "Internal server error."}), 500


@app.route('/api', methods=['POST'])
@require_auth
@limiter.limit("100 per day; 20 per hour")  # Adjust limits as desired
def validate_user():
    result, json_response, code = validate()
    if result:
        data = request.get_json()
        # Forward request to OpenAI or process as needed
        # For example:
        # response = requests.post(
        #     "https://api.openai.com/v1/completions",
        #     headers={"Authorization": f"Bearer {os.environ.get('OPENAI_API_KEY')}"},
        #     json={"prompt": data.get('message')}
        # )
        # openai_resp = response.json()
        return jsonify({"data": f"Response from OpenAI for request type: {data.get('type')} with data: {data.get('message')}"}), code
    else:
        return json_response, code

@app.route('/create_assistant', methods=['POST'])
@require_auth
def create_assistant():
    result, json_response, code = validate()
    if result:
        # Create assistant logic here
        # my_assistant = ...
        print("Creating assistant!")
        return jsonify({"data": "create_assistant"}), code
    else:
        return json_response, code

if __name__ == "__main__":
    app.run(debug=True)
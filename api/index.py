import json
import os
from flask import Flask, request, jsonify
import firebase_admin
from firebase_admin import credentials, firestore, auth
import requests
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from functools import wraps
from openai import OpenAI
    
app = Flask(__name__)
client = OpenAI()

# Configure Rate Limiting
limiter = Limiter(
    app=app,
    key_func=lambda: request.headers.get('x-api-key') or get_remote_address(),
    default_limits=["200 per day", "50 per hour"]
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
            uid = decoded_token['uid']
            request.user = decoded_token
        except Exception as e:
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
        message = data.get('message')

        if not user_id or not message:
            return False, jsonify({"error": "Missing 'user_id' or 'message' in request."}), 400

        # Ensure the user_id from token matches the user_id in the request
        token_uid = request.user['uid']
        if user_id != token_uid:
            return False, jsonify({"error": "Unauthorized access."}), 403

        # Validate user against Firestore
        user_ref = firestore_db.collection('users').document(user_id)
        doc = user_ref.get()

        if doc.exists:
            return True, None
        else:
            return False, jsonify({"error": "Invalid user."}), 401
    except Exception as e:
        print(f"Error processing request: {e}")
        return False, jsonify({"error": "Internal server error."}), 500


@app.route('/api', methods=['POST'])
@require_auth
@limiter.limit("100 per day; 20 per hour")  # Customize as needed
def validate_user():
    result, json = validate()
    if result == True:
        response = requests.post(
            "https://api.openai.com/v1/engines/davinci/completions",
            headers={"Authorization": f"Bearer {os.environ.get('OPENAI_API_KEY')}"},
            json=data
        )
        return jsonify(response.json()), 200
                
    else:
        return json
    
@app.route('/create_assistant', methods=['POST'])
@require_auth
def create_assistant():
    my_assistant = client.beta.assistants.create(
        instructions="You are a personal math tutor. When asked a question, write and run Python code to answer the question.",
        name="Math Tutor",
        tools=[{"type": "code_interpreter"}],
        model="gpt-4o-mini",
    )
    print(my_assistant)

def create_thread(assistantId):
    empty_thread = client.beta.threads.create()
    print(empty_thread)

if __name__ == "__main__":
    app.run(debug=True)
import json
import os
from flask import Flask, request, jsonify
import requests
import firebase_admin
from firebase_admin import credentials, firestore

app = Flask(__name__)

# Load OpenAI API Key from environment variables
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

# Initialize Firebase Admin SDK
def initialize_firebase():
    if not firebase_admin._apps:
        try:
            service_account_info = json.loads(os.environ.get('FIREBASE_API'))
            cred = credentials.Certificate(service_account_info)
            firebase_admin.initialize_app(cred)
            print("Firebase initialized successfully.")
        except Exception as e:
            print(f"Failed to initialize Firebase: {e}")

# Call the initialization function
initialize_firebase()

# Initialize Firestore DB
db = firestore.client()

@app.route('/api', methods=['POST'])
def validate_user():
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        message = data.get('message')

        if not user_id or not message:
            return jsonify({"error": "Missing 'user_id' or 'message' in request."}), 400

        # Validate user against Firestore
        user_ref = db.collection('users').document(user_id)
        doc = user_ref.get()

        if doc.exists:
            print(f"User {user_id} is valid.")
            # Forward request to OpenAI
            response = requests.post(
                "https://api.openai.com/v1/engines/davinci/completions",
                headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
                json=data
            )
            return jsonify(response.json()), 200
        else:
            print(f"User {user_id} is invalid.")
            return jsonify({"error": "Invalid user."}), 401

    except Exception as e:
        print(f"Error processing request: {e}")
        return jsonify({"error": "Internal server error."}), 500

if __name__ == "__main__":
    app.run(debug=True)
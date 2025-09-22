

from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import json
import subprocess
import time

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
MODEL_NAME = "gemma3:4b"

def is_ollama_running():
    """Check if Ollama is running on port 11434"""
    try:
        response = requests.get("http://127.0.0.1:11434/api/tags", timeout=5)
        return response.status_code == 200
    except:
        return False

def is_model_available():
    """Check if the required model is available"""
    try:
        response = requests.get("http://127.0.0.1:11434/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get("models", [])
            return any(model["name"] == MODEL_NAME for model in models)
        return False
    except:
        return False

def start_ollama():
    """Try to start Ollama if it's not running"""
    try:
        # Try to start Ollama (this works on most systems)
        subprocess.Popen(["ollama", "serve"])
        time.sleep(5)  # Wait for Ollama to start
        return True
    except:
        return False

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    user_message = data.get("message", "")
    if not user_message:
        return jsonify({"reply": "No message provided"}), 400

    # Check if Ollama is running
    if not is_ollama_running():
        if not start_ollama():
            return jsonify({"reply": "❌ Ollama is not running. Please start Ollama first."}), 500
        time.sleep(3)  # Give it more time to start

    # Check if model is available
    if not is_model_available():
        return jsonify({"reply": f"❌ Model '{MODEL_NAME}' not found. Please run: 'ollama pull {MODEL_NAME}'"}), 500

    payload = {
        "model": MODEL_NAME,
        "prompt": user_message,
        "stream": False
    }

    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=120)  # Increased timeout to 2 minutes
        response.raise_for_status()
        
        data = response.json()
        reply = data.get("response", "No response from model")
        
    except requests.exceptions.ConnectionError:
        reply = "❌ Cannot connect to Ollama. Please make sure Ollama is installed and running."
    except requests.exceptions.Timeout:
        reply = "❌ Ollama request timed out. The model might be loading or too slow. Try a simpler query."
    except requests.exceptions.RequestException as e:
        reply = f"❌ Error connecting to Ollama: {str(e)}"
    except json.JSONDecodeError:
        reply = "❌ Invalid response from Ollama. Please check if Ollama is functioning properly."
    except Exception as e:
        reply = f"❌ Unexpected error: {str(e)}"

    return jsonify({"reply": reply})

@app.route("/health", methods=["GET"])
def health_check():
    """Comprehensive health check"""
    ollama_status = is_ollama_running()
    model_status = is_model_available() if ollama_status else False
    
    return jsonify({
        "status": "healthy", 
        "service": "Flask Backend",
        "ollama_running": ollama_status,
        "model_available": model_status,
        "model_name": MODEL_NAME
    })

@app.route("/ollama-status", methods=["GET"])
def ollama_status():
    """Detailed Ollama status check"""
    ollama_running = is_ollama_running()
    model_available = is_model_available() if ollama_running else False
    
    return jsonify({
        "ollama_running": ollama_running,
        "model_available": model_available,
        "model_name": MODEL_NAME
    })

@app.route("/", methods=["GET"])
def index():
    return "DeepSeek-R1 Ollama API Flask Server is running!"

if __name__ == "__main__":
    print("🔍 Checking Ollama status...")
    if not is_ollama_running():
        print("⚠️  Ollama is not running. Attempting to start...")
        if start_ollama():
            print("✅ Ollama started successfully")
        else:
            print("❌ Failed to start Ollama. Please start it manually.")
    else:
        print("✅ Ollama is running")
    
    if is_model_available():
        print(f"✅ Model '{MODEL_NAME}' is available")
    else:
        print(f"❌ Model '{MODEL_NAME}' not found. Please run: 'ollama pull {MODEL_NAME}'")
    
    print("🚀 Starting Flask server...")
    app.run(host="0.0.0.0", port=5000, debug=True)
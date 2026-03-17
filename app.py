import os
import json
import base64
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS 
from groq import Groq
from PIL import Image
import logging
import tempfile

# Set up logging for the terminal output
logging.basicConfig(level=logging.INFO)

# --- Flask App Setup ---
from dotenv import load_dotenv
load_dotenv()
app = Flask(__name__)
# Enable CORS for all routes
CORS(app) 
app.config['UPLOAD_FOLDER'] = tempfile.gettempdir()
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# --- Groq AI Setup ---
GROQ_API_KEY = os.getenv("GROQ_API_KEY") 
client = Groq(api_key=GROQ_API_KEY) 

SYSTEM_PROMPT = """
You are a highly compassionate and professional AI health and wellness guide named 'AI Doctor'. 
Your primary function is to provide helpful, informative guidance and general knowledge related to health, 
symptoms, and wellness based on reliable, grounded information. 
You MUST include a prominent disclaimer in every single response stating: 
'I am an AI and cannot provide medical advice. Always consult a qualified healthcare professional for diagnosis and treatment.'
"""

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

# --- Routes ---

@app.route("/")
def home():
    logging.info("Serving frontend: test.html.")
    return render_template("test.html")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/terms")
def terms():
    return render_template("terms.html")

@app.route("/get-response", methods=["POST"])
def get_response():
    """Handles text chat using Groq."""
    try:
        data = request.get_json()
        user_message = data.get("message", "")
        history = data.get("history", []) 
        
        if not user_message.strip():
            return jsonify({"response": "Please say something."})

        # Reconstruct messages for Groq
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        
        for item in history:
            role = "assistant" if item['role'] == "model" else "user"
            messages.append({"role": role, "content": item['text']})
        
        # Add current message
        messages.append({"role": "user", "content": user_message})
        
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.7,
            max_tokens=1024,
            top_p=1,
            stream=False
        )
        
        return jsonify({
            "response": completion.choices[0].message.content,
            "sources": [] # Groq doesn't provide search grounding in the same way as Gemini yet
        })

    except Exception as e:
        logging.error(f"Chat Error: {e}")
        return jsonify({"response": f"Internal API Error: {str(e)}", "sources": []})

@app.route("/analyze-image", methods=["POST"])
def analyze_image():
    """Handles image uploads using Groq Vision."""
    if "image" not in request.files:
        return jsonify({"response": "No image provided."})

    image_file = request.files["image"]
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], image_file.filename)
    image_file.save(file_path)
    
    try:
        base64_image = encode_image(file_path)
        
        prompt = request.form.get("prompt", "Analyze this medical image, scan, or report. Provide a helpful, non-diagnostic explanation and a strict disclaimer about consulting a doctor.")
        
        completion = client.chat.completions.create(
            model="llama-3.2-11b-vision-preview",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": f"{SYSTEM_PROMPT}\n\n{prompt}"},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}",
                            },
                        },
                    ],
                }
            ],
            temperature=0.7,
            max_tokens=1024,
            top_p=1,
            stream=False
        )
        
        bot_reply = completion.choices[0].message.content
        
    except Exception as e:
        logging.error(f"Image Analysis Error: {e}")
        bot_reply = f"Error analyzing image: {str(e)}"
        
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)
            
    return jsonify({"response": bot_reply})

if __name__ == "__main__":
    app.run(debug=True, port=5000) 

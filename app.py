import os
import json
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS 
from google import genai 
from google.genai import types
from PIL import Image
import logging

# Set up logging for the terminal output
logging.basicConfig(level=logging.INFO)

# --- Flask App Setup ---
import tempfile
app = Flask(__name__)
# Enable CORS for all routes (necessary for frontend/backend communication)
CORS(app) 
app.config['UPLOAD_FOLDER'] = tempfile.gettempdir()
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# --- Generative AI Setup ---
# CRITICAL: Replace "YOUR_API_KEY" with your actual Gemini API Key. 
API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyA2xy0Y5STJtuYlG-xBbbVIediB1MafIvs") 

# FIX: Initialize the Client object directly, removing the faulty 'configure' call.
client = genai.Client(api_key=API_KEY) 

SYSTEM_PROMPT = """
You are a highly compassionate and professional AI health and wellness guide named 'AI Doctor'. 
Your primary function is to provide helpful, informative guidance and general knowledge related to health, 
symptoms, and wellness based on reliable, grounded information. 
You MUST include a prominent disclaimer in every single response stating: 
'I am an AI and cannot provide medical advice. Always consult a qualified healthcare professional for diagnosis and treatment.'
"""

# Tool configuration to enable Google Search grounding
search_tool = types.Tool(
    google_search={}
)

# --- Routes for Chat and Image Analysis ---

@app.route("/")
def home():
    # Log status to the console (where you run python app.py)
    logging.info("Serving frontend: test.html. Backend is running and ready for API calls.")
    # This renders the test.html file located in the 'templates' folder
    return render_template("test.html")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/terms")
def terms():
    return render_template("terms.html")

@app.route("/get-response", methods=["POST"])
def get_response():
    """Handles text chat and returns a grounded response."""
    try:
        data = request.get_json()
        user_message = data.get("message", "")
        # The frontend provides the full history for context
        chat_history_parts = data.get("history", []) 
        
        if not user_message.strip():
            return jsonify({"response": "Please say something."})

        # Reconstruct content list for the API call (including history and new message)
        contents = []
        for item in chat_history_parts:
            # Simple conversion of history to the format expected by generate_content
            contents.append(types.Content(role=item['role'], parts=[types.Part.from_text(item['text'])]))
        
        # Add the current user message
        contents.append(types.Content(role="user", parts=[types.Part.from_text(user_message)]))
        
        # Configuration for the model
        config = types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            tools=[search_tool]
        )

        # Use the client object for the API call
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=contents,
            config=config
        )
        
        # Process citations from grounding
        sources = []
        if response.candidates and response.candidates[0].grounding_metadata:
            for attribution in response.candidates[0].grounding_metadata.grounding_chunks:
                # The Python SDK provides source links directly in the chunks
                if attribution.web and attribution.web.uri:
                    sources.append({
                        "uri": attribution.web.uri,
                        "title": attribution.web.title or "Source Link"
                    })

        # Return the bot reply and the sources
        return jsonify({
            "response": response.text,
            "sources": sources
        })

    except Exception as e:
        # Log the error to the terminal
        logging.error(f"Chat Error: {e}")
        return jsonify({"response": f"Internal API Error: {str(e)}", "sources": []})

@app.route("/analyze-image", methods=["POST"])
def analyze_image():
    """Handles image file uploads and analysis."""
    if "image" not in request.files:
        return jsonify({"response": "No image provided."})

    image_file = request.files["image"]
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], image_file.filename)
    image_file.save(file_path)
    
    bot_reply = ""
    try:
        # Open the saved image using PIL
        img = Image.open(file_path)
        
        prompt = "Analyze this medical image, scan, or report. Provide a helpful, non-diagnostic explanation and a strict disclaimer about consulting a doctor."
        
        # Combine system prompt with image analysis
        full_prompt = SYSTEM_PROMPT + "\n\n" + prompt

        # Use the client object for the API call
        response = client.models.generate_content(
            model='gemini-2.5-flash', # Use the flash model for multimodal
            contents=[full_prompt, img]
        )
        bot_reply = response.text
        
    except Exception as e:
        # Log the error to the terminal
        logging.error(f"Image Analysis Error: {e}")
        bot_reply = f"Error analyzing image: {str(e)}"
        
    finally:
        # Clean up the saved file
        if os.path.exists(file_path):
            os.remove(file_path)
            
    return jsonify({"response": bot_reply})


if __name__ == "__main__":
    app.run(debug=True, port=5000) 

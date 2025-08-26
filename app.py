import os
import logging
from flask import Flask, render_template, request, jsonify
import google.generativeai as genai
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
from pathlib import Path


# --- App Initialization ---
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'

# --- Basic Logging Configuration ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Securely Load Environment Variables ---
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    # Use logger instead of print for production
    app.logger.critical("FATAL: GOOGLE_API_KEY not found. Please set it in your .env file.")
    # In a real production scenario, you might want the app to exit or handle this more gracefully.
    # For now, we'll raise an error to prevent it from starting without a key.
    raise ValueError("GOOGLE_API_KEY not found. Please set it in your .env file.")

# --- Configure and Initialize AI Model (ONCE) ---
try:
    genai.configure(api_key=api_key)
    # Initialize the models once on startup for better performance
    text_model = genai.GenerativeModel("models/gemini-1.5-flash")
    vision_model = genai.GenerativeModel("models/gemini-1.5-flash-latest")
    app.logger.info("Generative AI models initialized successfully.")
except Exception as e:
    app.logger.critical(f"Failed to configure or initialize Generative AI: {e}")
    text_model = None
    vision_model = None

# --- Route Definitions ---
@app.route("/")
def home():
    """Renders the main chat page."""
    # The HTML file should be inside a 'templates' folder
    return render_template("test.html")


@app.route("/get-response", methods=["POST"])
def get_response():
    """Handles text-based chat messages."""
    if not text_model:
        return jsonify({"error": "Text model is not available."}), 500

    user_message = request.json.get("message", "")

    if not user_message.strip():
        return jsonify({"response": "Please say something."})

    try:
        response = text_model.generate_content(user_message)
        # Using response.text is correct and concise
        return jsonify({"response": response.text})
    except Exception as e:
        app.logger.error(f"Error during text generation: {e}")
        return jsonify({"error": "Sorry, I encountered an error. Please try again."}), 500


@app.route("/analyze-image", methods=["POST"])
def analyze_image():
    """Handles image analysis requests."""
    if not vision_model:
        return jsonify({"error": "Vision model is not available."}), 500
        
    if "image" not in request.files:
        return jsonify({"error": "No image provided."}), 400

    image_file = request.files["image"]
    
    if image_file.filename == '':
        return jsonify({"error": "No selected file."}), 400

    # Sanitize the filename for security
    filename = secure_filename(image_file.filename)
    upload_folder = app.config['UPLOAD_FOLDER']
    os.makedirs(upload_folder, exist_ok=True) # Ensure the uploads directory exists
    file_path = os.path.join(upload_folder, filename)
    
    try:
        image_file.save(file_path)
        app.logger.info(f"Image saved temporarily to {file_path}")

        # The google-generativeai library can accept a file path directly, which is simpler
        # However, sending the bytes is also perfectly fine. Let's stick to your method.
        image_parts = [{
            "mime_type": image_file.mimetype,
            "data": Path(file_path).read_bytes()
        }]
        
        prompt = "Analyze this medical report or injury image and provide a helpful but non-diagnostic explanation. Disclaimer: you are an AI and not a medical professional."
        
        response = vision_model.generate_content([prompt, image_parts[0]])
        
        return jsonify({"response": response.text})
        
    except Exception as e:
        app.logger.error(f"Error during image analysis: {e}")
        return jsonify({"error": "Sorry, I couldn't analyze the image."}), 500
        
    finally:
        # IMPORTANT: Clean up the uploaded file to save space and for security
        if os.path.exists(file_path):
            os.remove(file_path)
            app.logger.info(f"Cleaned up temporary file: {file_path}")

# This block is for development only and should NOT be used in production.
# A WSGI server like Gunicorn will be the entry point.
if __name__ == "__main__":
    app.run(debug=True, port=8000)
    
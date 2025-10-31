"""
AI Image Generator API
----------------------
A Flask application that provides endpoints to generate and edit images using Google Vertex AI's Imagen models.

This module includes authentication, text-to-image generation, and image-editing endpoints.
"""

from flask import Flask, request, jsonify, render_template, render_template_string, redirect, url_for, session, flash, Response
from flask_cors import CORS
from dotenv import load_dotenv
import os
import time
import tempfile
import uuid
import base64
import requests
import vertexai
from vertexai.preview.vision_models import ImageGenerationModel
from google.auth.transport.requests import Request
from google.oauth2 import service_account
from datetime import timedelta
from functools import wraps
from typing import List, Dict, Any

# Initialize Flask app
app = Flask(__name__)
CORS(app)

app.secret_key = os.getenv("SECRET_KEY")

# Only load .env locally — not on Railway
if not os.getenv("RAILWAY_ENVIRONMENT"):
    from dotenv import load_dotenv
    load_dotenv()
    print("📦 Loaded local .env file")
else:
    print("🚀 Running on Railway — using environment variables")


# Handle Vertex AI credentials dynamically (for Railway/Render)
SERVICE_KEY_JSON = os.getenv("SERVICE_KEY_JSON")
if SERVICE_KEY_JSON:
    key_path = os.path.join(tempfile.gettempdir(), "vertex-key.json")
    with open(key_path, "w") as f:
        f.write(SERVICE_KEY_JSON)
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = key_path

# Get GCP configuration from environment
PROJECT_ID = os.getenv("PROJECT_ID")
LOCATION = os.getenv("LOCATION", "us-central1")
local_credentials = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
SCOPES = ["https://www.googleapis.com/auth/cloud-platform"]
credentials = service_account.Credentials.from_service_account_file(
    local_credentials, scopes=SCOPES
)
credentials.refresh(Request())
MODEL_ID = "imagen-3.0-capability-001"
ENDPOINT = f"https://{LOCATION}-aiplatform.googleapis.com/v1/projects/{PROJECT_ID}/locations/{LOCATION}/publishers/google/models/{MODEL_ID}:predict"
app.permanent_session_lifetime = timedelta(hours=1)

if not PROJECT_ID:
    raise ValueError("PROJECT_ID missing in environment variables")

# Initialize Vertex AI
vertexai.init(project=PROJECT_ID, location=LOCATION)
SUPERADMIN_OTP = os.getenv("SUPERADMIN_OTP")

def login_required(f):
    """Decorator that restricts access to logged-in admin users."""
    from functools import wraps

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("logged_in"):
            flash("Please log in to access the generator.", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

# ------------------------------
# Routes
# ------------------------------

@app.route("/login", methods=["GET", "POST"])
def login() -> Response:
    """Superadmin login page with OTP validation.

    Returns:
        Response: Renders the login form or redirects to the index if OTP is valid.
    """
    stored_otp = (os.getenv("SUPERADMIN_OTP") or "").strip().replace("\n", "").replace("\r", "").replace(" ", "")

    if request.method == "POST":
        entered_otp = (request.form.get("otp") or "").strip().replace("\n", "").replace("\r", "").replace(" ", "")
        print(f"🔍 DEBUG OTP | Entered='{entered_otp}' | Stored='{stored_otp}' | Match={entered_otp == stored_otp}")

        if entered_otp == stored_otp:
            session.permanent = True
            session["is_admin"] = True
            print("✅ OTP accepted — redirecting to index.")
            return redirect(url_for("index"))
        else:
            print("❌ Invalid OTP entered.")
            return render_template_string("""
                <!DOCTYPE html>
                <html lang="en">
                <head>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <title>Invalid OTP</title>
                    <style>
                        body { font-family: Arial; text-align: center; margin-top: 100px; }
                        a { color: #007bff; text-decoration: none; }
                    </style>
                </head>
                <body>
                    <h2 style='color:red;'>Invalid OTP</h2>
                    <a href='/login'>Try again</a>
                </body>
                </html>
            """)

    return render_template_string("""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Superadmin Login</title>
            <style>
                body { 
                    font-family: Arial, sans-serif; 
                    display: flex; 
                    flex-direction: column; 
                    align-items: center; 
                    justify-content: center; 
                    height: 100vh; 
                    background-color: #121212;
                    color: white;
                }
                input, button {
                    padding: 10px; 
                    margin: 10px;
                    border: none;
                    border-radius: 6px;
                }
                input {
                    width: 200px;
                    text-align: center;
                }
                button {
                    background-color: #4CAF50;
                    color: white;
                    cursor: pointer;
                }
                button:hover {
                    background-color: #45a049;
                }
            </style>
        </head>
        <body>
            <form method="POST">
                <h2>Enter Superadmin OTP</h2>
                <input type="password" name="otp" placeholder="Enter OTP" required>
                <button type="submit">Login</button>
            </form>
        </body>
        </html>
    """)


@app.before_request
def restrict_access() -> Response | None:
    """Restrict access to authorized users only."""
    if request.endpoint not in ("login", "static") and not session.get("is_admin"):
        return redirect(url_for("login"))


@app.route("/")
def index() -> Response:
    """Render the main web interface."""
    return render_template("index.html")


@app.route("/generate", methods=["POST"])
def generate_image() -> Response:
    """Generate image(s) using Vertex AI Imagen model.

    This endpoint generates one or more images based on the user's prompt and options.

    Request Body (JSON):
        prompt (str): The image description to generate.
        number_of_images (int, optional): Number of images to generate (default=1).
        aspect_ratio (str, optional): Aspect ratio, e.g. "1:1" or "16:9".
        negative_prompt (str, optional): Objects/concepts to avoid.

    Returns:
        Response: JSON containing a list of image URLs or an error message.
    """
    try:
        data = request.get_json()
        prompt = data.get("prompt")
        number_of_images = data.get("number_of_images", "1")
        aspect_ratio = data.get("aspect_ratio", "1:1")
        negative_prompt = data.get("negative_prompt", "")

        if not prompt:
            return jsonify({"error": "No prompt provided"}), 400

        # Load Imagen model
        model = ImageGenerationModel.from_pretrained("imagen-4.0-generate-001")

        # Generate image
        result = model.generate_images(
            prompt=prompt,
            number_of_images=int(number_of_images),
            aspect_ratio=aspect_ratio,
            negative_prompt=negative_prompt,
            person_generation="allow_all",
            safety_filter_level="block_few",
            add_watermark=True,
        )

        # Save image to static folder
        image_urls = []
        for img in result.images:
            static_dir = os.path.join(os.path.dirname(__file__), "static")
            os.makedirs(static_dir, exist_ok=True)
            
            filename = f"generated_{uuid.uuid4().hex}.png"
            output_path = os.path.join(static_dir, filename)
            img.save(output_path)

            filename = os.path.basename(output_path)
            image_urls.append(f"/static/{filename}?v={int(time.time())}")

        # Return image URL with timestamp (cache-buster)
        return jsonify({"image_urls": image_urls})

    except Exception as e:
        print("Error:", str(e))
        return jsonify({"error": str(e)}), 500


@app.route("/edit", methods=["POST"])
def edit_image() -> Response:
    """Edit an uploaded image using Vertex AI Imagen model.

    This endpoint accepts an image file and prompt to generate edited variants.

    Request Form Data:
        image (file): The uploaded image file to modify.
        prompt (str): The description of desired changes.
        number_of_images (int, optional): Number of variations to generate.

    Returns:
        Response: JSON containing a list of edited image URLs.
    """
    try:
        prompt = request.form.get("prompt", "").strip() or "Modify this image"
        number_of_images = int(request.form.get("number_of_images", 1))

        if "image" not in request.files:
            return jsonify({"error": "No image uploaded"}), 400

        # Save uploaded file temporarily
        uploaded = request.files["image"]
        temp_path = os.path.join(
            tempfile.gettempdir(), f"upload_{uuid.uuid4().hex}.png")
        uploaded.save(temp_path)

        # Read + base64 encode
        with open(temp_path, "rb") as f:
            img_b64 = base64.b64encode(f.read()).decode("utf-8")

        # ✅ Construct REST request body correctly
        body = {
            "instances": [
                {
                    "prompt": prompt,
                    "referenceImages": [
                        {
                            "referenceType": "REFERENCE_TYPE_RAW",
                            "referenceId": 1,
                            "referenceImage": {
                                "bytesBase64Encoded": img_b64
                            }
                        }
                    ],
                }
            ],
            # ✅ `parameters` moved to top level
            "parameters": {
                "sampleCount": number_of_images
            },
        }

        headers = {
            "Authorization": f"Bearer {credentials.token}",
            "Content-Type": "application/json",
        }

        response = requests.post(ENDPOINT, headers=headers, json=body)
        response.raise_for_status()
        result = response.json()

        predictions = result.get("predictions", [])
        if not predictions:
            print("⚠️ No predictions returned by Vertex AI:", result)
            return jsonify({"error": "Model returned no results — likely filtered or rejected."}), 400

        # Ensure static dir exists
        static_dir = os.path.join(os.path.dirname(__file__), "static")
        os.makedirs(static_dir, exist_ok=True)

        # Save decoded images
        image_urls = []
        for pred in predictions:
            data_b64 = pred.get("bytesBase64Encoded")
            if not data_b64:
                continue

            filename = f"edited_{uuid.uuid4().hex}.png"
            output_path = os.path.join(static_dir, filename)
            with open(output_path, "wb") as f:
                f.write(base64.b64decode(data_b64))

            image_urls.append(f"/static/{filename}?v={int(time.time())}")

        return jsonify({"image_urls": image_urls})

    except Exception as e:
        print("❌ Error in Imagen 3 Edit:", e)
        return jsonify({"error": str(e)}), 500
    

@app.route("/logout")
def logout() -> Response:
    """Log out the current admin session."""
    session.pop("is_admin", None)
    print("👋 Superadmin logged out.")
    return redirect(url_for("login"))


# ------------------------------
# Main Entry Point
# ------------------------------
if __name__ == "__main__":
    # Railway uses PORT env var, fallback to 8080 for local testing
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)

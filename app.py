from flask import Flask, request, jsonify, render_template,redirect,url_for, session, flask
from flask_cors import CORS
from dotenv import load_dotenv
import os
import json
import tempfile
import time
import uuid
import vertexai
from vertexai.preview.vision_models import ImageGenerationModel

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Load environment variables (if running locally)
load_dotenv()

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

if not PROJECT_ID:
    raise ValueError("PROJECT_ID missing in environment variables")

# Initialize Vertex AI
vertexai.init(project=PROJECT_ID, location=LOCATION)
SUPERADMIN_OTP = os.getenv("SUPERADMIN_OTP")

def login_required(f):
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
def login():
    if request.method == "POST":
        otp = request.form.get("otp")
        if otp == SUPERADMIN_OTP:
            session["logged_in"] = True
            flash("Access granted ✅", "success")
            return redirect(url_for("index"))
        else:
            flash("Invalid OTP ❌", "danger")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully.", "info")
    return redirect(url_for("login"))


@app.route("/")
def index():
    """Render the HTML UI."""
    return render_template("index.html")

@app.route("/generate", methods=["POST"])
def generate_image():
    """Generate an image using Vertex AI Imagen 4.0."""
    try:
        data = request.get_json()
        prompt = data.get("prompt")
        aspect_ratio = data.get("aspect_ratio", "1:1")
        negative_prompt = data.get("negative_prompt", "")

        if not prompt:
            return jsonify({"error": "No prompt provided"}), 400

        # Load Imagen model
        model = ImageGenerationModel.from_pretrained("imagen-4.0-generate-001")

        # Generate image
        result = model.generate_images(
            prompt=prompt,
            number_of_images=1,
            aspect_ratio=aspect_ratio,
            negative_prompt=negative_prompt,
            person_generation="allow_all",
            safety_filter_level="block_few",
            add_watermark=True,
        )

        # Save image to static folder
        filename = f"generated_{uuid.uuid4().hex}.png"
        output_path = os.path.join("static", filename)
        result.images[0].save(output_path)

        # Return image URL with timestamp (cache-buster)
        return jsonify({"image_url": f"/{output_path}?v={int(time.time())}"})

    except Exception as e:
        print("Error:", str(e))
        return jsonify({"error": str(e)}), 500

# ------------------------------
# Main Entry Point
# ------------------------------
if __name__ == "__main__":
    # Railway uses PORT env var, fallback to 8080 for local testing
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)

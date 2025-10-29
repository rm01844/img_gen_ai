from flask import Flask, request, jsonify, render_template,redirect,url_for, session, flash, render_template_string
from flask_cors import CORS
from dotenv import load_dotenv
import os
import json
import tempfile
import time
import uuid
import vertexai
from vertexai.preview.vision_models import ImageGenerationModel
from datetime import timedelta

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
app.permanent_session_lifetime = timedelta(hours=1)

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
def restrict_access():
    if request.endpoint not in ("login", "static") and not session.get("is_admin"):
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

@app.route("/debug_otp")
def debug_otp():
    val = os.getenv("SUPERADMIN_OTP")
    return {
        "otp_type": str(type(val)),
        "otp_raw": repr(val),
        "otp_len": len(val) if val else 0,
    }


@app.route("/logout")
def logout():
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

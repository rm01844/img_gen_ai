"""
AI Image Generator API
----------------------
A Flask application that provides endpoints to generate and edit images using Google Vertex AI's Imagen models.

This module includes authentication, text-to-image generation, and image-editing endpoints.
"""

from flask import Flask, request, jsonify, render_template_string, render_template, redirect, url_for, session, Response, flash
from flask_cors import CORS
from IPython.display import Image as IPyImage
from google import genai
from google.genai.types import GenerateContentConfig, Part
from PIL import Image, ImageEnhance
# from insightface.app import FaceAnalysis
import numpy as np
import cv2
from vertexai.generative_models import GenerativeModel
from typing import Optional
from functools import wraps
from datetime import timedelta
from google.oauth2 import service_account
from google.auth.transport.requests import Request
from vertexai.preview.vision_models import ImageGenerationModel
import vertexai
import requests
import base64
import uuid
import tempfile
import time
from urllib.parse import urlparse, unquote
import os 
from dotenv import load_dotenv

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

# Get GCP configuration from environment
PROJECT_ID = os.getenv("PROJECT_ID")
LOCATION = os.getenv("LOCATION", "us-central1")
service_key_json = os.getenv("SERVICE_KEY_JSON")
local_credentials = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

SCOPES = ["https://www.googleapis.com/auth/cloud-platform"]

credentials_path = None

if service_key_json:
    # Running on Railway (JSON string from environment)
    key_path = os.path.join(tempfile.gettempdir(), "vertex-key.json")
    with open(key_path, "w") as f:
        f.write(service_key_json)
    credentials_path = key_path
    print("✅ Using SERVICE_KEY_JSON from environment")
elif local_credentials:
    # Check if it's a path
    if os.path.exists(local_credentials):
        credentials_path = local_credentials
        print(f"✅ Using local credentials: {local_credentials}")
    else:
        print(
            f"⚠️ GOOGLE_APPLICATION_CREDENTIALS path does not exist: {local_credentials}")
        # Maybe it's the JSON content itself?
        try:
            import json
            json.loads(local_credentials)
            # It's valid JSON, write it to a temp file
            key_path = os.path.join(tempfile.gettempdir(), "vertex-key.json")
            with open(key_path, "w") as f:
                f.write(local_credentials)
            credentials_path = key_path
            print("✅ Parsed GOOGLE_APPLICATION_CREDENTIALS as JSON content")
        except:
            print(
                "❌ GOOGLE_APPLICATION_CREDENTIALS is neither a valid path nor valid JSON")

if not credentials_path:
    print("\n❌ ERROR: Could not find valid credentials!")
    print("Please set one of the following environment variables:")
    print("  1. SERVICE_KEY_JSON (JSON content as string)")
    print("  2. GOOGLE_APPLICATION_CREDENTIALS (path to JSON file)")
    print("\nExample .env file:")
    print("  PROJECT_ID=your-project-id")
    print("  LOCATION=us-central1")
    print("  GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json")
    raise FileNotFoundError("❌ Could not find valid credentials.")

# Load credentials
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path
credentials = service_account.Credentials.from_service_account_file(
    credentials_path, scopes=SCOPES
)
credentials.refresh(Request())
print("✅ Credentials loaded and refreshed successfully")

# Initialize Vertex AI
vertexai.init(project=PROJECT_ID, location=LOCATION)
client = genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION)

# Imagen 3 API endpoint
MODEL_ID = "gemini-2.5-flash-image"
ENDPOINT = f"https://{LOCATION}-aiplatform.googleapis.com/v1/projects/{PROJECT_ID}/locations/{LOCATION}/publishers/google/models/{MODEL_ID}:predict"

# SuperAdmin OTP
SUPERADMIN_OTP = os.getenv("SUPERADMIN_OTP")

# Initialize Gemini model for prompt refinement
gemini = GenerativeModel("gemini-2.5-pro")

# Face detection (lazy load)
# _face_app = None

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

# def get_face_app():
#     """Lazy initialization of face detection"""
#     global _face_app
#     if _face_app is None:
#         _face_app = FaceAnalysis(name="buffalo_l", providers=[
#                                  "CPUExecutionProvider"])
#         _face_app.prepare(ctx_id=0)
#     return _face_app


# def extract_skin_tone_description(img_path: str) -> str:
#     """
#     Extract detailed skin tone information from the reference image.
#     Returns a description that can be used in prompts to preserve ethnicity.
#     """
#     try:
#         face_app = get_face_app()
#         img = cv2.imread(img_path)
#         if img is None:
#             return ""

#         faces = face_app.get(img)
#         if not faces:
#             return ""

#         # Get the largest face
#         face = max(faces, key=lambda f: (
#             f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1]))
#         x1, y1, x2, y2 = face.bbox.astype(int)

#         # Extract face region
#         face_region = img[y1:y2, x1:x2]

#         # Calculate average color in LAB space (more perceptually uniform)
#         face_lab = cv2.cvtColor(face_region, cv2.COLOR_BGR2LAB)
#         avg_color = np.mean(face_lab, axis=(0, 1))

#         L, a, b = avg_color

#         # Classify skin tone based on L channel and a/b values
#         if L > 200:
#             tone = "very fair skin tone with pale complexion"
#         elif L > 170:
#             tone = "fair skin tone with light complexion"
#         elif L > 140:
#             tone = "medium-light skin tone with warm undertones"
#         elif L > 110:
#             tone = "medium skin tone with neutral undertones"
#         elif L > 80:
#             tone = "medium-dark skin tone with olive undertones"
#         elif L > 50:
#             tone = "dark skin tone with rich brown complexion"
#         else:
#             tone = "very dark skin tone with deep brown complexion"

#         # Add undertone information based on a and b channels
#         if a < -5:
#             tone += ", greenish undertones"
#         elif b > 15:
#             tone += ", warm golden undertones"
#         elif b < 0:
#             tone += ", cool blue undertones"

#         return tone
#     except Exception as e:
#         print(f"⚠️ Skin tone extraction failed: {e}")
#         return ""


# def build_improved_edit_prompt(user_prompt: str, skin_tone_desc: str = "") -> str:
#     """
#     Build a structured prompt that enforces constraints while allowing creative changes.
#     """
#     # Parse the user prompt to identify key elements
#     lines = [ln.strip() for ln in user_prompt.split("\n") if ln.strip()]

#     # Build constraint section
#     constraint_text = f"""STRICT IDENTITY CONSTRAINTS:
# - Maintain EXACT facial features, proportions, and bone structure from reference
# - Preserve EXACT skin tone: {skin_tone_desc or "match the reference image precisely"}
# - Keep original ethnicity and racial characteristics unchanged
# - Do NOT alter, lighten, or darken skin color under any circumstances

# COMPOSITION RULES:
# - Follow the layout description precisely
# - Only include objects explicitly mentioned in the prompt
# - Do NOT add weapons, guns, sticks, or any items not specified
# - Arrange items exactly as described in numbered lists
# - Use clean, minimal composition without extra clutter

# EDIT INSTRUCTIONS:
# {chr(10).join([f"• {ln}" for ln in lines])}

# TECHNICAL QUALITY:
# - Studio lighting with soft shadows
# - Professional product photography style
# - Sharp focus on main subject
# - Natural color rendering (avoid oversaturation)
# - Clean white or neutral background unless specified otherwise"""

#     return constraint_text


# def refine_prompt_with_gemini(raw_prompt: str, skin_tone: str = "") -> str:
#     """Use Gemini to restructure prompt with strict constraints."""
#     try:
#         if not raw_prompt.strip():
#             return "Modify this image while preserving all facial features and skin tone."

#         system_instruction = f"""You are a prompt engineer for Google Vertex Imagen 3 image editing API.
# Rewrite this prompt to be:
# 1. EXTREMELY EXPLICIT about preserving the person's exact facial features and skin tone
# 2. HIGHLY STRUCTURED with clear numbered steps for layout
# 3. SPECIFIC about what NOT to include (e.g., no weapons, no extra objects)

# CRITICAL RULES:
# - Always start with: "IDENTITY PRESERVATION: Keep the exact face, {skin_tone or 'skin tone'}, and proportions from the reference."
# - Break complex layouts into numbered steps
# - List items to EXCLUDE in a "DO NOT ADD" section
# - Use professional photography terminology
# - Keep it under 500 words

# Original prompt: {raw_prompt}"""

#         response = gemini.generate_content(system_instruction)
#         refined = getattr(response, "text", "") or ""

#         if not refined.strip() or len(refined.strip()) < 10:
#             print("⚠️ Gemini returned empty text, using fallback")
#             return build_improved_edit_prompt(raw_prompt, skin_tone)

#         return refined.strip()
#     except Exception as e:
#         print(f"⚠️ Gemini refinement failed: {e}")
#         return build_improved_edit_prompt(raw_prompt, skin_tone)


# def apply_skin_tone_preservation(reference_path: str, generated_path: str) -> None:
#     """
#     Apply aggressive color correction to match reference skin tone.
#     Runs AFTER generation to fix any tone drift.
#     """
#     try:
#         face_app = get_face_app()

#         ref_img = cv2.imread(reference_path)
#         gen_img = cv2.imread(generated_path)

#         if ref_img is None or gen_img is None:
#             return

#         ref_faces = face_app.get(ref_img)
#         gen_faces = face_app.get(gen_img)

#         if not ref_faces or not gen_faces:
#             print("⚠️ No faces detected for skin preservation")
#             return

#         ref_face = max(ref_faces, key=lambda f: (
#             f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1]))
#         gen_face = max(gen_faces, key=lambda f: (
#             f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1]))

#         rx1, ry1, rx2, ry2 = ref_face.bbox.astype(int)
#         gx1, gy1, gx2, gy2 = gen_face.bbox.astype(int)

#         # bounds clamp
#         Href, Wref = ref_img.shape[:2]
#         Hgen, Wgen = gen_img.shape[:2]
#         rx1, ry1 = max(0, rx1), max(0, ry1)
#         rx2, ry2 = min(Wref, rx2), min(Href, ry2)
#         gx1, gy1 = max(0, gx1), max(0, gy1)
#         gx2, gy2 = min(Wgen, gx2), min(Hgen, gy2)

#         if rx2 <= rx1 or ry2 <= ry1 or gx2 <= gx1 or gy2 <= gy1:
#             return

#         ref_face_region = ref_img[ry1:ry2, rx1:rx2]
#         gen_face_region = gen_img[gy1:gy2, gx1:gx2]
#         if ref_face_region.size == 0 or gen_face_region.size == 0:
#             return

#         # LAB color space matching
#         ref_lab = cv2.cvtColor(
#             ref_face_region, cv2.COLOR_BGR2LAB).astype(float)
#         gen_lab = cv2.cvtColor(
#             gen_face_region, cv2.COLOR_BGR2LAB).astype(float)

#         ref_mean, ref_std = ref_lab.mean(axis=(0, 1)), ref_lab.std(axis=(0, 1))
#         gen_mean, gen_std = gen_lab.mean(axis=(0, 1)), gen_lab.std(axis=(0, 1))

#         # Color transfer
#         for i in range(3):
#             gen_lab[:, :, i] = ((gen_lab[:, :, i] - gen_mean[i]) *
#                                 (ref_std[i] / (gen_std[i] + 1e-6))) + ref_mean[i]

#         gen_lab = np.clip(gen_lab, 0, 255).astype(np.uint8)
#         corrected_face = cv2.cvtColor(gen_lab, cv2.COLOR_LAB2BGR)

#         # soft ellipse mask
#         h, w = gen_face_region.shape[:2]
#         mask = np.zeros((h, w), dtype=np.float32)
#         cv2.ellipse(mask, (w//2, h//2), (w//2, h//2), 0, 0, 360, 1, -1)
#         mask = cv2.GaussianBlur(mask, (51, 51), 30)[..., None]

#         blended = (corrected_face * mask + gen_face_region *
#                    (1 - mask)).astype(np.uint8)
#         gen_img[gy1:gy2, gx1:gx2] = blended
#         cv2.imwrite(generated_path, gen_img, [cv2.IMWRITE_PNG_COMPRESSION, 9])
#         print("✅ Skin tone preservation applied")
#     except Exception as e:
#         print(f"⚠️ Skin preservation failed: {e}")

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
    """Edit an uploaded image using Gemini 2.5 Flash Image model.

    This endpoint accepts an image file and prompt to generate edited variants.

    Request Form Data:
        image (file): The uploaded image file to modify.
        prompt (str): The description of desired changes.
        number_of_images (int, optional): Number of variations to generate.

    Returns:
        Response: JSON containing a list of edited image URLs.
    """
    try:
        raw_prompt = request.form.get("prompt", "").strip()
        if "image" not in request.files:
            return jsonify({"error": "No image uploaded"}), 400

        uploaded = request.files["image"]
        temp_path = os.path.join(
            tempfile.gettempdir(), f"upload_{uuid.uuid4().hex}.png")
        uploaded.save(temp_path)

        with open(temp_path, "rb") as f:
            image_bytes = f.read()

        print(f"🖌️ Editing with Gemini 2.5 Flash Image...")

        response = client.models.generate_content(
            model="gemini-2.5-flash-image",
            contents=[
                {"role": "user", "parts": [
                    {"text": raw_prompt},
                    {"inline_data": {"mime_type": "image/png", "data": image_bytes}}
                ]}
            ],
            config=GenerateContentConfig(
                response_modalities=["IMAGE"],
                candidate_count=1,
            ),
        )

        static_dir = os.path.join(os.path.dirname(__file__), "static")
        os.makedirs(static_dir, exist_ok=True)
        filename = f"edited_{uuid.uuid4().hex}.png"
        output_path = os.path.join(static_dir, filename)

        for part in response.candidates[0].content.parts:
            if hasattr(part, "inline_data"):
                with open(output_path, "wb") as f:
                    f.write(part.inline_data.data)

        print(f"✅ Edit successful: {output_path}")
        return jsonify({"image_urls": [f"/static/{filename}?v={int(time.time())}"]})

    except Exception as e:
        print(f"❌ Edit error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/chat_edit", methods=["POST"])
def chat_edit() -> Response:
    """Iterative editing via chat interface using Gemini 2.5 Flash Image."""
    try:
        data = request.get_json()
        instruction = data.get("instruction", "")
        image_path = data.get("image_path", "")

        # 🔹 Validate input
        if not instruction or not image_path:
            return jsonify({"error": "Missing instruction or image"}), 400

        # 🔹 Clean up image path and resolve absolute path safely
        parsed_path = urlparse(image_path).path  # Remove query params like ?v=123
        clean_path = unquote(parsed_path).lstrip("/")  # Decode spaces and strip leading slash
        abs_path = os.path.join(os.getcwd(), clean_path)

        # 🔹 If not found in working dir, try relative to script location
        if not os.path.exists(abs_path):
            alt_path = os.path.join(os.path.dirname(__file__), clean_path)
            if os.path.exists(alt_path):
                abs_path = alt_path
            else:
                print(f"❌ Image not found: {clean_path}")
                return jsonify({
                    "error": f"Image not found: {clean_path}. Please re-upload or re-generate before refining."
                }), 404

        # 🔹 Prepare directive prompt
        directive_prompt = f"""IDENTITY PRESERVATION: Maintain exact facial features.
CHANGE REQUEST: {instruction}
CONSTRAINTS:
- Do NOT alter skin tone or facial structure
- Only modify elements explicitly mentioned
- Preserve realism and consistent lighting
- Professional studio photo quality"""

        print("🧠 Gemini 2.5 Flash Image chat-edit in progress...")

        # 🔹 Read image bytes (Gemini expects raw bytes, not base64)
        with open(abs_path, "rb") as f:
            image_bytes = f.read()

        # 🔹 Generate new version using Gemini 2.5 Flash Image
        response = client.models.generate_content(
            model="gemini-2.5-flash-image",
            contents=[
                {
                    "role": "user",
                    "parts": [
                        {"text": directive_prompt},
                        {"inline_data": {"mime_type": "image/png", "data": image_bytes}}
                    ],
                }
            ],
            config=GenerateContentConfig(
                response_modalities=["IMAGE"],
                candidate_count=1,
            ),
        )

        # 🔹 Save edited image in /static
        static_dir = os.path.join(os.path.dirname(__file__), "static")
        os.makedirs(static_dir, exist_ok=True)
        filename = f"chat_edit_{uuid.uuid4().hex}.png"
        output_path = os.path.join(static_dir, filename)

        for part in response.candidates[0].content.parts:
            if hasattr(part, "inline_data"):
                with open(output_path, "wb") as f:
                    f.write(part.inline_data.data)

        print(f"✅ Chat-edit successful: {output_path}")
        return jsonify({"image_url": f"/static/{filename}?v={int(time.time())}"})

    except Exception as e:
        print(f"❌ Chat-edit error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/compose", methods=["POST"])
def compose_images():
    """
    Combine multiple uploaded images into one composition.
    Example prompt:
      "Make an action figure of the person on the left and the accessories on the right in a blister package."
    """
    try:
        prompt = request.form.get("prompt", "").strip()
        uploads = request.files.getlist("images")

        if not uploads or not prompt:
            return jsonify({"error": "Please upload images and provide a prompt"}), 400

        parts = [{"text": prompt}]
        for img in uploads:
            img_bytes = img.read()
            parts.append({
                "inline_data": {
                    "mime_type": "image/png",
                    "data": img_bytes
                }
            })

        print(
            f"🧩 Composing {len(uploads)} images with Gemini 2.5 Flash Image...")

        response = client.models.generate_content(
            model="gemini-2.5-flash-image",
            contents=[{"role": "user", "parts": parts}],
            config=GenerateContentConfig(
                response_modalities=["IMAGE"],
                candidate_count=1,
            ),
        )

        static_dir = os.path.join(os.path.dirname(__file__), "static")
        os.makedirs(static_dir, exist_ok=True)
        filename = f"composed_{uuid.uuid4().hex}.png"
        output_path = os.path.join(static_dir, filename)

        for part in response.candidates[0].content.parts:
            if hasattr(part, "inline_data"):
                with open(output_path, "wb") as f:
                    f.write(part.inline_data.data)

        print(f"✅ Composition created: {output_path}")
        return jsonify({"image_url": f"/static/{filename}?v={int(time.time())}"})

    except Exception as e:
        print(f"❌ Composition error: {e}")
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

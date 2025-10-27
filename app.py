from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from dotenv import load_dotenv
import os
import json
import time
import uuid
import vertexai
from vertexai.preview.vision_models import ImageGenerationModel

app = Flask(__name__)
CORS(app)

# Load environment variables
load_dotenv()
PROJECT_ID = os.getenv("PROJECT_ID")
LOCATION = os.getenv("LOCATION")

if not PROJECT_ID:
    raise ValueError("PROJECT_ID missing in .env file")

# Initialize Vertex AI
vertexai.init(project=PROJECT_ID, location=LOCATION)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/generate", methods=["POST"])
def generate_image():
    try:
        data = request.get_json()
        prompt = data.get("prompt")
        aspect_ratio = data.get("aspect_ratio", "1:1")
        negative_prompt = data.get("negative_prompt", "")

        if not prompt:
            return jsonify({"error": "No prompt provided"}), 400

        # Load Imagen 4.0 model
        model = ImageGenerationModel.from_pretrained("imagen-4.0-generate-001")

        # Generate images
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
        output_path = f"static/{filename}"
        result.images[0].save(output_path)

        return jsonify({"image_url": f"/{output_path}?v={int(time.time())}"})

    except Exception as e:
        print("Error:", str(e))
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(port=5000, debug=True)

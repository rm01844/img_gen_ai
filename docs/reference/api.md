# 🧠 AI Image Generation API

This API enables developers to **generate** and **edit** images using
Google Vertex AI’s **Imagen models** through a secure Flask REST interface.

---

## 🔗 Base URL

The application is deployed and hosted on **Railway.app**.  
This URL serves as the **root endpoint** for all API requests.

**Base URL:**  
[https://web-production-fc79.up.railway.app/](https://web-production-fc79.up.railway.app/)

> Example:  
> To access `/generate`, send a POST request to  
> `https://web-production-fc79.up.railway.app/generate`


---

## 🔐 Authentication

All API endpoints require a valid **Bearer token** to be included in the request header.  
This token is used to authenticate and authorize client requests.

**Header Format:**

Authorization: Bearer <YOUR_API_TOKEN>


### 🔑 Obtaining the Token
Bearer tokens are provided by the **API administrator** upon onboarding.  
Each client or integration partner will receive a unique token associated with their account.

If you have not received your token, please contact the API administrator or project owner.

> ⚠️ **Important:**  
> - Do **not** share your token publicly or embed it in client-side code.  
> - Tokens are tied to your project identity and usage limits.  
> - Rotate tokens periodically or immediately if compromised.

### 🧩 Example: Authenticated Request

```bash
curl -X POST https://web-production-fc79.up.railway.app/generate \
  -H "Authorization: Bearer your_api_token_here" \
  -H "Content-Type: application/json" \
  -d '{"prompt":"a serene landscape with mountains and clouds"}'
```

---

## 📦 Requirements

- **Python 3.10+**
- **Google Cloud Vertex AI API enabled and copy the API_TOKEN**
- A **service account key (.json)** with the `Vertex AI User` and `Storage Admin` roles
- Railway.app or Render account for deployment
- MkDocs (optional) for documentation hosting

---

## ✨ Endpoints

### **POST /generate**

Generate one or more images from a text prompt.

Request Body

| Field              | Type   | Required | Description                                                  |
| ------------------ | ------ | -------- | ------------------------------------------------------------ |
| `prompt`           | string | ✅        | Description of the image to generate                         |
| `number_of_images` | int    | ❌        | Default: `1`, number of images to create                     |
| `aspect_ratio`     | string | ❌        | Default: `"1:1"`, aspect ratio such as `16:9`, `3:4`, `9:16` |
| `negative_prompt`  | string | ❌        | Optional text describing what to avoid                       |


Example

{
  **prompt**: "A futuristic city skyline at sunset",
  **number_of_images**: 2,
  **aspect_ratio**: "16:9"
}

Response

{
  **image_urls**: [
    "/static/generated_8fa3b3.png",
    "/static/generated_19df1d.png"
  ]
}

**Underlying Model:** imagen-4.0-generate-001
**Provider:** Google Vertex AI


### **POST /edit**

This endpoint enables **AI-powered image editing** by combining  
Google **Gemini 2.5 Pro** (for intelligent prompt refinement and feedback)  
with **Gemini 2.5 Flash Image** (for photo-realistic image generation).

---

### 🧩 Workflow Overview

1. **Prompt Refinement (Gemini 2.5 Pro)**
   - The user’s raw text prompt is rewritten by Gemini to be concise, spatially descriptive, and better aligned with Gemini's generation semantics.
   - Example transformation:  
     > _"Turn this person into an action figure in orange packaging"_  
     → _"Create a high-resolution product photo of the same person as a realistic action figure packaged in an orange blister pack with accessories arranged symmetrically and a name label at the top."_

2. **Image Generation (Gemini 2.5 Flash Image)**
   - The refined prompt and uploaded reference image are sent to Gemini 2.5 Flash Image to produce the edited output.

3. **Automated Feedback (Gemini Vision Review)**
   - Gemini optionally evaluates the generated image for identity and layout consistency,  
     then suggests a refined prompt for re-generation to improve results.

---

### 🔐 Authentication

All requests must include a valid **Bearer Token** in the HTTP header:

```bash
Authorization: Bearer <YOUR_API_TOKEN> 
```

Request (multipart/form-data)

| Field              | Type   | Required | Description                                           |
| ------------------ | ------ | -------- | ----------------------------------------------------- |
| `image`            | file   | ✅       | The source image to edit                              |
| `prompt`           | string | ✅       | Natural-language description of desired changes       |
| `number_of_images` | int    | ❌       | Default: `1`, number of variations to return          |
| `negative_prompt`  | string | ❌       | Optional text describing elements to avoid.           |
| `edit_strength`    | float  | ❌       | Degree of transformation, range 0.1–1.0 (default 0.55)|
| `enhance_detail`   | bool   | ❌       | Enhance visual detail and sharpness (true by default) |


Example 

```bash
curl -X POST https://web-production-fc79.up.railway.app/edit \
  -H "Authorization: Bearer <YOUR_API_TOKEN>" \
  -F "image=@ben_philip.jpg" \
  -F "prompt=Create a photo-realistic action figure of the same person in orange packaging with accessories neatly arranged." \
  -F "number_of_images=2"
```

Response

{
  **image_urls**: [
    "/static/edited_a13c0d.png",
    "/static/edited_b28d9f.png"
  ]
}

**Underlying Model**: Gemini 2.5 Flash Image + Gemini 2.5 Pro
**Provider:** Google Vertex AI

## Architecture Overview

```mermaid
graph TD
  A[Client Request (POST /edit)] --> B[Flask API (Python)]
  B -->|Multipart form: prompt + image| C[Gemini 2.5 Pro (Prompt Refinement)]
  C -->|Refined prompt| D[Nano Banana - Gemini 2.5 Flash Image(Image Editing)]
  D -->|Generated image URLs| E[Gemini Vision Review (Optional Feedback)]
  E -->|Revised prompt (if needed)| D
  D -->|Final image URLs| F[Flask API Response]
  F -->|JSON Response| G[Client (Web UI / API Consumer)]
```

## ⚠️ Error Handling

| HTTP Code | Meaning        | Example Cause              |
| --------- | -------------- | -------------------------- |
| 400       | Bad Request    | Missing prompt or file     |
| 401       | Unauthorized   | Invalid or missing token   |
| 404       | Not Found      | Endpoint mismatch          |
| 500       | Internal Error | Vertex API or server issue |

🧠 Notes

- Images are saved temporarily under /static/.

- Watermarks may be applied by Vertex AI for compliance.

- The API auto-refreshes credentials from your GCP service account.


---


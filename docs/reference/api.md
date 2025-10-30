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

Edit or transform an uploaded image using a text prompt.

Request (multipart/form-data)

| Field              | Type   | Required | Description                                  |
| ------------------ | ------ | -------- | -------------------------------------------- |
| `image`            | file   | ✅        | The source image to edit                     |
| `prompt`           | string | ✅        | The modification description                 |
| `number_of_images` | int    | ❌        | Default: `1`, number of variations to return |


Example 

```bash
curl -X POST https://web-production-fc79.up.railway.app/edit \
  -H "Authorization: Bearer <YOUR_API_TOKEN>" \
  -F "image=@castle.png" \
  -F "prompt=add fog and a dragon in the sky" \
  -F "number_of_images=2"
```

Response

{
  **image_urls**: [
    "/static/edited_a13c0d.png",
    "/static/edited_b28d9f.png"
  ]
}

**Underlying Model**: imagen-3.0-capability-001
**Provider:** Google Vertex AI

## Architecture Overview

```mermaid
graph TD
  A[Client / SDK / Postman] -->|POST /generate or /edit| B[Flask API (Railway)]
  B -->|Bearer Token| C[Auth Middleware]
  B -->|Vertex API call| D[Google Imagen Models (v3/v4)]
  D -->|Base64 images| B
  B -->|JSON response| A
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


## 🧩 **`docs/deployment.md`**


# 🚀 Deployment Guide

This document explains how to deploy and configure the **AI Image Generator API** using Google Vertex AI and Flask.

---

## 🧰 Environment Variables

Create a `.env` file (or configure on Railway):

| Variable | Description | Example |
|-----------|--------------|----------|
| `PROJECT_ID` | Your Google Cloud project ID | `your_project_ID` |
| `LOCATION` | Vertex AI region | `us-central1` |
| `SERVICE_KEY_JSON` | JSON contents of the service account key | `service account key (.json)` |
| `API_TOKEN` | Secret used for client API authentication | `API_TOKEN` |
| `SUPERADMIN_OTP` | OTP for admin web login | `custom_otp` |
| `SECRET_KEY` | Flask session encryption key | `random_flask_secret` |
| `PORT` | App port | `8080` |

> ⚠️ Never commit `.env` or `.json` files to GitHub.

## 🧱 Directory Structure

```bash
Img_gen_AI/
├── img_gen_ai/
│   ├── app.py
│   ├── __init__.py
│   ├── static/
│   ├── templates/
│       ├── index.html
│       └── login.html
└── docs/
│   ├── index.md 
│   ├── reference/
│       └── api.md
│       └── app.md
│   └── deployment.md
├── Procfile
├── mkdocs.yml
├── requirements.txt
└── README.md
```


---

## ⚙️ Deployment (Railway)

1. **Push to GitHub**
   - Ensure your `requirements.txt` and `Procfile` exist.

2. **Create Railway project**
   - Connect GitHub repo.
   - Set environment variables in **Settings → Variables**.

3. **Build & deploy**
   Railway auto-detects Flask from `Procfile`:

web: gunicorn img_gen_ai.app:app


4. **Access the app**

https://example.railway.app/login


---

## 🔐 Security Checklist

- [ ] Store tokens and service keys only in environment variables  
- [ ] Use long, random API tokens (≥ 32 chars)  
- [ ] Rotate API tokens periodically  
- [ ] Restrict GCP service account to minimal permissions  
- [ ] Enable HTTPS (Railway provides automatically)

---

## 🧠 Under the Hood

| Component | Purpose |
|------------|----------|
| **Flask** | Web framework and routing |
| **Vertex AI Imagen** | AI image generation and editing |
| **Google Service Account** | Authenticates your app with Vertex |
| **Gunicorn** | Production web server |
| **MkDocs** | Documentation generator |

---

## ✅ Verification

After deployment, test your API using:
```bash
curl -X POST https://example.railway.app/api \
-H "Authorization: Bearer <YOUR_API_TOKEN>" \
-H "Content-Type: application/json" \
-d '{"prompt":"a mountain landscape in watercolor","number_of_images":1}'
```
Expected Response:

{
  "image_urls": ["/static/generated_<uuid>.png"]
}

## 🧾 Credits

Google Cloud Vertex AI Imagen

Flask for backend

Railway.app for deployment

MkDocs for documentation


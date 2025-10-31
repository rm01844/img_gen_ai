# 🧠 AI Image Generator — Flask + Google Vertex AI Imagen 4.0

```[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/new/template?template=https://github.com/rm01844/img_gen_ai&envs=PROJECT_ID,LOCATION,SECRET_KEY,SUPERADMIN_OTP,SERVICE_KEY_JSON,PORT&PROJECT_IDDesc=Your+Google+Cloud+Project+ID&LOCATIONDesc=Vertex+AI+region+(e.g.,+us-central1)&SECRET_KEYDesc=Flask+secret+key+for+sessions&SUPERADMIN_OTPDesc=Admin+login+OTP&SERVICE_KEY_JSONDesc=Paste+the+full+Service+Account+JSON+content+here&PORTDefault=8080)```
```[![Deploy on Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/rm01844/img_gen_ai)```

A production-ready **Flask web app** that integrates **Google Vertex AI Imagen 4.0** for AI-driven image generation.  
Includes **Superadmin OTP authentication**, **responsive frontend**, and **easy deployment** on **Railway** or **Render**.

## 📘 Documentation

Official hosted documentation:  
[https://rm01844.github.io/img_gen_ai/](https://rm01844.github.io/img_gen_ai/)

---

## 🚀 Features

- ✨ Generate AI images with **Google Imagen 4.0**
- 🔐 **Superadmin OTP login** — restricts access to authorized users
- ☁️ **Vertex AI integration** via service account authentication
- ⚙️ Works both **locally** and **in the cloud**
- 🧭 Supports multiple aspect ratios (`1:1`, `16:9`, `4:3`, `9:16`, etc.)
- 🕒 **Session timeout** after 1 hour for added security
- 📱 **Fully responsive UI** for mobile, tablet, and desktop
- 🔁 **Logout button** for instant session clearing

---

## 🧩 Project Structure

img_gen_ai/
├── app.py # Flask backend logic
├── requirements.txt # Dependencies
├── Procfile # For gunicorn-based deployment
├── .env # Local environment variables (excluded from git)
├── .gitignore # Excludes creds, venv, cache files
├── templates/
│ └── index.html # Main frontend template
├── static/
│ ├── favicon.ico # App icon
│ └── generated_image.png # Sample generated image
└── venv/ # Local virtual environment (ignored)


---

## ⚙️ Setup Instructions

### 1️⃣ Clone the repository

```bash
git clone https://github.com/rm01844/img_gen_ai.git
cd img_gen_ai
```

2️⃣ Create and activate a virtual environment
```python3 -m venv venv```
```source venv/bin/activate```      # macOS / Linux
```venv\Scripts\activate```         # Windows

3️⃣ Install dependencies
```bash
pip install -r requirements.txt
```

4️⃣ Create a .env file
```
PROJECT_ID=" "
LOCATION=us-central1
GOOGLE_APPLICATION_CREDENTIALS=" "
SECRET_KEY=my_super_secret_key
SUPERADMIN_OTP=123456
FLASK_ENV=development
```

5️⃣ Add your Google Cloud credentials

Download your service account key from the Google Cloud Console and save it as a .json file in the root directory.
(Never commit this file to GitHub — it should remain local only!)


🧠 Google Cloud Vertex AI Setup

1. Go to the Google Cloud Console.

2. Create or select your project.

3. Enable these APIs:

    3.1. Vertex AI API

    3.2. Cloud Storage API

    3.3. IAM Service Account Credentials API

4. Create a Service Account and grant it the Vertex AI User role.

5. Generate a key (JSON) and download it.

6. Note your project_id and location (e.g., us-central1).


🧪 Run Locally
```bash
python app.py
```
Open localhost in browser
Login using the OTP you defined in .env

🌐 Deploy to the Cloud
🚄 Deploy on Railway (Recommended)

Click below 👇

Then set these variables in Railway’s Environment tab:

Variable	            Description
PROJECT_ID	          Your GCP project ID
LOCATION	            Vertex AI region (e.g., us-central1)
SECRET_KEY	          Flask session key
SUPERADMIN_OTP	      Admin login OTP
SERVICE_KEY_JSON	    Full JSON text of your Google service key
PORT	                8080

✅ Procfile (already included):
```makefile
web: gunicorn app:app
```

⚙️ Deploy on Render

Click below 👇

Configure your environment variables in Render’s dashboard (same as above).

✅ Start command:

```
gunicorn app:app
```

✅ Build command:

```
pip install -r requirements.txt
```

✅ Environment:
Python 3.13 or higher

🔐 Authentication Flow

1. Open /login

2. Enter Superadmin OTP (defined in environment)

3. On success → redirects to main generator page

4. Logout clears the session instantly

Sessions expire automatically after 1 hour for security.

🧰 Environment Variables Summary
Variable	                          Purpose
PROJECT_ID	                        Google Cloud Project ID
LOCATION	                          Vertex AI region
SECRET_KEY	                        Flask session encryption key
SUPERADMIN_OTP	                    One-time password for admin login
SERVICE_KEY_JSON	                  Full JSON text of GCP service account
GOOGLE_APPLICATION_CREDENTIALS	    Local-only path to service key
FLASK_ENV	                          Development or production mode
PORT	                              Required by Railway/Render (default: 8080)

)
🎨 Frontend Overview

Simple, elegant, and responsive interface:

    Text input for prompt
    Dropdown for aspect ratio selection
    Real-time image preview
    Auto-resizing image box for all screen sizes
    Logout button (top right)

👨‍💻 Author

Raqeeb Mohamad Rafeek
AI Engineer | Data Scientist | Web-Developer

🌐 LinkedIn: https://www.linkedin.com/in/raqeeb-mohamad-rafeek-312a5721a/
💻 GitHub:   https://github.com/rm01844

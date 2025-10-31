# 🧠 AI Image Generation API Documentation

Welcome to the **AI Image Generation & Editing API**, powered by **Google Vertex AI (Imagen Models)** and deployed securely on **Railway**.

This service allows developers to:
- 🎨 Generate images from text prompts
- 🪄 Edit existing images using AI guidance
- 🔐 Access both web UI and REST API endpoints with token-based authentication

---

## 📘 Documentation Overview

| Section | Description |
|----------|--------------|
| [🧩 API Reference](reference/api.md) | Details of each endpoint (`/generate`, `/edit`), request/response formats, and sample payloads |
| [🧰 Application Overview](reference/app.md) | Explains how the Flask app, Vertex AI integration, and authentication system work |
| [🚀 Deployment Guide](deployment.md) | Step-by-step guide for deploying to Railway or another cloud platform |
| [📄 OpenAPI Spec](openapi.yaml) | Swagger schema to auto-import into Postman / Insomnia / client SDKs |

---

## 🚀 Quick Start

### Base URL

[https://web-production-fc79.up.railway.app/](https://web-production-fc79.up.railway.app/)

All endpoints are relative to this base URL.

## 🔧 Endpoints

| Endpoint | Method | Description |
|-----------|---------|-------------|
| `/generate` | POST | Generate image(s) from text prompt |
| `/edit` | POST | Edit uploaded image based on prompt |
| `/login` | GET/POST | Superadmin login (OTP required) |
| `/logout` | GET | End session |

### 🧠 Available Models
| Function | Model ID | Version | Provider |
|-----------|-----------|----------|-----------|
| Text → Image | `imagen-4.0-generate-001` | v4.0 | Google Vertex AI |
| Image → Image (Edit) | `imagen-3.0-capability-001` | v3.0 | Google Vertex AI |

---


🧭 Navigation
For API details → start with API Reference

For deployment or local setup → see Deployment Guide

For technical app overview → see Application Structure

For client-side import → use OpenAPI Spec


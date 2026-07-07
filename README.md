# Scholar AI 🎓

> **IBM Internship Project** — An AI-powered Research Assistant built with IBM watsonx Orchestrate and Flask.

---

## 📌 Overview

Scholar AI is a full-stack web application that leverages **IBM watsonx Orchestrate** to provide researchers with:

- 📄 **Paper Summarisation** — Condense academic papers instantly
- 🔍 **Semantic Search** — Find papers by meaning, not just keywords
- 💬 **Concept Explanation** — Plain-language explanations with citations
- 🔗 **Citation Management** — Auto-generate APA, MLA, IEEE, Chicago formats
- 📊 **Trend Analysis** — Identify emerging research trends
- 🔒 **Enterprise Security** — IBM-grade data privacy

---

## 🏗️ Project Structure

```
ScholarAI/
│
├── frontend/
│   ├── index.html          # Main HTML — hero, features, dashboard, chat
│   ├── style.css           # Dark glassmorphism theme, responsive, 4K-ready
│   └── script.js           # Chat UI, particles, animations, API client
│
├── backend/
│   ├── app.py              # Flask application factory & REST routes
│   ├── config.py           # Environment-based configuration
│   ├── requirements.txt    # Python dependencies
│   ├── .env.example        # Environment variable template
│   └── services/
│       └── orchestrate.py  # IBM watsonx Orchestrate integration
│
├── assets/
│   ├── images/             # Static image assets
│   ├── icons/              # SVG / icon assets
│   └── animations/         # Lottie / CSS animation assets
│
├── screenshots/            # Project screenshots for README / docs
├── README.md               # This file
└── .gitignore
```

---

## ⚡ Quick Start

### Prerequisites

| Tool         | Version  | Notes                              |
|--------------|----------|------------------------------------|
| Python       | ≥ 3.11   | `python --version`                 |
| pip          | latest   | `pip install --upgrade pip`        |
| Git          | any      | for cloning / version control      |
| IBM Cloud account | —   | Required for watsonx credentials   |

---

### 1 — Clone the Repository

```bash
git clone https://github.com/<your-username>/scholar-ai.git
cd scholar-ai
```

---

### 2 — Backend Setup

```bash
# Navigate to the backend directory
cd backend

# Create and activate a virtual environment
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

---

### 3 — Configure Environment Variables

```bash
# Copy the example file
cp .env.example .env
```

Open `backend/.env` and fill in your IBM watsonx credentials:

```env
WATSONX_API_KEY=your-ibm-cloud-api-key
WATSONX_PROJECT_ID=your-watsonx-project-id
WATSONX_REGION=us-south
WATSONX_MODEL_ID=ibm/granite-13b-chat-v2
```

> 💡 **Where to get these?**
> - **API Key**: [IBM Cloud](https://cloud.ibm.com) → Manage → Access (IAM) → API Keys
> - **Project ID**: [IBM watsonx](https://dataplatform.cloud.ibm.com) → Projects → your project → Manage → General

---

### 4 — Run the Backend

```bash
# From the backend/ directory (with venv active)
python app.py
```

You should see:
```
2024-01-01 12:00:00 [INFO] __main__ — Scholar AI backend created. Environment: development
 * Running on http://0.0.0.0:5000
```

Verify the API is running:
```bash
curl http://localhost:5000/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "Scholar AI Backend",
  "components": {
    "flask_api": "healthy",
    "watsonx": { "connected": true, "mode": "live" }
  }
}
```

---

### 5 — Run the Frontend

The frontend is pure HTML/CSS/JS — no build step required.

**Option A — VS Code Live Server (recommended)**
1. Install the [Live Server](https://marketplace.visualstudio.com/items?itemName=ritwickdey.LiveServer) extension
2. Right-click `frontend/index.html` → **Open with Live Server**
3. Browser opens at `http://127.0.0.1:5500`

**Option B — Python simple server**
```bash
cd frontend
python -m http.server 3000
# Open http://localhost:3000
```

**Option C — Direct file open**
```
Double-click frontend/index.html in your file explorer.
```

---

## 🌐 API Reference

### `GET /`
Returns service information.

```json
{
  "service": "Scholar AI",
  "version": "1.0.0",
  "powered_by": "IBM watsonx Orchestrate"
}
```

---

### `GET /health`
Health check — includes IBM watsonx connectivity status.

```json
{
  "status": "healthy",
  "components": {
    "flask_api": "healthy",
    "watsonx": { "connected": true, "mode": "live", "model": "ibm/granite-13b-chat-v2" }
  }
}
```

---

### `POST /chat`
Send a research question to Scholar AI.

**Request**
```json
{
  "message": "Summarise the transformer architecture paper",
  "history": [
    { "role": "user", "content": "Hello!" },
    { "role": "ai",   "content": "Hi there!" }
  ]
}
```

**Response**
```json
{
  "reply":      "The transformer architecture introduced in…",
  "model":      "ibm/granite-13b-chat-v2",
  "latency_ms": 450
}
```

**Error codes**

| Code | Meaning                             |
|------|-------------------------------------|
| 400  | Malformed JSON body                 |
| 415  | Missing `Content-Type: application/json` |
| 422  | Validation error (empty message, etc.) |
| 500  | Backend / watsonx error             |

---

## 🔧 Development

### Running in Mock Mode (no IBM credentials)

If `WATSONX_API_KEY` / `WATSONX_PROJECT_ID` are not set, the backend automatically enters **mock mode** and returns pre-built demo responses. The frontend remains fully functional.

### Debug Mode

```bash
# backend/.env
DEBUG=true
FLASK_ENV=development
```

### Production Deployment (Gunicorn)

```bash
cd backend
gunicorn -w 4 -b 0.0.0.0:5000 "app:create_app()"
```

---

## 🧰 Tech Stack

| Layer      | Technology                  | Purpose                          |
|------------|-----------------------------|----------------------------------|
| Frontend   | HTML5 · CSS3 · Vanilla JS   | Single-page research UI          |
| Backend    | Python 3.11+ · Flask 3      | REST API server                  |
| AI Engine  | IBM watsonx Orchestrate     | LLM inference & orchestration    |
| LLM Model  | IBM Granite 13B Chat v2     | Conversational AI responses      |
| Auth       | IBM IAM (API key → Bearer)  | Secure IBM Cloud authentication  |
| CORS       | Flask-CORS                  | Cross-origin request handling    |

---

## 🔒 Security Notes

- **Never commit** your `.env` file — it is listed in `.gitignore`
- API keys are loaded exclusively from environment variables
- Rotate your `SECRET_KEY` before production deployment
- Set `DEBUG=false` in production
- Restrict `CORS_ORIGINS` to your actual frontend domain in production

---

## 📸 Screenshots

> Add screenshots to the `screenshots/` folder and link them here.

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Commit your changes: `git commit -m "feat: add my feature"`
4. Push to the branch: `git push origin feature/my-feature`
5. Open a Pull Request

---

## 📄 License

This project is created as part of an **IBM internship** programme and is intended for educational and demonstration purposes.

---

## 👤 Author

Built with ❤️ as part of the **IBM watsonx Orchestrate** internship programme.

---

<p align="center">
  <strong>Scholar AI</strong> · Powered by IBM watsonx Orchestrate
</p>

"""
Scholar AI — app.py
Flask REST API backend for Scholar AI research assistant.
IBM watsonx Orchestrate integration-ready.
──────────────────────────────────────────────────────────────────
Endpoints:
  GET  /            → Service info
  GET  /health      → Health check
  POST /chat        → Chat with Scholar AI (IBM watsonx)
──────────────────────────────────────────────────────────────────
"""

import logging
import time
from datetime import datetime

from flask import Flask, jsonify, request
from flask_cors import CORS

from config import Config
from services.orchestrate import OrchestrateService

# ─── Logging configuration ───────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# ─── Application factory ─────────────────────────────────────────
def create_app(config: Config | None = None) -> Flask:
    """
    Create and configure the Flask application.

    Args:
        config: Optional Config instance. Defaults to Config() which
                reads from environment variables / .env file.

    Returns:
        Configured Flask app instance.
    """
    app = Flask(__name__)
    cfg = config or Config()
    app.config.from_object(cfg)

    # ─── CORS ─────────────────────────────────────────────────────
    CORS(
        app,
        resources={r"/*": {"origins": cfg.CORS_ORIGINS}},
        supports_credentials=False,
    )

    # ─── Services ─────────────────────────────────────────────────
    orchestrate = OrchestrateService(cfg)

    # ─── Request lifecycle hooks ──────────────────────────────────
    @app.before_request
    def log_request():
        request.start_time = time.time()
        logger.info("→ %s %s", request.method, request.path)

    @app.after_request
    def log_response(response):
        duration_ms = round((time.time() - request.start_time) * 1000)
        logger.info("← %s %s  %d  (%dms)",
                    request.method, request.path,
                    response.status_code, duration_ms)
        return response

    # ═══════════════════════════════════════════════════════════════
    # ROUTES
    # ═══════════════════════════════════════════════════════════════

    # ─── GET / ────────────────────────────────────────────────────
    @app.route("/", methods=["GET"])
    def index():
        """Service information endpoint."""
        return jsonify({
            "service":     "Scholar AI",
            "version":     "1.0.0",
            "description": "IBM watsonx-powered AI Research Assistant",
            "powered_by":  "IBM watsonx Orchestrate",
            "docs":        "/health",
            "timestamp":   datetime.utcnow().isoformat() + "Z",
        }), 200

    # ─── GET /health ──────────────────────────────────────────────
    @app.route("/health", methods=["GET"])
    def health():
        """
        Health check endpoint.
        Returns service status and IBM watsonx connectivity information.
        """
        orchestrate_status = orchestrate.ping()
        overall = "healthy" if orchestrate_status["connected"] else "degraded"

        return jsonify({
            "status":      overall,
            "service":     "Scholar AI Backend",
            "timestamp":   datetime.utcnow().isoformat() + "Z",
            "components": {
                "flask_api":   "healthy",
                "watsonx":     orchestrate_status,
            },
        }), 200 if overall == "healthy" else 503

    # ─── POST /chat ───────────────────────────────────────────────
    @app.route("/chat", methods=["POST"])
    def chat():
        """
        Main chat endpoint.

        Request body (JSON):
            {
              "message": "What is quantum computing?",
              "history": [                           // optional
                {"role": "user",  "content": "…"},
                {"role": "ai",    "content": "…"}
              ]
            }

        Returns:
            {
              "reply":   "…AI response…",
              "model":   "ibm-granite-…",
              "latency_ms": 450
            }
        """
        # ── Validate request ──────────────────────────────────────
        if not request.is_json:
            return jsonify({"error": "Request must be JSON (Content-Type: application/json)"}), 415

        body = request.get_json(silent=True)
        if not body:
            return jsonify({"error": "Empty or malformed JSON body"}), 400

        message = body.get("message", "").strip()
        if not message:
            return jsonify({"error": "Field 'message' is required and cannot be empty"}), 422

        if len(message) > 4000:
            return jsonify({"error": "Message exceeds maximum length of 4000 characters"}), 422

        history = body.get("history", [])
        if not isinstance(history, list):
            return jsonify({"error": "Field 'history' must be an array"}), 422

        # ── Call IBM watsonx Orchestrate ──────────────────────────
        t0 = time.time()
        try:
            result = orchestrate.chat(message=message, history=history)
        except ValueError as e:
            logger.warning("Validation error in orchestrate.chat: %s", e)
            return jsonify({"error": str(e)}), 422
        except Exception as e:
            logger.exception("Unexpected error calling Orchestrate service: %s", e)
            return jsonify({
                "error":   "An internal error occurred while processing your request.",
                "detail":  str(e) if app.config.get("DEBUG") else None,
            }), 500

        latency_ms = round((time.time() - t0) * 1000)

        return jsonify({
            "reply":       result.get("reply", ""),
            "model":       result.get("model", "unknown"),
            "latency_ms":  latency_ms,
        }), 200

    # ─── 404 & 405 handlers ───────────────────────────────────────
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Endpoint not found", "path": request.path}), 404

    @app.errorhandler(405)
    def method_not_allowed(e):
        return jsonify({
            "error":   "Method not allowed",
            "method":  request.method,
            "path":    request.path,
        }), 405

    @app.errorhandler(500)
    def internal_error(e):
        logger.exception("Unhandled 500 error: %s", e)
        return jsonify({"error": "Internal server error"}), 500

    logger.info("Scholar AI backend created. Environment: %s", cfg.FLASK_ENV)
    return app


# ─── Entry point ─────────────────────────────────────────────────
if __name__ == "__main__":
    config = Config()
    app    = create_app(config)
    app.run(
        host=config.HOST,
        port=config.PORT,
        debug=config.DEBUG,
    )

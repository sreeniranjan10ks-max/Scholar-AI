"""
Scholar AI — config.py
Application configuration loaded from environment variables.
Uses python-dotenv to support a .env file in development.
──────────────────────────────────────────────────────────────────
Never hardcode credentials here — use environment variables or
the .env file (which must NOT be committed to version control).
──────────────────────────────────────────────────────────────────
"""

import os
import logging
from pathlib import Path

# Load .env file if it exists (development convenience)
try:
    from dotenv import load_dotenv
    _env_path = Path(__file__).parent / ".env"
    if _env_path.exists():
        load_dotenv(_env_path)
        logging.getLogger(__name__).info(".env loaded from %s", _env_path)
except ImportError:
    pass  # python-dotenv not installed; rely on OS environment


class Config:
    """
    Centralised configuration class.

    All values are read from environment variables.  Defaults are
    safe for local development but should be overridden in production.
    """

    # ── Flask core ────────────────────────────────────────────────
    SECRET_KEY: str  = os.getenv("SECRET_KEY", "dev-secret-change-in-production")
    FLASK_ENV:  str  = os.getenv("FLASK_ENV", "development")
    DEBUG:      bool = os.getenv("DEBUG", "false").lower() == "true"

    # ── Server binding ────────────────────────────────────────────
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "5000"))

    # ── CORS ──────────────────────────────────────────────────────
    # Comma-separated list of allowed origins, e.g.
    #   CORS_ORIGINS=http://localhost:3000,https://my-app.com
    _cors_raw: str = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000,null")
    CORS_ORIGINS: list[str] = [o.strip() for o in _cors_raw.split(",") if o.strip()]

    # ── IBM watsonx Orchestrate ───────────────────────────────────
    WATSONX_API_KEY:      str = os.getenv("WATSONX_API_KEY", "")
    WATSONX_PROJECT_ID:   str = os.getenv("WATSONX_PROJECT_ID", "")
    WATSONX_REGION:       str = os.getenv("WATSONX_REGION", "us-south")
    WATSONX_MODEL_ID:     str = os.getenv("WATSONX_MODEL_ID", "ibm/granite-13b-chat-v2")
    WATSONX_API_VERSION:  str = os.getenv("WATSONX_API_VERSION", "2024-05-31")

    # Constructed endpoint (override by setting WATSONX_URL directly)
    WATSONX_URL: str = os.getenv(
        "WATSONX_URL",
        f"https://{os.getenv('WATSONX_REGION', 'us-south')}.ml.cloud.ibm.com",
    )

    # ── IBM IAM (token exchange) ──────────────────────────────────
    IBM_IAM_URL: str = os.getenv("IBM_IAM_URL", "https://iam.cloud.ibm.com/identity/token")

    # ── Generation parameters ─────────────────────────────────────
    MAX_NEW_TOKENS:   int   = int(os.getenv("MAX_NEW_TOKENS",   "800"))
    MIN_NEW_TOKENS:   int   = int(os.getenv("MIN_NEW_TOKENS",   "20"))
    TEMPERATURE:      float = float(os.getenv("TEMPERATURE",    "0.7"))
    TOP_P:            float = float(os.getenv("TOP_P",          "0.95"))
    REPETITION_PENALTY: float = float(os.getenv("REPETITION_PENALTY", "1.1"))

    # ── Rate limiting (future use) ────────────────────────────────
    RATE_LIMIT_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "30"))

    # ── Logging ───────────────────────────────────────────────────
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    def __repr__(self) -> str:
        return (
            f"<Config env={self.FLASK_ENV!r} "
            f"host={self.HOST}:{self.PORT} "
            f"debug={self.DEBUG} "
            f"model={self.WATSONX_MODEL_ID!r}>"
        )

    def validate(self) -> list[str]:
        """
        Return a list of configuration warnings.
        Called at startup to surface missing credentials early.
        """
        warnings: list[str] = []
        if not self.WATSONX_API_KEY:
            warnings.append("WATSONX_API_KEY is not set — AI responses will be mocked.")
        if not self.WATSONX_PROJECT_ID:
            warnings.append("WATSONX_PROJECT_ID is not set — AI responses will be mocked.")
        if self.SECRET_KEY == "dev-secret-change-in-production" and self.FLASK_ENV == "production":
            warnings.append("SECRET_KEY is using the insecure default in production!")
        return warnings

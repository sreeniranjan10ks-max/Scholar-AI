"""
Scholar AI — services/orchestrate.py
IBM watsonx Orchestrate integration service.
──────────────────────────────────────────────────────────────────
This module handles:
  - IBM IAM token exchange (API key → Bearer token)
  - Token caching with expiry
  - Building research-focused system prompts
  - Calling the watsonx /ml/v1/text/generation endpoint
  - Graceful fallback (mock mode) when credentials are absent

IBM watsonx API docs:
  https://cloud.ibm.com/apidocs/watsonx-ai
──────────────────────────────────────────────────────────────────
"""

from __future__ import annotations

import logging
import time
from typing import Any

import requests

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════════
# SYSTEM PROMPT
# ══════════════════════════════════════════════════════════════════

SYSTEM_PROMPT = """You are Scholar AI, an expert academic research assistant powered by IBM watsonx Orchestrate.

Your capabilities include:
- Summarising academic papers with precision and clarity
- Explaining complex research concepts in accessible language
- Generating properly formatted citations (APA, MLA, IEEE, Chicago)
- Finding relevant academic sources and references
- Identifying research trends and key authors in any field
- Cross-referencing facts from multiple authoritative sources

Behaviour guidelines:
- Be concise yet thorough — prioritise signal over noise
- Always acknowledge uncertainty; never fabricate citations or facts
- Structure responses with clear headings and bullet points where helpful
- Cite sources when making factual claims about research
- If a question is outside academic research, politely redirect

Tone: Professional, knowledgeable, approachable, and helpful."""


# ══════════════════════════════════════════════════════════════════
# MOCK RESPONSES (used when credentials are not configured)
# ══════════════════════════════════════════════════════════════════

MOCK_RESPONSES: dict[str, str] = {
    "default": (
        "**Scholar AI (Demo Mode)**\n\n"
        "I'm running in demo mode because IBM watsonx credentials are not yet configured.\n\n"
        "To enable real AI responses:\n"
        "1. Copy `backend/.env.example` → `backend/.env`\n"
        "2. Add your `WATSONX_API_KEY` and `WATSONX_PROJECT_ID`\n"
        "3. Restart the Flask server\n\n"
        "In production, I'll provide comprehensive research assistance powered by IBM's "
        "enterprise-grade language models."
    ),
    "summarise": (
        "**Paper Summary (Demo Mode)**\n\n"
        "In a live environment, I would provide a structured summary including:\n\n"
        "• **Objective** — The research question or hypothesis\n"
        "• **Methodology** — How the study was conducted\n"
        "• **Key Findings** — Principal results and data\n"
        "• **Conclusions** — Implications and future work\n"
        "• **Citations** — Related works referenced\n\n"
        "*Configure your IBM watsonx API key to enable real paper summarisation.*"
    ),
    "citation": (
        "**Citation Generator (Demo Mode)**\n\n"
        "Example APA citation:\n"
        "> Vaswani, A., Shazeer, N., Parmar, N., et al. (2017). "
        "Attention is all you need. *Advances in Neural Information Processing Systems*, 30.\n\n"
        "*Configure your IBM watsonx API key to generate citations for any paper.*"
    ),
}


# ══════════════════════════════════════════════════════════════════
# ORCHESTRATE SERVICE
# ══════════════════════════════════════════════════════════════════

class OrchestrateService:
    """
    Encapsulates all IBM watsonx Orchestrate API interactions.

    When WATSONX_API_KEY / WATSONX_PROJECT_ID are absent, the service
    operates in mock mode and returns demo responses so the frontend
    remains fully functional during development.
    """

    # IBM IAM token expires in 3600s; refresh 5 minutes early
    _TOKEN_REFRESH_BUFFER = 300

    def __init__(self, config) -> None:
        self._cfg           = config
        self._access_token: str  = ""
        self._token_expiry: float = 0.0
        self._mock_mode: bool = not (config.WATSONX_API_KEY and config.WATSONX_PROJECT_ID)

        # Log warnings from config validation
        for w in config.validate():
            logger.warning("Config warning: %s", w)

        if self._mock_mode:
            logger.info(
                "OrchestrateService running in MOCK mode. "
                "Set WATSONX_API_KEY and WATSONX_PROJECT_ID to enable real AI."
            )
        else:
            logger.info(
                "OrchestrateService initialised. Model: %s | Region: %s",
                config.WATSONX_MODEL_ID,
                config.WATSONX_REGION,
            )

    # ──────────────────────────────────────────────────────────────
    # Public API
    # ──────────────────────────────────────────────────────────────

    def ping(self) -> dict[str, Any]:
        """
        Check connectivity to IBM watsonx.
        Used by the /health endpoint.
        """
        if self._mock_mode:
            return {"connected": False, "mode": "mock", "reason": "Credentials not configured"}

        try:
            token = self._get_token()
            return {
                "connected": bool(token),
                "mode":      "live",
                "model":     self._cfg.WATSONX_MODEL_ID,
                "region":    self._cfg.WATSONX_REGION,
            }
        except Exception as e:
            logger.warning("watsonx ping failed: %s", e)
            return {"connected": False, "mode": "live", "reason": str(e)}

    def chat(self, message: str, history: list[dict] | None = None) -> dict[str, Any]:
        """
        Send a message to IBM watsonx and return the reply.

        Args:
            message: The user's research question.
            history: Conversation history — list of
                     {"role": "user"|"ai", "content": "…"}.

        Returns:
            {"reply": "…", "model": "…"}
        """
        if self._mock_mode:
            return self._mock_reply(message)

        prompt = self._build_prompt(message, history or [])

        try:
            token = self._get_token()
            reply = self._generate(prompt, token)
            return {"reply": reply, "model": self._cfg.WATSONX_MODEL_ID}
        except Exception as e:
            logger.exception("Error calling watsonx generate API: %s", e)
            raise

    # ──────────────────────────────────────────────────────────────
    # IBM IAM — Token management
    # ──────────────────────────────────────────────────────────────

    def _get_token(self) -> str:
        """Return a valid IBM IAM Bearer token, refreshing if expired."""
        if self._access_token and time.time() < self._token_expiry:
            return self._access_token

        logger.debug("Requesting new IBM IAM token…")
        resp = requests.post(
            self._cfg.IBM_IAM_URL,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={
                "grant_type": "urn:ibm:params:oauth:grant-type:apikey",
                "apikey":     self._cfg.WATSONX_API_KEY,
            },
            timeout=15,
        )
        resp.raise_for_status()
        token_data = resp.json()

        self._access_token = token_data["access_token"]
        # expires_in is in seconds; subtract buffer for safety
        self._token_expiry = time.time() + token_data.get("expires_in", 3600) - self._TOKEN_REFRESH_BUFFER

        logger.debug("IBM IAM token refreshed. Expires in ~%ds.", token_data.get("expires_in", 3600))
        return self._access_token

    # ──────────────────────────────────────────────────────────────
    # watsonx text generation
    # ──────────────────────────────────────────────────────────────

    def _generate(self, prompt: str, token: str) -> str:
        """Call the watsonx /ml/v1/text/generation endpoint."""
        url = (
            f"{self._cfg.WATSONX_URL}/ml/v1/text/generation"
            f"?version={self._cfg.WATSONX_API_VERSION}"
        )
        payload = {
            "model_id":   self._cfg.WATSONX_MODEL_ID,
            "project_id": self._cfg.WATSONX_PROJECT_ID,
            "input":      prompt,
            "parameters": {
                "max_new_tokens":     self._cfg.MAX_NEW_TOKENS,
                "min_new_tokens":     self._cfg.MIN_NEW_TOKENS,
                "temperature":        self._cfg.TEMPERATURE,
                "top_p":              self._cfg.TOP_P,
                "repetition_penalty": self._cfg.REPETITION_PENALTY,
                "stop_sequences":     ["Human:", "User:"],
            },
        }
        resp = requests.post(
            url,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type":  "application/json",
                "Accept":        "application/json",
            },
            json=payload,
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()

        # Extract generated text from watsonx response schema
        results = data.get("results", [])
        if results:
            return results[0].get("generated_text", "").strip()

        logger.warning("Unexpected watsonx response structure: %s", data)
        return "I was unable to generate a response. Please try again."

    # ──────────────────────────────────────────────────────────────
    # Prompt builder
    # ──────────────────────────────────────────────────────────────

    def _build_prompt(self, message: str, history: list[dict]) -> str:
        """
        Construct an instruction-following prompt with conversation history.
        Uses Granite / LLAMA-style formatting.
        """
        lines = [f"[SYSTEM]\n{SYSTEM_PROMPT}\n"]

        # Append conversation history (last 10 turns max)
        for turn in history[-10:]:
            role    = turn.get("role", "user")
            content = turn.get("content", "").strip()
            if role == "user":
                lines.append(f"Human: {content}")
            else:
                lines.append(f"Assistant: {content}")

        lines.append(f"Human: {message}")
        lines.append("Assistant:")
        return "\n".join(lines)

    # ──────────────────────────────────────────────────────────────
    # Mock mode
    # ──────────────────────────────────────────────────────────────

    def _mock_reply(self, message: str) -> dict[str, Any]:
        """Return a canned response when running in mock mode."""
        msg_lower = message.lower()
        if any(k in msg_lower for k in ("summar", "paper", "abstract")):
            reply = MOCK_RESPONSES["summarise"]
        elif any(k in msg_lower for k in ("cit", "reference", "apa", "mla", "ieee")):
            reply = MOCK_RESPONSES["citation"]
        else:
            reply = MOCK_RESPONSES["default"]

        return {"reply": reply, "model": "mock (demo mode)"}

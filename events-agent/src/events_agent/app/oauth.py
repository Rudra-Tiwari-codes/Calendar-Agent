from __future__ import annotations

import secrets
import time
from typing import Dict

from fastapi import APIRouter, HTTPException, Query
from starlette.responses import JSONResponse, RedirectResponse

from ..infra.crypto import encrypt_text
from ..infra.logging import get_logger
from ..infra.settings import settings


router = APIRouter()
logger = get_logger().bind(service="http")

_state_cache: Dict[str, float] = {}


def _make_state(discord_id: str) -> str:
    nonce = secrets.token_urlsafe(16)
    state = f"{discord_id}:{nonce}"
    _state_cache[state] = time.time() + 300
    return state


def _consume_state(state: str) -> str:
    exp = _state_cache.get(state)
    if not exp or exp < time.time():
        raise HTTPException(status_code=400, detail="invalid_state")
    del _state_cache[state]
    discord_id = state.split(":", 1)[0]
    return discord_id


@router.get("/oauth/start")
async def oauth_start(discord_id: str = Query(...)) -> JSONResponse:
    if not settings.google_client_id or not settings.oauth_redirect_uri:
        raise HTTPException(status_code=500, detail="oauth_not_configured")
    state = _make_state(discord_id)
    params = {
        "response_type": "code",
        "client_id": settings.google_client_id,
        "redirect_uri": settings.oauth_redirect_uri,
        "scope": "openid email https://www.googleapis.com/auth/calendar",
        "access_type": "offline",
        "prompt": "consent",
        "state": state,
    }
    from urllib.parse import urlencode

    url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"
    return JSONResponse({"url": url, "state": state})


@router.get("/oauth/callback")
async def oauth_callback(code: str, state: str) -> JSONResponse:
    discord_id = _consume_state(state)
    # Placeholder: store encrypted code as a stand-in for tokens.
    ciphertext = encrypt_text(code)
    logger.info("oauth_linked", discord_id=discord_id)
    return JSONResponse({"ok": True})



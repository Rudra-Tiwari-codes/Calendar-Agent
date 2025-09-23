from __future__ import annotations

import secrets
import time
from typing import Dict

from fastapi import APIRouter, HTTPException, Query
from starlette.responses import JSONResponse, RedirectResponse
from pydantic import BaseModel

from ..infra.crypto import encrypt_text
from ..infra.logging import get_logger
from ..infra.settings import settings


router = APIRouter()
logger = get_logger().bind(service="http")

_state_cache: Dict[str, float] = {}
_token_cache: Dict[str, str] = {}


class TokenRequest(BaseModel):
    access_token: str
    state: str
    provider: str


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
    if not settings.google_client_id:
        raise HTTPException(status_code=500, detail="google_oauth_not_configured")
    
    state = _make_state(discord_id)
    
    # Use direct Google OAuth (simpler and more reliable)
    # Get the base URL from settings or environment
    base_url = getattr(settings, 'base_url', None) or f"http://localhost:{settings.http_port}"
    redirect_uri = f"{base_url}/auth/success"
    
    params = {
        "response_type": "token",  # Use implicit flow for direct token
        "client_id": settings.google_client_id,
        "redirect_uri": redirect_uri,
        "scope": "openid email https://www.googleapis.com/auth/calendar https://www.googleapis.com/auth/calendar.events",
        "access_type": "offline",
        "prompt": "consent",
        "state": state,
    }
    from urllib.parse import urlencode

    url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"
    logger.info("oauth_url_generated", url=url, discord_id=discord_id)
    return JSONResponse({"url": url, "state": state})


@router.get("/oauth/callback")
async def oauth_callback(code: str, state: str) -> JSONResponse:
    discord_id = _consume_state(state)
    # Placeholder: store encrypted code as a stand-in for tokens.
    ciphertext = encrypt_text(code)
    logger.info("oauth_linked", discord_id=discord_id)
    return JSONResponse({"ok": True})


@router.post("/oauth/token")
async def receive_token(token_request: TokenRequest) -> JSONResponse:
    """Receive access token from frontend auth success page"""
    try:
        # Validate state and get discord_id
        discord_id = _consume_state(token_request.state)
        
        # Store the encrypted access token
        encrypted_token = encrypt_text(token_request.access_token)
        _token_cache[discord_id] = encrypted_token
        
        logger.info("oauth_token_received", 
                   discord_id=discord_id, 
                   provider=token_request.provider)
        
        return JSONResponse({
            "ok": True, 
            "message": "Token saved successfully",
            "discord_id": discord_id
        })
        
    except HTTPException as e:
        logger.error("oauth_token_error", error=str(e.detail))
        raise e
    except Exception as e:
        logger.error("oauth_token_unexpected_error", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to process token")



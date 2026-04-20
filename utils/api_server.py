from __future__ import annotations

import os
import secrets
from pathlib import Path
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from core.behavior_monitor import tagged_users
from core.deception_engine import user_count
from utils.config_manager import load_rules


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")


def _load_api_config() -> dict[str, Any]:
    config_path = os.getenv("GGS_CONFIG_PATH", "config.yaml")
    config = load_rules(config_path)
    return config.get("api", {})


API_CONFIG = _load_api_config()
_SERVICE_ACCOUNTS = {
    account.get("username"): account.get("password")
    for account in API_CONFIG.get("service_accounts", [])
    if account.get("username")
}
_STATIC_TOKENS = set(API_CONFIG.get("tokens", []) or [])
_ISSUED_TOKENS: dict[str, str] = {}


def _verify_token(token: str) -> str:
    if token in _STATIC_TOKENS:
        return "static-token-client"
    username = _ISSUED_TOKENS.get(token)
    if username:
        return username
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token invalido o expirado",
        headers={"WWW-Authenticate": "Bearer"},
    )


def require_authenticated_user(token: str = Depends(oauth2_scheme)) -> str:
    return _verify_token(token)


app = FastAPI(title="Guardian Graph API", version="1.0.0")


@app.post("/token")
def token(form_data: OAuth2PasswordRequestForm = Depends()) -> dict[str, str]:
    username = form_data.username
    expected_password = _SERVICE_ACCOUNTS.get(username)
    if not expected_password or not secrets.compare_digest(expected_password, form_data.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales invalidas",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = secrets.token_urlsafe(32)
    _ISSUED_TOKENS[access_token] = username
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/v1/health")
def health(_: str = Depends(require_authenticated_user)) -> dict[str, str]:
    return {"status": "ok"}


@app.get("/v1/risk")
def risk(_: str = Depends(require_authenticated_user)) -> dict[str, Any]:
    risk_levels, scores = user_count()
    return {
        "risk_levels": risk_levels,
        "scores": dict(scores),
        "tagged_users": tagged_users,
    }


@app.get("/v1/alerts")
def alerts(limit: int = 100, _: str = Depends(require_authenticated_user)) -> dict[str, Any]:
    config = load_rules(os.getenv("GGS_CONFIG_PATH", "config.yaml"))
    log_path = Path(config.get("log_file", "system_events.log"))
    entries: list[dict[str, Any]] = []
    if log_path.exists():
        with log_path.open("r", encoding="utf-8") as f:
            lines = [line.strip() for line in f.readlines() if line.strip()]
        for raw in lines[-max(1, min(limit, 1000)) :]:
            try:
                import json

                entries.append(json.loads(raw))
            except Exception:
                entries.append({"message": raw, "event_type": "raw"})
    return {"count": len(entries), "items": entries}


def run_api_server(host: str = "0.0.0.0", port: int = 8080) -> None:
    import uvicorn

    uvicorn.run(app, host=host, port=port)

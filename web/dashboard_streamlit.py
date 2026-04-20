from __future__ import annotations

import datetime as dt
from typing import Any

import requests
import streamlit as st


DEFAULT_API_BASE = "http://localhost:8080"
DEFAULT_ALERT_LIMIT = 100
DEFAULT_REFRESH_SECONDS = 5


def _token_headers(token: str | None) -> dict[str, str]:
    if not token:
        return {}
    return {"Authorization": f"Bearer {token}"}


def _request_token(api_base: str, username: str, password: str) -> str:
    response = requests.post(
        f"{api_base.rstrip('/')}/token",
        data={"username": username, "password": password},
        timeout=5,
    )
    response.raise_for_status()
    payload = response.json()
    return payload["access_token"]


def _fetch_alerts(api_base: str, token: str, limit: int) -> dict[str, Any]:
    response = requests.get(
        f"{api_base.rstrip('/')}/v1/alerts",
        params={"limit": limit},
        headers=_token_headers(token),
        timeout=5,
    )
    response.raise_for_status()
    return response.json()


def _fetch_risk(api_base: str, token: str) -> dict[str, Any]:
    response = requests.get(
        f"{api_base.rstrip('/')}/v1/risk",
        headers=_token_headers(token),
        timeout=5,
    )
    response.raise_for_status()
    return response.json()


def _logout() -> None:
    st.session_state.pop("ggs_token", None)
    st.session_state.pop("ggs_user", None)


def _login_form(api_base: str) -> None:
    with st.form("auth_form", clear_on_submit=False):
        username = st.text_input("API username", value="guardian_api")
        password = st.text_input("API password", type="password")
        submitted = st.form_submit_button("Sign in")

    if submitted:
        try:
            token = _request_token(api_base, username, password)
            st.session_state["ggs_token"] = token
            st.session_state["ggs_user"] = username
            st.success("Authenticated")
            st.rerun()
        except requests.RequestException as exc:
            st.error(f"Authentication failed: {exc}")


def _render_risk_panel(risk_payload: dict[str, Any]) -> None:
    risk_levels = risk_payload.get("risk_levels", {})
    scores = risk_payload.get("scores", {})

    rows: list[dict[str, Any]] = []
    users = sorted(set(risk_levels.keys()) | set(scores.keys()))
    for user in users:
        rows.append(
            {
                "user": user,
                "risk_level": risk_levels.get(user, "N/A"),
                "score": scores.get(user, 0),
            }
        )

    st.subheader("Current risk by user")
    if rows:
        st.dataframe(rows, use_container_width=True, hide_index=True)
    else:
        st.info("No risk data available yet.")


def _render_alerts_panel(alert_payload: dict[str, Any]) -> None:
    items = alert_payload.get("items", [])
    st.subheader("Recent alerts")
    st.caption(f"Total returned: {alert_payload.get('count', 0)}")

    if not items:
        st.info("No alerts found.")
        return

    table_rows: list[dict[str, Any]] = []
    for item in reversed(items):
        context = item.get("context", {}) if isinstance(item, dict) else {}
        table_rows.append(
            {
                "timestamp": item.get("timestamp", ""),
                "level": item.get("level", ""),
                "event_type": item.get("event_type", ""),
                "source": item.get("source", ""),
                "message": item.get("message", ""),
                "username": context.get("username", ""),
                "process_name": context.get("process_name", ""),
            }
        )

    st.dataframe(table_rows, use_container_width=True, hide_index=True)

    with st.expander("Raw JSON payload"):
        st.json(items)


def main() -> None:
    st.set_page_config(page_title="Guardian Graph Live Dashboard", page_icon="GGS", layout="wide")

    st.title("Guardian Graph Live Dashboard")
    st.caption("Live API consumer for /v1/alerts and /v1/risk")

    with st.sidebar:
        st.header("Connection")
        api_base = st.text_input("API base URL", value=DEFAULT_API_BASE)
        refresh_seconds = st.number_input(
            "Refresh interval (seconds)",
            min_value=2,
            max_value=60,
            value=DEFAULT_REFRESH_SECONDS,
            step=1,
        )
        alert_limit = st.number_input(
            "Alerts limit",
            min_value=10,
            max_value=1000,
            value=DEFAULT_ALERT_LIMIT,
            step=10,
        )

        if st.button("Sign out"):
            _logout()
            st.rerun()

    token = st.session_state.get("ggs_token")
    if not token:
        st.info("Authenticate to start consuming protected endpoints.")
        _login_form(api_base)
        return

    st.markdown(f"<meta http-equiv='refresh' content='{int(refresh_seconds)}'>", unsafe_allow_html=True)

    col_left, col_right = st.columns(2)

    try:
        alerts = _fetch_alerts(api_base, token, int(alert_limit))
        risk = _fetch_risk(api_base, token)
    except requests.RequestException as exc:
        st.error(f"Failed to fetch data from API: {exc}")
        if st.button("Re-authenticate"):
            _logout()
            st.rerun()
        return

    with col_left:
        _render_alerts_panel(alerts)

    with col_right:
        _render_risk_panel(risk)

    last_update = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    st.caption(f"Last update: {last_update}")


if __name__ == "__main__":
    main()

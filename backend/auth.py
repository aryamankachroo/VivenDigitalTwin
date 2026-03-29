"""Google OAuth 2.0 helpers."""

from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials

import config


def get_flow(
    state: str | None = None,
    code_verifier: str | None = None,
) -> Flow:
    """Build Flow. Pass ``code_verifier`` on callback (same value as login step)."""
    kwargs: dict = {
        "redirect_uri": config.GOOGLE_REDIRECT_URI,
    }
    if state is not None:
        kwargs["state"] = state
    if code_verifier is not None:
        kwargs["code_verifier"] = code_verifier
        kwargs["autogenerate_code_verifier"] = False
    return Flow.from_client_secrets_file(
        str(config.CREDENTIALS_FILE),
        scopes=config.SCOPES,
        **kwargs,
    )


def get_auth_url() -> tuple[str, str, str]:
    """Returns (authorization_url, state, code_verifier).

    The verifier must be stored server-side and reused on token exchange (PKCE).
    """
    flow = get_flow()
    auth_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )
    verifier = flow.code_verifier or ""
    if not verifier:
        raise RuntimeError("PKCE code_verifier was not generated")
    return auth_url, state, verifier


def credentials_from_callback(
    request_url: str, expected_state: str, code_verifier: str
) -> dict:
    """Exchange authorization response for credentials; validates OAuth state."""
    flow = get_flow(state=expected_state, code_verifier=code_verifier)
    flow.fetch_token(authorization_response=request_url)
    return credentials_to_dict(flow.credentials)


def credentials_to_dict(credentials: Credentials) -> dict:
    return {
        "token": credentials.token,
        "refresh_token": credentials.refresh_token,
        "token_uri": credentials.token_uri,
        "client_id": credentials.client_id,
        "client_secret": credentials.client_secret,
        "scopes": list(credentials.scopes) if credentials.scopes else [],
    }


def credentials_from_session(data: dict) -> Credentials:
    kwargs = {k: v for k, v in data.items() if v is not None}
    return Credentials(**kwargs)

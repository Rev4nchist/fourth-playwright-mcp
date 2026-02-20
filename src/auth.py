"""OAuth 2.1 configuration for Claude.ai Custom Connector."""

import os

from fastmcp.server.auth import OAuthProxy


def create_oauth_proxy() -> OAuthProxy | None:
    """Create OAuth 2.1 proxy if credentials are configured.

    Returns None if OAUTH_CLIENT_ID is not set (allows local dev without auth).
    """
    client_id = os.environ.get("OAUTH_CLIENT_ID")
    if not client_id:
        return None

    client_secret = os.environ.get("OAUTH_CLIENT_SECRET", "")
    base_url = os.environ.get("BASE_URL", "http://127.0.0.1:8000")
    auth_endpoint = os.environ.get(
        "OAUTH_AUTHORIZATION_ENDPOINT",
        "https://accounts.google.com/o/oauth2/v2/auth",
    )
    token_endpoint = os.environ.get(
        "OAUTH_TOKEN_ENDPOINT",
        "https://oauth2.googleapis.com/token",
    )
    scopes = os.environ.get("OAUTH_SCOPES", "openid email profile").split()

    return OAuthProxy(
        upstream_authorization_endpoint=auth_endpoint,
        upstream_token_endpoint=token_endpoint,
        upstream_client_id=client_id,
        upstream_client_secret=client_secret,
        base_url=base_url,
        scopes=scopes,
    )

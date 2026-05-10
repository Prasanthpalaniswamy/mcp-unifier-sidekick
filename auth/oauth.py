import os

from authlib.integrations.starlette_client import OAuth


GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET")


def validate_oauth_config() -> None:
    if not GITHUB_CLIENT_ID:
        print("WARNING: GITHUB_CLIENT_ID not configured")

    if not GITHUB_CLIENT_SECRET:
        print("WARNING: GITHUB_CLIENT_SECRET not configured")


oauth = OAuth()

oauth.register(
    name="github",
    client_id=GITHUB_CLIENT_ID,
    client_secret=GITHUB_CLIENT_SECRET,
    access_token_url="https://github.com/login/oauth/access_token",
    authorize_url="https://github.com/login/oauth/authorize",
    api_base_url="https://api.github.com/",
    client_kwargs={
        "scope": "read:user user:email"
    },
)


__all__ = ["oauth", "validate_oauth_config"]
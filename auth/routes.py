from starlette.requests import Request
from starlette.responses import JSONResponse

from .oauth import oauth
from .service import authenticate_user, create_jwt_token


async def login(request: Request):
    body = await request.json()
    username = body.get("username")
    password = body.get("password")

    if not username or not password:
        return JSONResponse({"error": "Username and password are required"}, status_code=400)

    if not authenticate_user(username, password):
        return JSONResponse({"error": "Invalid credentials"}, status_code=401)

    token = create_jwt_token(username)
    return JSONResponse({"access_token": token, "token_type": "bearer"})

async def github_login(request):

    redirect_uri = request.url_for("github_callback")

    return await oauth.github.authorize_redirect(
        request,
        redirect_uri
    )

async def github_callback(request):

    token = await oauth.github.authorize_access_token(request)

    resp = await oauth.github.get(
        "user",
        token=token
    )

    user = resp.json()

    github_username = user["login"]

    jwt_token = create_jwt_token(github_username)

    return JSONResponse({
        "access_token": jwt_token,
        "token_type": "bearer",
        "github_user": github_username
    })


__all__ = ["login", "github_login", "github_callback"]
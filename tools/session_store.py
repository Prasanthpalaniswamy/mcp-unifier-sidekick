from typing import Any

from mcp.server.fastmcp import Context


UNIFIER_SESSIONS: dict[str, dict[str, Any]] = {}


def get_session_key(ctx: Context) -> str:
    if ctx.client_id:
        return f"client:{ctx.client_id}"

    try:
        session = ctx.session
    except Exception:
        session = None

    if session is not None:
        return f"session:{id(session)}"

    return f"request:{ctx.request_id}"
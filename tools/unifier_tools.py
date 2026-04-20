import os
import json
import requests
from pathlib import Path
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv
from typing import TypedDict, Optional

from mcp.server.fastmcp import Context
from tools.session_store import UNIFIER_SESSIONS, get_session_key

def get_session(ctx: Context):
    session = UNIFIER_SESSIONS.get(get_session_key(ctx))
    if not session:
        raise ValueError(
            "⚠️ Unifier session not initialized. Please provide base_url, username, password."
        )
    return session

class UnifierSession(TypedDict):
    base_url: str
    username: str
    password: str
    token: Optional[str]

# -------------------------------
# Load environment variables once
# -------------------------------
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

# BASE_URL = os.getenv("UNIFIER_BASE_URL", "http://169.224.230.179:7001/ws/rest/service/v1")
BASE_URL = os.getenv("UNIFIER_BASE_URL")
USERNAME = os.getenv("UNIFIER_USERNAME")
PASSWORD = os.getenv("UNIFIER_PASSWORD")

# -------------------------------
# Global session + token cache
# -------------------------------
SESSION = requests.Session()
TOKEN = None


# -------------------------------
# Authentication
# -------------------------------
# def get_token(force_refresh=False):
#     global TOKEN
    
#     if force_refresh:
#         TOKEN = None

#     if TOKEN:
#         return TOKEN

#     if not USERNAME or not PASSWORD:
#         raise ValueError("UNIFIER_USERNAME and UNIFIER_PASSWORD must be set")

#     url = f"{BASE_URL}/login"

#     response = SESSION.get(
#         url,
#         auth=HTTPBasicAuth(USERNAME, PASSWORD),
#         timeout=150
#     )

#     response.raise_for_status()

#     data = response.json()
#     TOKEN = data.get("token")

#     if not TOKEN:
#         raise ValueError("Token not found in login response")

#     return TOKEN

#new auth method
def get_token(ctx: Context, force_refresh=False):
    session = get_session(ctx)

    if force_refresh:
        session["token"] = None

    if session.get("token"):
        return session["token"]

    url = f"{session['base_url']}/login"

    response = SESSION.get(
        url,
        auth=HTTPBasicAuth(session["username"], session["password"]),
        timeout=150
    )

    response.raise_for_status()

    token = response.json().get("token")

    if not token:
        raise ValueError("Token not found")

    session["token"] = token
    return token


# -------------------------------
# Helper request function
# -------------------------------
def unifier_get(ctx: Context,endpoint, params=None):
    session = get_session(ctx)
    token = get_token(ctx)

    headers = {
        "Authorization": f"Bearer {token}"
    }

    url = f"{session['base_url']}{endpoint}"

    response = SESSION.get(
        url,
        headers=headers,
        params=params,
        timeout=150
    )

    if response.status_code == 401:
        # Token might be expired, refresh and retry once
        token = get_token(ctx, force_refresh=True)
        headers["Authorization"] = f"Bearer {token}"
        response = SESSION.get(
            url,
            headers=headers,
            params=params,
            timeout=150
        )

    response.raise_for_status()

    return response.json()



def unifier_post(ctx: Context,endpoint, data):
    token = get_token(ctx)

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }


    session = get_session(ctx)
    url = f"{session['base_url']}{endpoint}"

    response = SESSION.post(
        url,
        headers=headers,
        json=data,
        timeout=150
    )

    if response.status_code == 401:
        # Token might be expired, refresh and retry once
        token = get_token(ctx, force_refresh=True)
        headers["Authorization"] = f"Bearer {token}"
        response = SESSION.post(
            url,
            headers=headers,
            json=data,
            timeout=150
        )

    response.raise_for_status()

    return response.json()


# -------------------------------
# Unifier API Wrappers
# -------------------------------
def get_projects(ctx: Context, shell_type="Projects", limit=None, offset=0):
    options = {
        "filter": {
            "shell_type": shell_type
        }
    }

    # Pass limit/offset server-side so Unifier returns only what we need
    if limit is not None:
        options["limit"] = limit
        options["offset"] = offset

    params = {
        "options": json.dumps(options)
    }

    result = unifier_get(ctx,"/admin/shell", params=params)

    # Also apply client-side pagination as a fallback (in case API ignores limit/offset)
    data = result.get("data", [])
    if limit is not None and len(data) > limit:
        total = len(data)
        result["data"] = data[offset : offset + limit]
        result["pagination"] = {
            "total": total,
            "limit": limit,
            "offset": offset,
            "count": len(result["data"])
        }
    return result


# def get_project_cost(project_id):
#     return unifier_get(f"/projects/{project_id}/cost")


# def get_rfis(project_id):
#     return unifier_get(f"/projects/{project_id}/rfis")


def get_data_elements(ctx: Context, filter_options=None, limit=None, offset=0):
    """
    Fetch data elements from Unifier.
    filter_options: dict containing data_element, data_definition, form_label, description, tooltip
    """
    params = {}
    if filter_options:
        params["filter"] = json.dumps(filter_options)

    result = unifier_get(ctx,"/ds/data-elements", params=params)
    
    # Client-side pagination if limit is specified
    if limit is not None:
        data = result.get("data", [])
        total = len(data)
        result["data"] = data[offset : offset + limit]
        result["pagination"] = {
            "total": total,
            "limit": limit,
            "offset": offset,
            "count": len(result["data"])
        }
    return result


def get_data_definitions(ctx: Context, df_type=None, filter_options=None, limit=None, offset=0):
    """
    Fetch data definitions from Unifier.
    df_type: Basic, Cost Codes, Data Picker
    filter_options: dict containing name, data_source
    """
    params = {}
    if df_type:
        params["type"] = df_type
    if filter_options:
        params["filter"] = json.dumps(filter_options)

    result = unifier_get(ctx,"/ds/data-def", params=params)
    
    # Client-side pagination if limit is specified
    if limit is not None:
        data = result.get("data", [])
        total = len(data)
        result["data"] = data[offset : offset + limit]
        result["pagination"] = {
            "total": total,
            "limit": limit,
            "offset": offset,
            "count": len(result["data"])
        }
    return result





def get_users(ctx: Context, filter_condition=None, limit=None, offset=0):
    """
    Fetch users from Unifier.
    Uses POST /ws/rest/service/v1/admin/user/get
    """
    payload = {}
    if filter_condition:
        payload["filterCondition"] = filter_condition

    result = unifier_post(ctx,"/admin/user/get", data=payload)
    
    # Client-side pagination if limit is specified
    if limit is not None:
        data = result.get("data", [])
        total = len(data)
        result["data"] = data[offset : offset + limit]
        result["pagination"] = {
            "total": total,
            "limit": limit,
            "offset": offset,
            "count": len(result["data"])
        }
    return result


def get_bp_records(ctx: Context, bpname: str, project_number: str = None, options: dict = None, limit: int = None, offset: int = 0):
    """
    Fetch BP records from Unifier. 
    If project_number is provided, fetches Project level records. Else Company level.
    Uses POST /ws/rest/service/v1/bp/records/{project_number}
    """
    if project_number:
        endpoint = f"/bp/records/{project_number}"
    else:
        endpoint = "/bp/records"
        
    payload = {"bpname": bpname}
    if options:
        payload.update(options)

    result = unifier_post(ctx,endpoint, data=payload)
    
    # Client-side pagination if limit is specified
    if limit is not None:
        data = result.get("data", [])
        total = len(data)
        result["data"] = data[offset : offset + limit]
        result["pagination"] = {
            "total": total,
            "limit": limit,
            "offset": offset,
            "count": len(result["data"])
        }
    return result


def create_data_elements(ctx: Context,elements_list):
    """
    Create custom data elements in Unifier.
    elements_list: list of dicts containing data_element, data_definition, form_label, etc.
    """
    data = {
        "data": elements_list
    }
    return unifier_post(ctx,"/ds/data-elements", data=data)
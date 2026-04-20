import os
from datetime import datetime
from contextlib import asynccontextmanager
import pandas as pd
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route, Mount
from mcp.server.fastmcp import FastMCP
# from tools.base64_tools import encode_credentials, decode_credentials
# from tools.unifier_tools import create_data_elements, get_data_definitions, get_data_elements
from tools.unifier_tools import get_projects, get_data_elements, get_data_definitions, create_data_elements, get_users, get_bp_records
from tools.session_store import UNIFIER_SESSIONS, get_session_key
from dotenv import load_dotenv
from mcp.server.fastmcp import Context

# Load variables from .env into the environment
load_dotenv()

mcp = FastMCP("Unifier Tools Server", host="0.0.0.0")


@mcp.tool()
def init_unifier(
    ctx: Context,
    base_url: str,
    username: str,
    password: str
):
    UNIFIER_SESSIONS[get_session_key(ctx)] = {
        "base_url": base_url.rstrip("/"),
        "username": username,
        "password": password,
        "token": None,
    }

    return "✅ Session initialized"

# @mcp.tool(description=(
#     "Convert login credentials into Base64 format.\n\n"
#     "Input:\n"
#     "- login: string (username)\n"
#     "- password: string\n\n"
#     "Output:\n"
#     "- Base64 encoded string of 'login:password'\n\n"
#     "Use case:\n"
#     "- Preparing credentials for HTTP Basic Authentication headers."
# ))
# def encode_credentials_tool(login: str, password: str) -> str:
#     return encode_credentials(login, password)


# @mcp.tool(description=(
#     "Decode Base64-encoded credentials.\n\n"
#     "Input:\n"
#     "- encoded_data: Base64 string representing 'login:password'\n\n"
#     "Output:\n"
#     "- JSON object with:\n"
#     "  - login: string\n"
#     "  - password: string\n\n"
#     "Use case:\n"
#     "- Extracting username and password from encoded credentials."
# ))
# def decode_credentials_tool(encoded_data: str) -> dict:
#     return decode_credentials(encoded_data)


# UNIFIER TOOLS
@mcp.tool()
def list_projects(ctx: Context,shell_type: str = "Projects", limit: int = 50, offset: int = 0):
    """Return list of projects from Unifier"""
    return get_projects(ctx, shell_type=shell_type, limit=limit, offset=offset)
@mcp.tool()
def list_data_elements(
    ctx: Context,        
    data_element: str = None,
    data_definition: str = None,
    form_label: str = None,
    description: str = None,
    tooltip: str = None,
    limit: int = 50,
    offset: int = 0
):
    """
    Return list of custom data elements from Unifier. 
    Filters (case-insensitive) can be applied for data_element name, definition, label, description, or tooltip.
    """
    filter_options = {}
    if data_element: filter_options["data_element"] = data_element
    if data_definition: filter_options["data_definition"] = data_definition
    if form_label: filter_options["form_label"] = form_label
    if description: filter_options["description"] = description
    if tooltip: filter_options["tooltip"] = tooltip
    return get_data_elements(ctx, filter_options=filter_options if filter_options else None, limit=limit, offset=offset)
@mcp.tool()
def list_data_definitions(
    ctx: Context,
    df_type: str = None,
    name: str = None,
    data_source: str = None,
    limit: int = 50,
    offset: int = 0
):
    """
    Return list of data definitions from Unifier.
    df_type: Possible values are Basic, Cost Codes, Data Picker (case-insensitive).
    name: Name of the Data definition.
    data_source: Data source of the data picker (only for Data Picker type).
    """
    filter_options = {}
    if name: filter_options["name"] = name
    if data_source: filter_options["data_source"] = data_source
    return get_data_definitions(ctx, df_type=df_type, filter_options=filter_options if filter_options else None, limit=limit, offset=offset)
@mcp.tool()
def create_data_element(
    ctx: Context,
    data_element: str,
    data_definition: str,
    form_label: str,
    description: str = None,
    tooltip: str = None,
    decimal_format: str = "2",
    height: str = None,
    no_of_lines: str = None,
    hide_currency_symbol: str = "No"
):
    """
    Create a new custom data element in Unifier.
    data_element: Unique name (e.g., 'sampleDE').
    data_definition: Field definition to use (e.g., 'Decimal Amount').
    form_label: Label name.
    decimal_format: For 'Decimal Amount' (default '2').
    height: For 'Image Picker' or 'SYS Rich Text'.
    no_of_lines: For 'textarea'.
    hide_currency_symbol: For 'SYS Numeric Query Based' (Yes/No).
    """
    element_data = {
        "data_element": data_element,
        "data_definition": data_definition,
        "form_label": form_label
    }
    if description: element_data["description"] = description
    if tooltip: element_data["tooltip"] = tooltip
    
    if data_definition == "Decimal Amount":
        element_data["decimal_format"] = decimal_format
    elif data_definition in ["Image Picker", "SYS Rich Text"]:
        if height: element_data["height"] = height
    elif data_definition == "textarea":
        if no_of_lines: element_data["no_of_lines"] = no_of_lines
    elif data_definition == "SYS Numeric Query Based":
        element_data["hide_currency_symbol"] = hide_currency_symbol
    return create_data_elements(ctx,[element_data])

@mcp.tool()
def bulk_create_data_elements_from_excel(ctx: Context, file_path: str) -> str:
    """
    Read data elements from an Excel file and create them in Unifier in bulk.
    Generates an 'api_response.xlsx' report in the same directory as the input file.
    
    file_path: Absolute path to the Excel file containing the 'DataElementCR_Inp' sheet.
    """
    try:
        df = pd.read_excel(file_path, sheet_name='DataElementCR_Inp', dtype=str)
        # Replace NaN with empty strings (equivalent to the legacy script's np.nan replacement)
        df = df.fillna('')
        data_records = df.to_dict(orient='records')   
        if not data_records:
            return "No data found in sheet 'DataElementCR_Inp'."

        # Call existing API client
        result = create_data_elements(ctx, data_records)
        
        # Parse response for report generation
        messages = result.get("message", [])
        if not messages:
            return "API call succeeded but no detail messages returned to export."

        records = [
            {
                "Data_Element_Name": msg.get("data_element", ""),
                "Integration_Message": msg.get("message", ""),
                "status_code": msg.get("status", "")
            }
            for msg in messages
        ]
        out_df = pd.DataFrame(records)
        input_dir = os.path.dirname(file_path)
        output_file = os.path.normpath(os.path.join(input_dir, "api_response.xlsx"))
        
        try:
            # Check if file is locked
            with open(output_file, "a"):
                pass
            out_df.to_excel(output_file, index=False)
            report_msg = f"Excel report saved successfully to: {output_file}"
        except PermissionError:
            fallback_name = f"api_response_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            fallback = os.path.normpath(os.path.join(input_dir, fallback_name))
            out_df.to_excel(fallback, index=False)
            report_msg = f"Target file was locked. Saved fallback report to: {fallback}"
        return f"Bulk creation executed. Processed {len(data_records)} records. {report_msg}"
    except Exception as e:
        return f"Error executing bulk creation: {str(e)}"
@mcp.tool()
def list_users(
    ctx: Context,
    filter_condition: str = None,
    limit: int = 50,
    offset: int = 0
):
    """
    Return list of users from Unifier. 
    This uses the POST /admin/user/get endpoint.
    filter_condition: Criteria to filter users (e.g., 'uuu_user_status=1' for active users).
    """
    return get_users(ctx, filter_condition=filter_condition, limit=limit, offset=offset)
@mcp.tool()
def list_bp_records(
    ctx: Context,
    bpname: str,
    project_number: str = None,
    record_fields: str = None,
    filter_condition: str = None,
    filter_criteria: str = None,
    fetch_lineitems: bool = False,
    limit: int = 50,
    offset: int = 0
):
    """
    Fetch a list of Business Process (BP) records from a specific project or company level.
    bpname: The name of the BP (e.g., 'Vendors').
    project_number: The project number. If empty, fetches company level BP records.
    record_fields: Semicolon separated list of data element names to return.
    filter_condition: Simple string filter (e.g., 'status=Active').
    filter_criteria: Advanced JSON string for filtering.
    fetch_lineitems: True to return line item details, False defaults to 'no'.
    """
    options = {}
    options["lineitem"] = "yes" if fetch_lineitems else "no"
    
    if record_fields:
        options["record_fields"] = record_fields
    if filter_condition:
        options["filter_condition"] = filter_condition
    if filter_criteria:
        import json
        try:
            options["filter_criteria"] = json.loads(filter_criteria)
        except json.JSONDecodeError:
            options["filter_criteria"] = filter_criteria # Pass as string if parsed fails, let API decide
    return get_bp_records(ctx,bpname=bpname, project_number=project_number, options=options, limit=limit, offset=offset)



async def healthcheck(request):
    return JSONResponse({
        "status": "ok",
        "message": "Unifier MCP Server is running",
        "mcp_endpoint": "/mcp"
    })


mcp_app = mcp.streamable_http_app()


@asynccontextmanager
async def lifespan(app):
    async with mcp.session_manager.run():
        yield

app = Starlette(routes=[
    Route("/health", healthcheck),
    Mount("/", app=mcp_app),
], lifespan=lifespan)


if __name__ == "__main__":
    transport = os.getenv("MCP_TRANSPORT", "http").lower()
    print(f"Starting MCP server with transport: {transport}")

    if transport in ["http", "https"]:
        import uvicorn

        port = int(os.environ.get("PORT", 8000))
        # print(f"MCP HTTP server starting on port {port}...")

        uvicorn.run(
            "server:app",
            host="0.0.0.0",
            port=port,
            proxy_headers=True,
            forwarded_allow_ips="*",
        )
    else:
        mcp.run()

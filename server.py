import os
from datetime import datetime
from contextlib import asynccontextmanager
import pandas as pd
from starlette.applications import Starlette
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import JSONResponse
from starlette.routing import Route, Mount
from mcp.server.fastmcp import FastMCP
# from tools.base64_tools import encode_credentials, decode_credentials
# from tools.unifier_tools import create_data_elements, get_data_definitions, get_data_elements
from tools.unifier_tools import get_projects, get_data_elements, get_data_definitions, create_data_elements, get_users, get_bp_records,validate_base_url,validate_username,validate_password
from tools.supporting_tools import export_content_to_file, export_content_to_pdf, export_content_to_docx, convert_docx_to_pdf_content_based, send_email_via_smtp, compress_files_to_zip, split_file, create_reassembly_instructions
from tools.visualization_tools import generate_chart_image, generate_summary_dashboard, generate_table_image
from tools.session_store import UNIFIER_SESSIONS, get_session_key
from dotenv import load_dotenv
from mcp.server.fastmcp import Context
from auth import (
    AuthMiddleware,
    github_callback,
    github_login,
    login,
)
# from starlette.responses import JSONResponse
# from starlette.responses import JSONResponse



# Load variables from .env into the environment
load_dotenv()
MCP_API_KEY = os.getenv("MCP_API_KEY")
SESSION_SECRET = os.getenv("SESSION_SECRET") or os.getenv("JWT_SECRET") or "dev-session-secret-change-me"
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
SMTP_SENDER_EMAIL = os.getenv("SMTP_SENDER_EMAIL", SMTP_USERNAME or "")

mcp = FastMCP("Unifier Tools Server", host="0.0.0.0")


@mcp.tool()
def init_unifier(
    ctx: Context,
    base_url: str,
    username: str,
    password: str
):
    base_url = validate_base_url(base_url)
    username = validate_username(username)
    password = validate_password(password)
    UNIFIER_SESSIONS[get_session_key(ctx)] = {
        "base_url": base_url,
        "username": username,
        "password": password,
        "token": None,
    }

    return "✅ Session initialized"


@mcp.tool()
def clear_unifier_session(ctx: Context):
    """Clear the currently stored Unifier session for this client/session."""
    session_key = get_session_key(ctx)

    if session_key in UNIFIER_SESSIONS:
        del UNIFIER_SESSIONS[session_key]
        return "✅ Unifier session cleared"

    return "ℹ️ No active Unifier session found"


@mcp.tool()
def get_current_unifier_session(ctx: Context):
    """Return safe details about the current Unifier session without exposing the password."""
    session = UNIFIER_SESSIONS.get(get_session_key(ctx))

    if not session:
        return {
            "connected": False,
            "message": "No active Unifier session found"
        }

    return {
        "connected": True,
        "base_url": session.get("base_url"),
        "username": session.get("username"),
        "has_token": bool(session.get("token")),
    }

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
def export_content(
    content: str,
    output_file: str,
    sheet_name: str = "Sheet1"
) -> str:
    """
    Export fetched content to a .csv or .xlsx file.

    content: JSON string for a list of objects, a single object, or an API response containing `data`.
    output_file: Relative or absolute path ending in .csv or .xlsx.
    sheet_name: Excel sheet name when exporting to .xlsx.
    """
    try:
        return export_content_to_file(content=content, output_file=output_file, sheet_name=sheet_name)
    except Exception as e:
        return f"Error exporting content: {str(e)}"


@mcp.tool()
def export_content_to_pdf_tool(
    content: str,
    output_file: str
) -> str:
    """
    Export fetched content to a .pdf file.

    content: JSON string for a list of objects, a single object, or an API response containing `data`.
    output_file: Relative or absolute path ending in .pdf.
    """
    try:
        return export_content_to_pdf(content=content, output_file=output_file)
    except Exception as e:
        return f"Error exporting content to PDF: {str(e)}"


@mcp.tool()
def export_content_to_docx_tool(
    content: str,
    output_file: str
) -> str:
    """
    Export fetched content to a .docx file.

    content: JSON string for a list of objects, a single object, or an API response containing `data`.
    output_file: Relative or absolute path ending in .docx.
    """
    try:
        return export_content_to_docx(content=content, output_file=output_file)
    except Exception as e:
        return f"Error exporting content to DOCX: {str(e)}"


@mcp.tool()
def generate_chart(
    content: str,
    chart_type: str,
    output_file: str,
    x_field: str,
    y_field: str = "",
    title: str = "Chart",
    group_by: str = ""
) -> str:
    """
    Generate a chart image (.png) from fetched JSON content.

    chart_type: bar, line, pie, horizontal_bar
    x_field: field used for x-axis or category grouping
    y_field: optional numeric field for aggregation
    group_by: optional secondary grouping field for grouped charts
    """
    try:
        return generate_chart_image(
            content=content,
            chart_type=chart_type,
            output_file=output_file,
            x_field=x_field,
            y_field=y_field,
            title=title,
            group_by=group_by,
        )
    except Exception as e:
        return f"Error generating chart: {str(e)}"


@mcp.tool()
def generate_summary_dashboard_tool(
    content: str,
    output_file: str,
    title: str = "Summary Dashboard",
    metric_fields: str = "",
    category_field: str = "",
    top_n: int = 10
) -> str:
    """
    Generate a summary dashboard PNG with row/column counts, numeric summaries,
    and an optional top-category frequency chart.
    """
    try:
        return generate_summary_dashboard(
            content=content,
            output_file=output_file,
            title=title,
            metric_fields=metric_fields,
            category_field=category_field,
            top_n=top_n,
        )
    except Exception as e:
        return f"Error generating summary dashboard: {str(e)}"


@mcp.tool()
def generate_table_image_tool(
    content: str,
    output_file: str,
    title: str = "Data Table",
    columns: str = "",
    max_rows: int = 20
) -> str:
    """
    Generate a table image PNG from fetched JSON content.
    """
    try:
        return generate_table_image(
            content=content,
            output_file=output_file,
            title=title,
            columns=columns,
            max_rows=max_rows,
        )
    except Exception as e:
        return f"Error generating table image: {str(e)}"


@mcp.tool()
def convert_docx_to_pdf_tool(
    input_docx_file: str,
    output_pdf_file: str
) -> str:
    """
    Convert an uploaded .docx file into a simple content-based .pdf.

    This extracts paragraphs and tables from the Word document and rebuilds them in PDF form.
    It is machine-independent, but not layout-faithful to the original Word formatting.
    """
    try:
        return convert_docx_to_pdf_content_based(
            input_docx_file=input_docx_file,
            output_pdf_file=output_pdf_file,
        )
    except Exception as e:
        return f"Error converting DOCX to PDF: {str(e)}"


@mcp.tool()
def send_email(
    to_emails: str,
    subject: str,
    body: str,
    attachment_paths: str = ""
) -> str:
    """
    Send a simple plain-text email using configured Gmail SMTP settings.

    to_emails: Comma-separated recipient email addresses.
    subject: Email subject.
    body: Plain text email body.
    attachment_paths: Optional comma-separated file paths.
    """
    try:
        if not SMTP_USERNAME or not SMTP_PASSWORD or not SMTP_SENDER_EMAIL:
            return (
                "Error sending email: Missing SMTP configuration. "
                "Please set SMTP_USERNAME, SMTP_PASSWORD, and SMTP_SENDER_EMAIL in the environment."
            )

        attachments = [path.strip() for path in attachment_paths.split(",") if path.strip()]
        return send_email_via_smtp(
            smtp_host=SMTP_HOST,
            smtp_port=SMTP_PORT,
            username=SMTP_USERNAME,
            password=SMTP_PASSWORD,
            sender_email=SMTP_SENDER_EMAIL,
            to_emails=to_emails,
            subject=subject,
            body=body,
            attachment_paths=attachments,
            use_starttls=True,
        )
    except Exception as e:
        return f"Error sending email: {str(e)}"


@mcp.tool()
def compress_files(
    input_paths: str,
    output_zip_file: str
) -> str:
    """
    Compress one or more files into a ZIP archive.

    input_paths: Comma-separated file paths.
    output_zip_file: Output .zip file path.
    """
    try:
        files = [path.strip() for path in input_paths.split(",") if path.strip()]
        return compress_files_to_zip(files, output_zip_file)
    except Exception as e:
        return f"Error compressing files: {str(e)}"


@mcp.tool()
def split_large_file(
    input_file: str,
    output_dir: str = "",
    part_size_mb: int = 10
) -> dict:
    """
    Split a large file into smaller parts for email transfer.

    input_file: Path to the file to split.
    output_dir: Directory for output parts. Defaults to the same folder.
    part_size_mb: Max size per part in MB.
    """
    try:
        result = split_file(input_file=input_file, output_dir=output_dir, part_size_mb=part_size_mb)
        result["reassembly_instructions"] = create_reassembly_instructions(
            original_file_name=os.path.basename(input_file),
            part_files=result["parts"],
        )
        return result
    except Exception as e:
        return {"error": str(e)}
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
    Route("/login", login, methods=["POST"]),
    Route("/login/github", github_login),
    Route(
        "/auth/github/callback",
        github_callback,
        methods=["GET"],
        name="github_callback"
    ),
    Mount("/", app=mcp_app),
], lifespan=lifespan)

app.add_middleware(
    SessionMiddleware,
    secret_key=SESSION_SECRET,
    same_site="lax",
    https_only=os.getenv("ENV", "development").lower() in {"production", "prod"},
)
app.add_middleware(AuthMiddleware)

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

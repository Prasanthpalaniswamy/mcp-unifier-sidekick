from mcp.server.fastmcp import FastMCP
import base64

mcp = FastMCP("Base64 Tools")

@mcp.tool()
def encode_credentials(login: str, password: str) -> str:
    """Encode login and password into Base64"""
    credentials = f"{login}:{password}"
    return base64.b64encode(credentials.encode("utf-8")).decode("utf-8")

@mcp.tool()
def decode_credentials(encoded_data: str) -> dict:
    """Decode Base64 string into login and password"""
    decoded_bytes = base64.b64decode(encoded_data)
    decoded_string = decoded_bytes.decode("utf-8")
    login, password = decoded_string.split(":", 1)

    return {
        "login": login,
        "password": password
    }

if __name__ == "__main__":
    mcp.run()
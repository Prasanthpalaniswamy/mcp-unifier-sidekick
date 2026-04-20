import asyncio
import json

from mcp.client.session import ClientSession
from mcp.client.streamable_http import streamablehttp_client


MCP_URL = "http://127.0.0.1:8000/mcp"


async def run_client(name: str, username: str, password: str):
    print(f"\n=== Starting client: {name} ===")

    async with streamablehttp_client(MCP_URL) as streams:
        reader = streams[0]
        writer = streams[1]

        async with ClientSession(reader, writer) as client:
            await client.initialize()

            tools = await client.list_tools()
            tool_names = [tool.name for tool in tools.tools]
            print(f"[{name}] Tools: {tool_names}")

            init_result = await client.call_tool(
                "init_unifier",
                {
                    "base_url": "http://169.224.230.179:7001/ws/rest/service/v1",
                    "username": username,
                    "password": password,
                },
            )
            print(f"[{name}] init_unifier => {init_result.content[0].text}")

            projects_result = await client.call_tool(
                "list_projects",
                {
                    "shell_type": "Projects",
                    "limit": 5,
                    "offset": 0,
                },
            )

            if hasattr(projects_result, "structuredContent") and projects_result.structuredContent:
                payload = projects_result.structuredContent
            else:
                payload = json.loads(projects_result.content[0].text)

            count = len(payload.get("data", [])) if isinstance(payload, dict) else 0
            print(f"[{name}] list_projects returned {count} records")
            print(json.dumps(payload, indent=2)[:1200])

            return {
                "client": name,
                "tool_names": tool_names,
                "project_count": count,
                "sample_project": payload.get("data", [None])[0] if isinstance(payload, dict) else None,
            }


async def main():
    results = await asyncio.gather(
        run_client("client-1", "$$intuser", "intuser@123"),
        run_client("client-2", "$$intuser", "intuser@123"),
    )

    print("\n=== Summary ===")
    print(json.dumps(results, indent=2, default=str)[:2000])


if __name__ == "__main__":
    asyncio.run(main())
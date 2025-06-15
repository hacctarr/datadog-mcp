#!/usr/bin/env python3
"""
Datadog CI Visibility MCP Server

Provides tools to query Datadog CI pipelines with filtering capabilities.
"""

import asyncio
import logging
from typing import List

from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import CallToolRequest, CallToolResult, Tool, ServerCapabilities

from tools import get_fingerprints, list_pipelines, get_logs, get_teams, get_metrics, get_metric_fields, get_metric_field_values, list_metrics

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("datadog-mcp-server")

# Create MCP server instance
server = Server("datadog-mcp-server")

# Tool registry
TOOLS = {
    "list_ci_pipelines": {
        "definition": list_pipelines.get_tool_definition,
        "handler": list_pipelines.handle_call,
    },
    "get_pipeline_fingerprints": {
        "definition": get_fingerprints.get_tool_definition,
        "handler": get_fingerprints.handle_call,
    },
    "get_logs": {
        "definition": get_logs.get_tool_definition,
        "handler": get_logs.handle_call,
    },
    "get_teams": {
        "definition": get_teams.get_tool_definition,
        "handler": get_teams.handle_call,
    },
    "get_metrics": {
        "definition": get_metrics.get_tool_definition,
        "handler": get_metrics.handle_call,
    },
    "get_metric_fields": {
        "definition": get_metric_fields.get_tool_definition,
        "handler": get_metric_fields.handle_call,
    },
    "get_metric_field_values": {
        "definition": get_metric_field_values.get_tool_definition,
        "handler": get_metric_field_values.handle_call,
    },
    "list_metrics": {
        "definition": list_metrics.get_tool_definition,
        "handler": list_metrics.handle_call,
    },
}


@server.list_tools()
async def handle_list_tools() -> List[Tool]:
    """List available tools."""
    return [tool_config["definition"]() for tool_config in TOOLS.values()]


@server.call_tool()
async def handle_call_tool(request: CallToolRequest) -> CallToolResult:
    """Handle tool calls."""
    try:
        if request.name in TOOLS:
            handler = TOOLS[request.name]["handler"]
            return await handler(request)
        else:
            return CallToolResult(
                content=[{"type": "text", "text": f"Unknown tool: {request.name}"}],
                isError=True,
            )
    except Exception as e:
        logger.error(f"Error handling tool call: {e}")
        return CallToolResult(
            content=[{"type": "text", "text": f"Error: {str(e)}"}],
            isError=True,
        )


async def main():
    """Main entry point."""
    # Run the server using stdio transport
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="datadog-mcp-server",
                server_version="1.0.0",
                capabilities=ServerCapabilities(
                    tools={}
                ),
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())
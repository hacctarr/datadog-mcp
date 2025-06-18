"""
Get service logs tool
"""

import json
import logging
from typing import Any, Dict

from mcp.types import CallToolRequest, CallToolResult, Tool, TextContent

logger = logging.getLogger(__name__)

from ..utils.datadog_client import fetch_logs
from ..utils.formatters import extract_log_info, format_logs_as_table, format_logs_as_text


def get_tool_definition() -> Tool:
    """Get the tool definition for get_logs."""
    return Tool(
        name="get_logs",
        description="Search and retrieve logs from Datadog with flexible filtering parameters. Similar to get_metrics but for log data.",
        inputSchema={
            "type": "object",
            "properties": {
                "time_range": {
                    "type": "string",
                    "description": "Time range to look back",
                    "enum": ["1h", "4h", "8h", "1d", "7d", "14d", "30d"],
                    "default": "1h",
                },
                "filters": {
                    "type": "object",
                    "description": "Filters to apply to the log search (e.g., {'service': 'web', 'env': 'prod', 'status': 'error', 'host': 'web-01'})",
                    "additionalProperties": {"type": "string"},
                    "default": {},
                },
                "query": {
                    "type": "string",
                    "description": "Free-text search query (e.g., 'error OR exception', 'timeout', 'user_id:12345')",
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of log entries (default: 100)",
                    "default": 100,
                    "minimum": 1,
                    "maximum": 1000,
                },
                "format": {
                    "type": "string",
                    "description": "Output format",
                    "enum": ["table", "text", "json"],
                    "default": "table",
                },
            },
            "additionalProperties": False,
            "required": [],
        },
    )


async def handle_call(request: CallToolRequest) -> CallToolResult:
    """Handle the get_logs tool call."""
    try:
        args = request.arguments or {}
        
        time_range = args.get("time_range", "1h")
        filters = args.get("filters", {})
        query = args.get("query")
        limit = args.get("limit", 100)
        format_type = args.get("format", "table")
        
        # Fetch log events using the new flexible API
        log_events = await fetch_logs(
            time_range=time_range,
            filters=filters,
            query=query,
            limit=limit,
        )
        
        # Extract log info
        logs = extract_log_info(log_events)
        
        # Check if we got zero results with a custom query
        if len(logs) == 0 and query and ":" in query:
            suggestion_msg = f"No logs found with query: '{query}'\n\n"
            suggestion_msg += "Try adjusting your query or checking if the field names are correct.\n"
            suggestion_msg += "Common log fields include: service, env, status, host, container, source"
            
            return CallToolResult(
                content=[TextContent(type="text", text=suggestion_msg)],
                isError=False,
            )
        
        # Format output
        if format_type == "json":
            content = json.dumps(logs, indent=2)
        elif format_type == "text":
            content = format_logs_as_text(logs)
        else:  # table
            content = format_logs_as_table(logs)
        
        # Add summary header
        summary = f"Time Range: {time_range} | Found: {len(logs)} logs"
        if filters:
            filter_strs = [f"{k}={v}" for k, v in filters.items()]
            summary += f" | Filters: {', '.join(filter_strs)}"
        if query:
            summary += f" | Query: {query}"
        
        final_content = f"{summary}\n{'=' * len(summary)}\n\n{content}"
        
        return CallToolResult(
            content=[TextContent(type="text", text=final_content)],
            isError=False,
        )
        
    except Exception as e:
        return CallToolResult(
            content=[TextContent(type="text", text=f"Error: {str(e)}")],
            isError=True,
        )
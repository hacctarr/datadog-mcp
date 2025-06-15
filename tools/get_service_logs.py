"""
Get service logs tool
"""

import json
from typing import Any, Dict

from mcp.types import CallToolRequest, CallToolResult, TextContent, Tool

from utils.datadog_client import fetch_service_logs
from utils.formatters import extract_log_info, format_logs_as_table, format_logs_as_text


def get_tool_definition() -> Tool:
    """Get the tool definition for get_service_logs."""
    return Tool(
        name="get_service_logs",
        description="Get service logs from Datadog for various time ranges",
        inputSchema={
            "type": "object",
            "properties": {
                "service": {
                    "type": "string",
                    "description": "Service name to get logs for (e.g., 'content', 'accounts')",
                },
                "time_range": {
                    "type": "string",
                    "description": "Time range to look back",
                    "enum": ["1h", "4h", "8h", "1d", "7d", "14d", "30d"],
                    "default": "1h",
                },
                "environment": {
                    "type": "string",
                    "description": "Environment to filter logs for",
                    "enum": ["prod", "staging", "backoffice"],
                },
                "log_level": {
                    "type": "string",
                    "description": "Filter by log level",
                    "enum": ["debug", "info", "warn", "error", "critical"],
                },
                "query": {
                    "type": "string",
                    "description": "Additional query filter (e.g., 'error OR exception')",
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
            "required": ["service"],
        },
    )


async def handle_call(request: CallToolRequest) -> CallToolResult:
    """Handle the get_service_logs tool call."""
    try:
        args = request.arguments or {}
        
        service = args.get("service")
        time_range = args.get("time_range", "1h")
        environment = args.get("environment")
        log_level = args.get("log_level")
        query = args.get("query")
        limit = args.get("limit", 100)
        format_type = args.get("format", "table")
        
        if not service:
            return CallToolResult(
                content=[TextContent(type="text", text="Error: service parameter is required")],
                isError=True,
            )
        
        # Fetch log events
        log_events = await fetch_service_logs(
            service=service,
            time_range=time_range,
            environment=environment,
            log_level=log_level,
            query=query,
            limit=limit,
        )
        
        # Extract log info
        logs = extract_log_info(log_events)
        
        # Format output
        if format_type == "json":
            content = json.dumps(logs, indent=2)
        elif format_type == "text":
            content = format_logs_as_text(logs)
        else:  # table
            content = format_logs_as_table(logs)
        
        # Add summary header
        summary = f"Service: {service} | Time Range: {time_range} | Found: {len(logs)} logs"
        if environment:
            summary += f" | Environment: {environment}"
        if log_level:
            summary += f" | Level: {log_level}"
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
"""
List metrics tool
"""

import json
import logging
from typing import Any, Dict

from mcp.types import CallToolRequest, CallToolResult, TextContent, Tool

logger = logging.getLogger(__name__)

from utils.datadog_client import fetch_metrics_list


def get_tool_definition() -> Tool:
    """Get the tool definition for list_metrics."""
    return Tool(
        name="list_metrics",
        description="List all available metrics from Datadog. Useful for discovering metrics before querying them with get_metrics.",
        inputSchema={
            "type": "object",
            "properties": {
                "filter": {
                    "type": "string",
                    "description": "Optional filter to search for metrics by tags (e.g., 'aws:*', 'env:*', 'service:web'). Leave empty to list all metrics.",
                    "default": "",
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of metrics to return",
                    "minimum": 1,
                    "maximum": 10000,
                    "default": 100,
                },
                "format": {
                    "type": "string",
                    "description": "Output format",
                    "enum": ["list", "json", "summary"],
                    "default": "list",
                },
            },
            "additionalProperties": False,
            "required": [],
        },
    )


async def handle_call(request: CallToolRequest) -> CallToolResult:
    """Handle the list_metrics tool call."""
    try:
        args = request.params.arguments or {}
        
        filter_query = args.get("filter", "")
        limit = args.get("limit", 100)
        format_type = args.get("format", "list")
        
        # Fetch metrics list
        metrics_response = await fetch_metrics_list(
            filter_query=filter_query,
            limit=limit
        )
        
        if "data" not in metrics_response:
            return CallToolResult(
                content=[TextContent(type="text", text="No metrics data returned from API")],
                isError=True,
            )
        
        metrics = metrics_response["data"]
        
        # Format output
        if format_type == "json":
            content = json.dumps(metrics_response, indent=2)
        elif format_type == "summary":
            content = f"Found {len(metrics)} metrics"
            if filter_query:
                content += f" matching filter: '{filter_query}'"
            content += f"\n\nFirst 10 metrics:\n"
            for i, metric in enumerate(metrics[:10]):
                metric_id = metric.get("id", "unknown")
                content += f"{i+1:2d}. {metric_id}\n"
            if len(metrics) > 10:
                content += f"... and {len(metrics) - 10} more"
        else:  # list format
            content = f"Available Datadog metrics"
            if filter_query:
                content += f" (filtered by: '{filter_query}')"
            content += f" | Total: {len(metrics)}"
            if limit < len(metrics):
                content += f" (showing first {limit})"
            content += "\n" + "=" * len(content.split('\n')[-1]) + "\n\n"
            
            if metrics:
                for i, metric in enumerate(metrics, 1):
                    metric_id = metric.get("id", "unknown")
                    metric_type = metric.get("type", "unknown")
                    
                    # Try to get attributes for additional info
                    attributes = metric.get("attributes", {})
                    description = attributes.get("description", "")
                    unit = attributes.get("unit", "")
                    
                    content += f"{i:3d}. {metric_id}"
                    if unit:
                        content += f" ({unit})"
                    if description:
                        content += f"\n     {description[:100]}"
                        if len(description) > 100:
                            content += "..."
                    content += "\n"
            else:
                content += "No metrics found"
                if filter_query:
                    content += f" matching filter: '{filter_query}'"
        
        return CallToolResult(
            content=[TextContent(type="text", text=content)],
            isError=False,
        )
        
    except Exception as e:
        logger.error(f"Error in list_metrics: {e}")
        return CallToolResult(
            content=[TextContent(type="text", text=f"Error: {str(e)}")],
            isError=True,
        )
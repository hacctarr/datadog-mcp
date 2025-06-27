"""
List monitors tool
"""

import json
import logging
from typing import Any, Dict

from mcp.types import CallToolRequest, CallToolResult, Tool, TextContent

logger = logging.getLogger(__name__)

from ..utils.datadog_client import fetch_monitors


def get_tool_definition() -> Tool:
    """Get the tool definition for list_monitors."""
    return Tool(
        name="list_monitors",
        description="List all monitors from Datadog. Monitors are used for alerting on metrics, logs, and other data.",
        inputSchema={
            "type": "object",
            "properties": {
                "tags": {
                    "type": "string",
                    "description": "Filter monitors by tags (e.g., 'env:prod,service:web'). Leave empty to list all monitors.",
                    "default": "",
                },
                "name": {
                    "type": "string", 
                    "description": "Filter monitors by name (substring match). Leave empty to include all monitors.",
                    "default": "",
                },
                "monitor_tags": {
                    "type": "string",
                    "description": "Filter monitors by monitor tags (e.g., 'team:backend'). Leave empty to include all monitors.",
                    "default": "",
                },
                "format": {
                    "type": "string",
                    "description": "Output format",
                    "enum": ["table", "json", "summary"],
                    "default": "table",
                },
                "page_size": {
                    "type": "integer",
                    "description": "Number of monitors per page (default: 50, max: 1000)",
                    "default": 50,
                    "minimum": 1,
                    "maximum": 1000,
                },
                "page": {
                    "type": "integer", 
                    "description": "Page number (0-indexed, default: 0)",
                    "default": 0,
                    "minimum": 0,
                },
            },
            "additionalProperties": False,
            "required": [],
        },
    )


async def handle_call(request: CallToolRequest) -> CallToolResult:
    """Handle the list_monitors tool call."""
    try:
        args = request.arguments or {}
        
        tags = args.get("tags", "")
        name = args.get("name", "")
        monitor_tags = args.get("monitor_tags", "")
        format_type = args.get("format", "table")
        page_size = args.get("page_size", 50)
        page = args.get("page", 0)
        
        # Fetch monitors list
        monitors = await fetch_monitors(
            tags=tags,
            name=name,
            monitor_tags=monitor_tags,
            page_size=page_size,
            page=page
        )
        
        if not monitors:
            return CallToolResult(
                content=[TextContent(type="text", text="No monitors found")],
                isError=False,
            )
        
        # Format output
        if format_type == "json":
            content = json.dumps(monitors, indent=2)
        elif format_type == "summary":
            content = f"Found {len(monitors)} monitors"
            if page_size < 1000:
                content += f" (page {page + 1}, showing up to {page_size} per page)"
            if tags or name or monitor_tags:
                filters = []
                if tags:
                    filters.append(f"tags: '{tags}'")
                if name:
                    filters.append(f"name: '{name}'")
                if monitor_tags:
                    filters.append(f"monitor_tags: '{monitor_tags}'")
                content += f" matching filters: {', '.join(filters)}"
            
            # Group by type and state
            by_type = {}
            by_state = {}
            for monitor in monitors:
                monitor_type = monitor.get("type", "unknown")
                monitor_state = monitor.get("overall_state", "unknown")
                
                by_type[monitor_type] = by_type.get(monitor_type, 0) + 1
                by_state[monitor_state] = by_state.get(monitor_state, 0) + 1
            
            content += "\n\nBy Type:"
            for type_name, count in sorted(by_type.items()):
                content += f"\n  {type_name}: {count}"
            
            content += "\n\nBy State:"
            for state, count in sorted(by_state.items()):
                content += f"\n  {state}: {count}"
            
        else:  # table format
            content = f"Datadog Monitors"
            filters = []
            if tags:
                filters.append(f"tags: '{tags}'")
            if name:
                filters.append(f"name: '{name}'")
            if monitor_tags:
                filters.append(f"monitor_tags: '{monitor_tags}'")
            
            if filters:
                content += f" (filtered by: {', '.join(filters)})"
            content += f" | Total: {len(monitors)}"
            if page_size < 1000:
                content += f" (page {page + 1}, up to {page_size} per page)"
            content += "\n" + "=" * len(content.split('\n')[-1]) + "\n\n"
            
            for i, monitor in enumerate(monitors, 1):
                monitor_id = monitor.get("id", "unknown")
                monitor_name = monitor.get("name", "Unnamed")
                monitor_type = monitor.get("type", "unknown")
                monitor_state = monitor.get("overall_state", "unknown")
                
                # Get tags if available
                monitor_tag_list = monitor.get("tags", [])
                tags_str = ", ".join(monitor_tag_list[:3])  # Show first 3 tags
                if len(monitor_tag_list) > 3:
                    tags_str += f" (+{len(monitor_tag_list) - 3} more)"
                
                content += f"{i:3d}. [{monitor_state.upper()}] {monitor_name}\n"
                content += f"     ID: {monitor_id} | Type: {monitor_type}"
                if tags_str:
                    content += f" | Tags: {tags_str}"
                content += "\n\n"
        
        return CallToolResult(
            content=[TextContent(type="text", text=content)],
            isError=False,
        )
        
    except Exception as e:
        logger.error(f"Error in list_monitors: {e}")
        return CallToolResult(
            content=[TextContent(type="text", text=f"Error: {str(e)}")],
            isError=True,
        )
"""
Get metric field values tool
"""

import json
import logging
from typing import Any, Dict

from mcp.types import CallToolRequest, CallToolResult, TextContent, Tool

logger = logging.getLogger(__name__)

from utils.datadog_client import fetch_metric_field_values


def get_tool_definition() -> Tool:
    """Get the tool definition for get_metric_field_values."""
    return Tool(
        name="get_metric_field_values",
        description="Get all possible values for a specific field of a metric from Datadog to discover available dimensions",
        inputSchema={
            "type": "object",
            "properties": {
                "service": {
                    "type": "string",
                    "description": "Service name to get metric field values for (e.g., 'content', 'aws-apigateway')",
                },
                "metric_name": {
                    "type": "string",
                    "description": "Datadog metric name to get field values for",
                },
                "field_name": {
                    "type": "string", 
                    "description": "Field name to get all possible values for (e.g., 'region', 'account', 'environment')",
                },
                "time_range": {
                    "type": "string",
                    "description": "Time range to look back for value discovery",
                    "enum": ["1h", "4h", "8h", "1d", "7d", "14d", "30d"],
                    "default": "7d",
                },
                "environment": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Environment(s) to filter value discovery for. Can be one or multiple environments.",
                    "default": ["prod"],
                },
                "aggregation": {
                    "type": "string",
                    "description": "Metric aggregation method",
                    "enum": ["avg", "sum", "min", "max", "count"],
                    "default": "avg",
                },
                "format": {
                    "type": "string",
                    "description": "Output format",
                    "enum": ["list", "json"],
                    "default": "list",
                },
            },
            "additionalProperties": False,
            "required": ["service", "metric_name", "field_name"],
        },
    )


async def handle_call(request: CallToolRequest) -> CallToolResult:
    """Handle the get_metric_field_values tool call."""
    try:
        args = request.arguments or {}
        
        service = args.get("service")
        metric_name = args.get("metric_name")
        field_name = args.get("field_name")
        time_range = args.get("time_range", "7d")
        environment = args.get("environment", ["prod"])
        aggregation = args.get("aggregation", "avg")
        format_type = args.get("format", "list")
        
        # Handle legacy single environment string
        if isinstance(environment, str):
            environment = [environment]
        
        if not service:
            return CallToolResult(
                content=[TextContent(type="text", text="Error: service parameter is required")],
                isError=True,
            )
        
        if not metric_name:
            return CallToolResult(
                content=[TextContent(type="text", text="Error: metric_name parameter is required")],
                isError=True,
            )
            
        if not field_name:
            return CallToolResult(
                content=[TextContent(type="text", text="Error: field_name parameter is required")],
                isError=True,
            )
        
        # Fetch field values
        field_values = await fetch_metric_field_values(
            service=service,
            metric_name=metric_name,
            field_name=field_name,
            time_range=time_range,
            environment=environment,
            aggregation=aggregation,
        )
        
        # Format output
        if format_type == "json":
            content = json.dumps({
                "metric_name": metric_name,
                "service": service,
                "field_name": field_name,
                "time_range": time_range,
                "environment": environment,
                "aggregation": aggregation,
                "field_values": field_values
            }, indent=2)
        else:  # list format
            # Add summary header
            summary = f"Values for field '{field_name}' in metric '{metric_name}' | Service: {service} | Time Range: {time_range}"
            if environment:
                summary += f" | Environment: {', '.join(environment)}"
            
            content = f"{summary}\n{'=' * len(summary)}\n\n"
            
            if field_values:
                content += f"Found {len(field_values)} unique values for field '{field_name}':\n\n"
                content += "\n".join([f"  • {value}" for value in field_values])
                content += f"\n\nUsage examples:\n"
                content += f"• Filter by specific value: aggregation_by: [\"{field_name}\"] with environment filter\n"
                content += f"• Combine with other fields: aggregation_by: [\"{field_name}\", \"service\"]\n"
                if field_values:
                    sample_value = field_values[0]
                    content += f"• Query for specific {field_name}: add filter {field_name}:{sample_value} to your query"
            else:
                content += f"No values found for field '{field_name}' in the specified time range.\n\n"
                content += "This could mean:\n"
                content += f"• The field '{field_name}' doesn't exist for this metric\n"
                content += f"• No data exists in the specified time range ({time_range})\n"
                content += f"• The service '{service}' doesn't have this metric with this field\n\n"
                content += "Try:\n"
                content += "• Using get_metric_fields tool to see available fields\n"
                content += "• Extending the time_range (e.g., '30d')\n"
                content += "• Checking the service name"
        
        return CallToolResult(
            content=[TextContent(type="text", text=content)],
            isError=False,
        )
        
    except Exception as e:
        logger.error(f"Error in get_metric_field_values: {e}")
        return CallToolResult(
            content=[TextContent(type="text", text=f"Error: {str(e)}")],
            isError=True,
        )
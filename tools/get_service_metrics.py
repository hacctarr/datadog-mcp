"""
Get service metrics tool
"""

import json
from typing import Any, Dict

from mcp.types import CallToolRequest, CallToolResult, TextContent, Tool

from utils.datadog_client import fetch_service_metrics, fetch_multiple_metrics
from utils.formatters import (
    format_metrics_summary,
    format_metrics_table,
    format_metrics_timeseries,
)


def get_tool_definition() -> Tool:
    """Get the tool definition for get_service_metrics."""
    return Tool(
        name="get_service_metrics",
        description="Get service metrics from Datadog for various time ranges to see dynamics",
        inputSchema={
            "type": "object",
            "properties": {
                "service": {
                    "type": "string",
                    "description": "Service name to get metrics for (e.g., 'content', 'accounts')",
                },
                "metrics": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of metric names to fetch",
                    "default": [
                        "datadog.estimated_usage.logs.ingested_bytes",
                        "datadog.estimated_usage.logs.indexed_logs",
                        "trace.servlet.request.duration",
                        "trace.servlet.request.hits"
                    ],
                },
                "time_range": {
                    "type": "string",
                    "description": "Time range to look back",
                    "enum": ["1h", "4h", "8h", "1d", "7d", "14d", "30d"],
                    "default": "1h",
                },
                "environment": {
                    "type": "string",
                    "description": "Environment to filter metrics for",
                    "enum": ["prod", "staging", "backoffice"],
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
                    "enum": ["table", "summary", "timeseries", "json"],
                    "default": "table",
                },
            },
            "additionalProperties": False,
            "required": ["service"],
        },
    )


async def handle_call(request: CallToolRequest) -> CallToolResult:
    """Handle the get_service_metrics tool call."""
    try:
        args = request.arguments or {}
        
        service = args.get("service")
        metrics = args.get("metrics", [
            "datadog.estimated_usage.logs.ingested_bytes",
            "datadog.estimated_usage.logs.indexed_logs",
            "trace.servlet.request.duration",
            "trace.servlet.request.hits"
        ])
        time_range = args.get("time_range", "1h")
        environment = args.get("environment")
        aggregation = args.get("aggregation", "avg")
        format_type = args.get("format", "table")
        
        if not service:
            return CallToolResult(
                content=[TextContent(type="text", text="Error: service parameter is required")],
                isError=True,
            )
        
        # Fetch metrics data
        if len(metrics) == 1:
            # Single metric
            metric_name = metrics[0]
            single_result = await fetch_service_metrics(
                service=service,
                metric_name=metric_name,
                time_range=time_range,
                environment=environment,
                aggregation=aggregation,
            )
            metrics_data = {metric_name: single_result}
        else:
            # Multiple metrics
            metrics_data = await fetch_multiple_metrics(
                service=service,
                metric_names=metrics,
                time_range=time_range,
                environment=environment,
                aggregation=aggregation,
            )
        
        # Format output
        if format_type == "json":
            content = json.dumps(metrics_data, indent=2)
        elif format_type == "summary":
            content = format_metrics_summary(metrics_data)
        elif format_type == "timeseries":
            content = format_metrics_timeseries(metrics_data)
        else:  # table
            content = format_metrics_table(metrics_data)
        
        # Add summary header
        summary = f"Service: {service} | Time Range: {time_range} | Aggregation: {aggregation} | Metrics: {len(metrics)}"
        if environment:
            summary += f" | Environment: {environment}"
        
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
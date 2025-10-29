"""
Get APM traces tool
"""

import json
import logging
from typing import Any, Dict

from mcp.types import CallToolRequest, CallToolResult, Tool, TextContent

logger = logging.getLogger(__name__)

from ..utils.datadog_client import fetch_traces
from ..utils.formatters import extract_trace_info, format_traces_as_table, format_traces_as_text, format_traces_as_hierarchy


def get_tool_definition() -> Tool:
    """Get the tool definition for get_traces."""
    return Tool(
        name="get_traces",
        description="Search and retrieve APM traces (spans) from Datadog with flexible filtering parameters. Use this to analyze application performance, find slow requests, or investigate errors.",
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
                    "description": "Filters to apply to the trace search (e.g., {'service': 'web', 'env': 'prod', 'resource_name': 'GET /api/users', 'operation_name': 'http.request'})",
                    "additionalProperties": {"type": "string"},
                    "default": {},
                },
                "query": {
                    "type": "string",
                    "description": "Free-text search query (e.g., 'error', 'status:error', 'service:web AND env:prod', '@http.status_code:500')",
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of trace spans (default: 50)",
                    "default": 50,
                    "minimum": 1,
                    "maximum": 1000,
                },
                "cursor": {
                    "type": "string",
                    "description": "Pagination cursor from previous response (for getting next page)",
                    "default": "",
                },
                "format": {
                    "type": "string",
                    "description": "Output format",
                    "enum": ["table", "text", "json", "debug"],
                    "default": "table",
                },
                "include_children": {
                    "type": "boolean",
                    "description": "When true, automatically fetch all child spans for each trace found. This retrieves the full span hierarchy (database queries, middleware, etc.) for each parent span.",
                    "default": False,
                },
            },
            "additionalProperties": False,
            "required": [],
        },
    )


async def handle_call(request: CallToolRequest) -> CallToolResult:
    """Handle the get_traces tool call."""
    try:
        args = request.arguments or {}

        time_range = args.get("time_range", "1h")
        filters = args.get("filters", {})
        query = args.get("query")
        limit = args.get("limit", 50)
        cursor = args.get("cursor", "")
        format_type = args.get("format", "table")
        include_children = args.get("include_children", False)

        # Fetch trace events using the flexible API
        response = await fetch_traces(
            time_range=time_range,
            filters=filters,
            query=query,
            limit=limit,
            cursor=cursor if cursor else None,
        )

        # Handle case where response might be None or missing expected structure
        if response is None:
            return CallToolResult(
                content=[TextContent(type="text", text="Error: No response received from Datadog API")],
                isError=True,
            )

        trace_events = response.get("data", [])

        # Log response structure for debugging
        logger.debug(f"Received {len(trace_events)} trace events from API")

        # If include_children is True, fetch all child spans for each trace
        if include_children and trace_events:
            all_spans = []
            trace_ids_seen = set()

            for event in trace_events:
                attrs = event.get("attributes", {})
                trace_id = attrs.get("trace_id")

                if trace_id and trace_id not in trace_ids_seen:
                    trace_ids_seen.add(trace_id)

                    # Fetch all spans for this trace_id
                    logger.debug(f"Fetching child spans for trace_id: {trace_id}")
                    child_response = await fetch_traces(
                        time_range=time_range,
                        query=f"trace_id:{trace_id}",
                        limit=1000,  # Get all spans in the trace
                    )

                    if child_response and child_response.get("data"):
                        all_spans.extend(child_response["data"])
                    else:
                        # If child fetch fails, include the original span
                        all_spans.append(event)
                else:
                    # No trace_id, just include the original span
                    all_spans.append(event)

            trace_events = all_spans
            logger.debug(f"After fetching children: {len(trace_events)} total spans")

        # Extract trace info
        traces = extract_trace_info(trace_events)

        logger.debug(f"Extracted {len(traces)} traces after processing")

        # Get pagination info
        meta = response.get("meta", {})
        if meta is None:
            meta = {}
        page = meta.get("page", {})
        if page is None:
            page = {}
        next_cursor = page.get("after")

        # Check if we got zero results with a custom query
        if len(traces) == 0 and (query or filters):
            suggestion_msg = "No traces found with the specified filters.\n\n"
            if filters:
                filter_strs = [f"{k}={v}" for k, v in filters.items()]
                suggestion_msg += f"Filters: {', '.join(filter_strs)}\n"
            if query:
                suggestion_msg += f"Query: '{query}'\n"
            suggestion_msg += "\nTry adjusting your filters or query. Common trace fields include:\n"
            suggestion_msg += "- service: Service name (e.g., 'web', 'api', 'database')\n"
            suggestion_msg += "- env: Environment (e.g., 'prod', 'staging', 'dev')\n"
            suggestion_msg += "- resource_name: Resource name (e.g., 'GET /api/users', 'POST /api/orders')\n"
            suggestion_msg += "- operation_name: Operation name (e.g., 'http.request', 'db.query')\n"
            suggestion_msg += "- status: Status (e.g., 'ok', 'error')\n"
            suggestion_msg += "- @http.status_code: HTTP status code (e.g., '200', '500')\n"
            suggestion_msg += "- @http.method: HTTP method (e.g., 'GET', 'POST')\n"

            return CallToolResult(
                content=[TextContent(type="text", text=suggestion_msg)],
                isError=False,
            )

        # Format output
        if format_type == "debug":
            # Debug format: show raw API response for the first event
            sample_event = None
            if trace_events:
                event = trace_events[0]
                attrs = event.get("attributes", {})

                # Show all attribute keys (sorted for easier reading)
                all_keys = sorted(list(attrs.keys()))

                # Separate out timestamp/duration related fields
                timestamp_related = {k: attrs[k] for k in all_keys if 'time' in k.lower() or 'start' in k.lower()}
                duration_related = {k: attrs[k] for k in all_keys if 'duration' in k.lower()}

                sample_event = {
                    "id": event.get("id"),
                    "type": event.get("type"),
                    "total_attributes": len(all_keys),
                    "all_attribute_keys": all_keys,
                    "timestamp_related_fields": timestamp_related,
                    "duration_related_fields": duration_related,
                    "selected_attributes": {}
                }

                # Show first 30 attributes with their values
                for i, (key, value) in enumerate(attrs.items()):
                    if i < 30:
                        # Truncate long values
                        if isinstance(value, str) and len(value) > 100:
                            sample_event["selected_attributes"][key] = value[:100] + "..."
                        elif isinstance(value, dict):
                            sample_event["selected_attributes"][key] = f"<dict with {len(value)} keys>"
                        elif isinstance(value, list):
                            sample_event["selected_attributes"][key] = f"<list with {len(value)} items>"
                        else:
                            sample_event["selected_attributes"][key] = value

            debug_output = {
                "total_events": len(trace_events),
                "sample_event": sample_event,
                "extracted_trace": traces[0] if traces else None,
            }
            content = json.dumps(debug_output, indent=2)
        elif format_type == "json":
            # Include pagination info in JSON response
            output = {
                "traces": traces,
                "pagination": {
                    "next_cursor": next_cursor,
                    "has_more": bool(next_cursor)
                }
            }
            content = json.dumps(output, indent=2)
        elif format_type == "text":
            # Use hierarchy format if child spans were fetched
            if include_children:
                content = format_traces_as_hierarchy(traces)
            else:
                content = format_traces_as_text(traces)
            if next_cursor:
                content += f"\n\nNext cursor: {next_cursor}"
        else:  # table
            content = format_traces_as_table(traces)
            if next_cursor:
                content += f"\n\nNext cursor: {next_cursor}"

        # Add summary header (not for JSON/debug format which includes pagination separately)
        if format_type not in ["json", "debug"]:
            summary = f"Time Range: {time_range} | Found: {len(traces)} traces"
            if cursor:
                summary += f" (cursor pagination)"
            if filters:
                filter_strs = [f"{k}={v}" for k, v in filters.items()]
                summary += f" | Filters: {', '.join(filter_strs)}"
            if query:
                summary += f" | Query: {query}"

            final_content = f"{summary}\n{'=' * len(summary)}\n\n{content}"
        else:
            final_content = content

        return CallToolResult(
            content=[TextContent(type="text", text=final_content)],
            isError=False,
        )

    except Exception as e:
        logger.error(f"Error in get_traces handler: {str(e)}", exc_info=True)
        error_msg = f"Error retrieving traces: {str(e)}"

        # Add context about the query that failed
        if 'args' in locals():
            error_msg += f"\n\nQuery parameters:"
            if args.get("query"):
                error_msg += f"\n  - Query: {args.get('query')}"
            if args.get("filters"):
                error_msg += f"\n  - Filters: {args.get('filters')}"
            if args.get("time_range"):
                error_msg += f"\n  - Time range: {args.get('time_range')}"

        return CallToolResult(
            content=[TextContent(type="text", text=error_msg)],
            isError=True,
        )

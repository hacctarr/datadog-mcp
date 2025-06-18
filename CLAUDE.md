# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Building and Running
- `uv sync` - Install dependencies using UV package manager
- `uv run datadog_mcp/server.py` - Run the MCP server locally
- `docker build -t datadog-mcp .` - Build Docker image
- `docker-compose up` - Run with Docker Compose (requires DD_API_KEY and DD_APP_KEY env vars)

### Testing
- `uv run pytest tests/test_integration.py` - Test core server functionality (no API required)
- `uv run pytest tests/test_tools_working.py` - Test tool functionality (no API required) 
- `uv run pytest tests/` - Run all tests
- Most tests use mocking and don't require real Datadog API credentials
- For integration tests with real API, set DD_API_KEY and DD_APP_KEY environment variables

### Syntax Checking
- `uv run python -m py_compile datadog_mcp/server.py` - Check main server syntax
- `uv run python -m py_compile datadog_mcp/tools/*.py` - Check all tool implementations
- `uv run python -m py_compile datadog_mcp/utils/*.py` - Check utility modules

## Architecture Overview

This is a **Model Context Protocol (MCP) server** that provides Datadog monitoring capabilities to Claude Desktop. The architecture follows a modular tool-based pattern:

### Core Components

**`datadog_mcp/server.py`** - Main MCP server orchestrator that:
- Registers all available tools in the TOOLS dictionary
- Routes tool calls to appropriate handlers
- Manages async server lifecycle using stdio transport
- Handles authentication via environment variables

**`datadog_mcp/tools/`** - Individual MCP tool implementations, each with:
- `get_tool_definition()` - Returns MCP Tool schema with input validation
- `handle_call()` - Processes requests and returns formatted responses
- Consistent error handling and parameter validation patterns

**`datadog_mcp/utils/datadog_client.py`** - Centralized Datadog API client that:
- Manages authentication headers (DD_API_KEY, DD_APP_KEY)
- Implements all API endpoints (pipelines, logs, metrics, teams)
- Handles multiple environments via array parameters
- Supports aggregation_by for grouping metrics
- Uses proper Datadog API endpoints (e.g., `/api/v2/metrics/{metric_name}/all-tags` for field discovery)
- Constructs metric queries in Datadog format: `aggregation:metric{filters} by {fields}`

**`datadog_mcp/utils/formatters.py`** - Data transformation layer providing:
- Multiple output formats (table, JSON, summary, timeseries)
- Statistical analysis for metrics
- Consistent data presentation across tools

### Tool Registration Pattern
```python
TOOLS = {
    "list_metrics": {
        "definition": list_metrics.get_tool_definition,
        "handler": list_metrics.handle_call,
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
    # ... other tools
}
```

### Environment Parameter Handling
Environment parameters now accept arrays for multi-environment queries:
- Single: `["prod"]` (default)
- Multiple: `["prod", "staging", "dev"]`
- Arbitrary environment names supported

### Recently Modified Tools
The `get_metrics` tool (formerly `get_service_metrics`) now supports:
- General purpose metric querying for any metric (not just service metrics)
- Flexible parameter-based query construction
- User-specified metric names, filters, and aggregation fields
- Multiple environments via array parameter
- `aggregation_by` parameter accepting any field name(s) as array
- Automatic field discovery when aggregation fails
- User prompting with available fields for invalid aggregations
- Multiple aggregation fields support (e.g., `["service", "environment"]`)
- Backward compatibility with single environment and aggregation_by strings

The `list_metrics` tool has been added to discover available metrics using the `/api/v2/metrics` endpoint.

The `get_log_fields` tool has been removed as it was based on non-existent API endpoints.

## Key Implementation Patterns

### Async API Client Pattern
All Datadog API calls use async/await with httpx:
```python
async with httpx.AsyncClient() as client:
    response = await client.post(url, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()
```

### Error Handling Strategy
- Tool handlers wrap logic in try-catch blocks
- Return `CallToolResult` with `isError=True` for failures
- Log errors while returning user-friendly messages
- Individual metric failures don't fail entire requests

### Multi-Environment Query Building
For multiple environments, the client builds OR logic queries:
```python
if len(environment) > 1:
    env_filter = "env:" + " OR env:".join(environment)
    filters.append(f"({env_filter})")
```

### Dynamic Field Discovery Pattern
When aggregation fields don't exist or return zero results:
```python
# Check for zero results
if not has_data and aggregation_by != ["service"]:
    # Fetch available fields for the metric
    available_fields = await fetch_metric_available_fields(...)
    # Suggest available fields to user
    return suggestion_message_with_available_fields
```

### Multi-Field Aggregation Support
Aggregation by multiple fields uses comma-separated syntax:
```python
if aggregation_by and aggregation_by != ["service"]:
    by_clause = ",".join(aggregation_by)
    query_parts.append(f"by {{{by_clause}}}")
```

## Configuration Requirements

### Required Environment Variables
- `DD_API_KEY` - Datadog API authentication key
- `DD_APP_KEY` - Datadog application key for authorization

### Python Requirements
- Python 3.13+ (specified in pyproject.toml)
- UV package manager for dependency management
- Async/await support throughout codebase

### Docker Integration
The Docker setup uses multi-stage builds with:
- Python 3.13-slim base image
- UV package manager installation
- Multi-architecture support (AMD64/ARM64)

## Testing Strategy

Tests are organized by feature area and require real Datadog API access:
- All tests validate actual API responses
- Environment variables must be set for test execution
- Tests cover both success and error scenarios
- Each tool has dedicated test coverage

## Claude Desktop Integration

The server integrates with Claude Desktop via MCP configuration:
```json
{
  "mcpServers": {
    "datadog": {
      "command": "docker",
      "args": ["run", "-i", "-e", "DD_API_KEY=${DD_API_KEY}", "-e", "DD_APP_KEY=${DD_APP_KEY}", "magistersart/datadog-mcp:latest"]
    }
  }
}
```

The server provides comprehensive Datadog monitoring through conversational commands like "Show CI pipelines for my-repo" or "Get error logs for service-name in the last 4 hours".
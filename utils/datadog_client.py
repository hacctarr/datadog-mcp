"""
Datadog API client utilities
"""

import logging
import os
from typing import Any, Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)

# Datadog API configuration
DATADOG_API_URL = "https://api.datadoghq.com"
DATADOG_API_KEY = os.getenv("DD_API_KEY")
DATADOG_APP_KEY = os.getenv("DD_APP_KEY")

if not DATADOG_API_KEY or not DATADOG_APP_KEY:
    logger.error("DD_API_KEY and DD_APP_KEY environment variables must be set")
    raise ValueError("Datadog API credentials not configured")


async def fetch_ci_pipelines(
    repository: Optional[str] = None,
    pipeline_name: Optional[str] = None,
    days_back: int = 90,
    limit: int = 1000,
) -> List[Dict[str, Any]]:
    """Fetch CI pipelines from Datadog API."""
    url = f"{DATADOG_API_URL}/api/v2/ci/pipelines/events/search"
    
    headers = {
        "Content-Type": "application/json",
        "DD-API-KEY": DATADOG_API_KEY,
        "DD-APPLICATION-KEY": DATADOG_APP_KEY,
    }
    
    # Build query filter
    query_parts = []
    if repository:
        query_parts.append(f'@git.repository.name:"{repository}"')
    if pipeline_name:
        query_parts.append(f'@ci.pipeline.name:"{pipeline_name}"')
    
    query = " AND ".join(query_parts) if query_parts else "*"
    
    payload = {
        "filter": {
            "query": query,
            "from": f"now-{days_back}d",
            "to": "now",
        },
        "page": {"limit": limit},
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            return response.json().get("data", [])
        except httpx.HTTPError as e:
            logger.error(f"HTTP error fetching pipelines: {e}")
            raise
        except Exception as e:
            logger.error(f"Error fetching pipelines: {e}")
            raise


async def fetch_service_logs(
    service: str,
    time_range: str = "1h",
    environment: Optional[List[str]] = None,
    log_level: Optional[str] = None,
    query: Optional[str] = None,
    limit: int = 100,
) -> List[Dict[str, Any]]:
    """Fetch service logs from Datadog API."""
    url = f"{DATADOG_API_URL}/api/v2/logs/events/search"
    
    headers = {
        "Content-Type": "application/json",
        "DD-API-KEY": DATADOG_API_KEY,
        "DD-APPLICATION-KEY": DATADOG_APP_KEY,
    }
    
    # Build query filter
    query_parts = [f"service:{service}"]
    
    if environment:
        if len(environment) == 1:
            query_parts.append(f"env:{environment[0]}")
        else:
            # For multiple environments, use OR logic
            env_filter = "env:" + " OR env:".join(environment)
            query_parts.append(f"({env_filter})")
    
    if log_level:
        query_parts.append(f"status:{log_level}")
    
    if query:
        query_parts.append(query)
    
    combined_query = " AND ".join(query_parts)
    
    payload = {
        "filter": {
            "query": combined_query,
            "from": f"now-{time_range}",
            "to": "now",
        },
        "page": {"limit": limit},
        "sort": "-timestamp",  # Most recent first
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            return response.json().get("data", [])
        except httpx.HTTPError as e:
            logger.error(f"HTTP error fetching logs: {e}")
            raise
        except Exception as e:
            logger.error(f"Error fetching logs: {e}")
            raise


async def fetch_teams() -> List[Dict[str, Any]]:
    """Fetch teams from Datadog API."""
    url = f"{DATADOG_API_URL}/api/v2/team"
    
    headers = {
        "Content-Type": "application/json",
        "DD-API-KEY": DATADOG_API_KEY,
        "DD-APPLICATION-KEY": DATADOG_APP_KEY,
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            return response.json().get("data", [])
        except httpx.HTTPError as e:
            logger.error(f"HTTP error fetching teams: {e}")
            raise
        except Exception as e:
            logger.error(f"Error fetching teams: {e}")
            raise


async def fetch_team_memberships(team_id: str) -> List[Dict[str, Any]]:
    """Fetch team memberships from Datadog API."""
    url = f"{DATADOG_API_URL}/api/v2/team/{team_id}/memberships"
    
    headers = {
        "Content-Type": "application/json",
        "DD-API-KEY": DATADOG_API_KEY,
        "DD-APPLICATION-KEY": DATADOG_APP_KEY,
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            return response.json().get("data", [])
        except httpx.HTTPError as e:
            logger.error(f"HTTP error fetching team memberships for {team_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error fetching team memberships for {team_id}: {e}")
            raise


async def fetch_metrics(
    metric_name: str,
    time_range: str = "1h",
    aggregation: str = "avg",
    filters: Optional[Dict[str, str]] = None,
    aggregation_by: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Fetch metrics from Datadog API with flexible filtering."""
    
    headers = {
        "DD-API-KEY": DATADOG_API_KEY,
        "DD-APPLICATION-KEY": DATADOG_APP_KEY,
    }
    
    # Build metric query
    query_parts = [f"{aggregation}:{metric_name}"]
    
    # Add filters if specified
    filter_list = []
    if filters:
        for key, value in filters.items():
            filter_list.append(f"{key}:{value}")
    
    # Combine filters with proper syntax first
    if filter_list:
        query_parts.append("{" + ",".join(filter_list) + "}")
    
    # Add aggregation_by to the query if specified (after filters)
    if aggregation_by:
        by_clause = ",".join(aggregation_by)
        query_parts.append(f" by {{{by_clause}}}")
    
    query = "".join(query_parts)
    
    # Log the constructed query for debugging
    logger.debug(f"Constructed query: {query}")
    
    # Calculate time range in seconds
    import time
    to_timestamp = int(time.time())
    
    time_deltas = {
        "1h": 3600,
        "4h": 14400,
        "8h": 28800,
        "1d": 86400,
        "7d": 604800,
        "14d": 1209600,
        "30d": 2592000,
    }
    
    seconds_back = time_deltas.get(time_range, 3600)
    from_timestamp = to_timestamp - seconds_back
    
    # Use GET request with query parameters
    params = {
        "query": query,
        "from": from_timestamp,
        "to": to_timestamp,
    }
    
    url = f"{DATADOG_API_URL}/api/v1/query"
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, params=params)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"HTTP error fetching metrics: {e}")
            logger.error(f"Query: {query}")
            raise
        except Exception as e:
            logger.error(f"Error fetching metrics: {e}")
            raise




async def fetch_metrics_list(
    filter_query: str = "",
    limit: int = 100,
) -> Dict[str, Any]:
    """Fetch list of all available metrics from Datadog API."""
    
    headers = {
        "DD-API-KEY": DATADOG_API_KEY,
        "DD-APPLICATION-KEY": DATADOG_APP_KEY,
    }
    
    # Use the v2 metrics endpoint to list all metrics
    url = f"{DATADOG_API_URL}/api/v2/metrics"
    
    # Build query parameters
    params = {
        "page[size]": min(limit, 10000),  # API maximum
    }
    
    if filter_query:
        params["filter[tags]"] = filter_query
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, params=params)
            response.raise_for_status()
            return response.json()
            
        except httpx.HTTPError as e:
            logger.error(f"HTTP error fetching metrics list: {e}")
            raise
        except Exception as e:
            logger.error(f"Error fetching metrics list: {e}")
            raise


async def fetch_metric_available_fields(
    metric_name: str,
    time_range: str = "1h",
    environment: Optional[List[str]] = None,
) -> List[str]:
    """Fetch available fields/tags for a metric from Datadog API."""
    
    headers = {
        "DD-API-KEY": DATADOG_API_KEY,
        "DD-APPLICATION-KEY": DATADOG_APP_KEY,
    }
    
    # Use the proper Datadog API endpoint to get all tags for a metric
    url = f"{DATADOG_API_URL}/api/v2/metrics/{metric_name}/all-tags"
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            available_fields = set()
            
            # Extract tags from the response
            if "data" in data and "attributes" in data["data"]:
                attributes = data["data"]["attributes"]
                
                # Get tags from the attributes
                if "tags" in attributes:
                    for tag in attributes["tags"]:
                        # Tags are in format "field:value", extract just the field name
                        if ":" in tag:
                            field_name = tag.split(":", 1)[0]
                            available_fields.add(field_name)
            
            return sorted(list(available_fields))
            
        except httpx.HTTPError as e:
            logger.error(f"HTTP error fetching metric tags: {e}")
            if hasattr(e, 'response') and e.response.status_code == 404:
                logger.warning(f"Metric {metric_name} not found or has no tags")
                return []
            raise
        except Exception as e:
            logger.error(f"Error fetching metric tags: {e}")
            raise



async def fetch_metric_field_values(
    service: str,
    metric_name: str,
    field_name: str,
    time_range: str = "1h",
    environment: Optional[List[str]] = None,
    aggregation: str = "avg",
) -> List[str]:
    """Fetch all possible values for a specific field of a metric from Datadog API."""
    
    headers = {
        "DD-API-KEY": DATADOG_API_KEY,
        "DD-APPLICATION-KEY": DATADOG_APP_KEY,
    }
    
    # Build metric query to get all values for the specified field
    # Format: aggregation:metric{filters} by {field}
    
    # Start with aggregation and metric
    query = f"{aggregation}:{metric_name}"
    
    # Add filters
    filters = [f"service:{service}"]
    
    # Add environment filters if specified
    if environment:
        if len(environment) == 1:
            filters.append(f"env:{environment[0]}")
        else:
            env_filter = "env:" + " OR env:".join(environment)
            filters.append(f"({env_filter})")
    
    # Add filters to query
    if filters:
        query += "{" + ",".join(filters) + "}"
    
    # Add 'by' clause for the field we want to get values for
    query += f" by {{{field_name}}}"
    
    # Calculate time range in seconds
    import time
    to_timestamp = int(time.time())
    
    time_deltas = {
        "1h": 3600,
        "4h": 14400,
        "8h": 28800,
        "1d": 86400,
        "7d": 604800,
        "14d": 1209600,
        "30d": 2592000,
    }
    
    seconds_back = time_deltas.get(time_range, 3600)
    from_timestamp = to_timestamp - seconds_back
    
    # Use GET request with query parameters
    params = {
        "query": query,
        "from": from_timestamp,
        "to": to_timestamp,
    }
    
    url = f"{DATADOG_API_URL}/api/v1/query"
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            
            field_values = set()
            
            # Extract field values from the series data
            if "series" in data:
                for series in data["series"]:
                    # Check scope for field values
                    if "scope" in series:
                        scope = series["scope"]
                        # Parse scope to extract field values
                        # Scope format is typically "field1:value1,field2:value2"
                        for scope_item in scope.split(","):
                            if ":" in scope_item:
                                field, value = scope_item.split(":", 1)
                                field = field.strip()
                                value = value.strip()
                                if field == field_name:
                                    field_values.add(value)
                    
                    # Check tags for field values
                    if "tags" in series:
                        for tag in series["tags"]:
                            if ":" in tag:
                                tag_field, tag_value = tag.split(":", 1)
                                tag_field = tag_field.strip()
                                tag_value = tag_value.strip()
                                if tag_field == field_name:
                                    field_values.add(tag_value)
                    
                    # Check display_name for additional context
                    if "display_name" in series:
                        display_name = series["display_name"]
                        # Display name might contain field values in format like "field:value"
                        if f"{field_name}:" in display_name:
                            parts = display_name.split(f"{field_name}:")
                            if len(parts) > 1:
                                # Extract value after field_name:
                                value_part = parts[1].split(",")[0].split("}")[0].strip()
                                if value_part:
                                    field_values.add(value_part)
            
            return sorted(list(field_values))
            
        except httpx.HTTPError as e:
            logger.error(f"HTTP error fetching field values: {e}")
            logger.error(f"Query: {query}")
            # Check if it's a 400 error which might indicate invalid metric
            if hasattr(e, 'response') and e.response.status_code == 400:
                return []  # Return empty list for invalid metrics
            raise
        except Exception as e:
            logger.error(f"Error fetching field values: {e}")
            # For any other error, return empty list
            return []
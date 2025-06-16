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

# Datadog API configuration loaded from environment

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


async def fetch_logs(
    time_range: str = "1h",
    filters: Optional[Dict[str, str]] = None,
    query: Optional[str] = None,
    limit: int = 100,
) -> List[Dict[str, Any]]:
    """Fetch logs from Datadog API with flexible filtering."""
    url = f"{DATADOG_API_URL}/api/v2/logs/events/search"
    
    headers = {
        "Content-Type": "application/json",
        "DD-API-KEY": DATADOG_API_KEY,
        "DD-APPLICATION-KEY": DATADOG_APP_KEY,
    }
    
    # Build query filter
    query_parts = []
    
    # Add filters from the filters dictionary
    if filters:
        for key, value in filters.items():
            query_parts.append(f"{key}:{value}")
    
    # Add free-text query
    if query:
        query_parts.append(query)
    
    combined_query = " AND ".join(query_parts) if query_parts else "*"
    
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


# Backward compatibility alias
async def fetch_service_logs(
    service: Optional[str] = None,
    time_range: str = "1h",
    environment: Optional[List[str]] = None,
    log_level: Optional[str] = None,
    query: Optional[str] = None,
    limit: int = 100,
) -> List[Dict[str, Any]]:
    """Backward compatibility wrapper for fetch_logs."""
    filters = {}
    if service:
        filters["service"] = service
    if environment and len(environment) > 0:
        # Use first environment for simplicity
        filters["env"] = environment[0]
    if log_level:
        filters["status"] = log_level
    
    return await fetch_logs(
        time_range=time_range,
        filters=filters,
        query=query,
        limit=limit,
    )


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
    metric_name: str,
    field_name: str,
) -> List[str]:
    """Fetch all possible values for a specific field of a metric from Datadog API."""
    
    headers = {
        "DD-API-KEY": DATADOG_API_KEY,
        "DD-APPLICATION-KEY": DATADOG_APP_KEY,
    }
    
    # Use the same endpoint as get_metric_fields but extract values for specific field
    url = f"{DATADOG_API_URL}/api/v2/metrics/{metric_name}/all-tags"
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            field_values = set()
            
            # Extract values for the specific field from the tags
            if "data" in data and "attributes" in data["data"]:
                attributes = data["data"]["attributes"]
                
                # Get tags from the attributes
                if "tags" in attributes:
                    for tag in attributes["tags"]:
                        # Tags are in format "field:value", extract values for the specific field
                        if ":" in tag:
                            tag_field, tag_value = tag.split(":", 1)
                            if tag_field == field_name:
                                field_values.add(tag_value)
            
            return sorted(list(field_values))
            
        except httpx.HTTPError as e:
            logger.error(f"HTTP error fetching metric field values: {e}")
            if hasattr(e, 'response') and e.response.status_code == 404:
                logger.warning(f"Metric '{metric_name}' not found")
                return []
            raise
        except Exception as e:
            logger.error(f"Error fetching metric field values: {e}")
            raise


async def fetch_service_definitions(
    page_size: int = 10,
    page_number: int = 0,
    schema_version: Optional[str] = None,
) -> Dict[str, Any]:
    """Fetch service definitions from Datadog API."""
    
    headers = {
        "DD-API-KEY": DATADOG_API_KEY,
        "DD-APPLICATION-KEY": DATADOG_APP_KEY,
    }
    
    # Use the service definitions endpoint
    url = f"{DATADOG_API_URL}/api/v2/services/definitions"
    
    # Build query parameters
    params = {
        "page[size]": page_size,
        "page[number]": page_number,
    }
    
    if schema_version:
        params["filter[schema_version]"] = schema_version
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, params=params)
            response.raise_for_status()
            return response.json()
            
        except httpx.HTTPError as e:
            logger.error(f"HTTP error fetching service definitions: {e}")
            raise
        except Exception as e:
            logger.error(f"Error fetching service definitions: {e}")
            raise


async def fetch_service_definition(
    service_name: str,
    schema_version: str = "v2.2",
) -> Dict[str, Any]:
    """Fetch a single service definition from Datadog API."""
    
    headers = {
        "DD-API-KEY": DATADOG_API_KEY,
        "DD-APPLICATION-KEY": DATADOG_APP_KEY,
    }
    
    # Use the specific service definition endpoint
    url = f"{DATADOG_API_URL}/api/v2/services/definitions/{service_name}"
    
    # Build query parameters
    params = {
        "schema_version": schema_version,
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, params=params)
            response.raise_for_status()
            return response.json()
            
        except httpx.HTTPError as e:
            logger.error(f"HTTP error fetching service definition for '{service_name}': {e}")
            if hasattr(e, 'response') and e.response.status_code == 404:
                logger.warning(f"Service definition for '{service_name}' not found")
            raise
        except Exception as e:
            logger.error(f"Error fetching service definition for '{service_name}': {e}")
            raise
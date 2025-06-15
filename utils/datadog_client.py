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
    environment: Optional[str] = None,
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
        query_parts.append(f"env:{environment}")
    
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


async def fetch_service_metrics(
    service: str,
    metric_name: str,
    time_range: str = "1h",
    environment: Optional[str] = None,
    aggregation: str = "avg",
) -> Dict[str, Any]:
    """Fetch service metrics from Datadog API."""
    
    headers = {
        "DD-API-KEY": DATADOG_API_KEY,
        "DD-APPLICATION-KEY": DATADOG_APP_KEY,
    }
    
    # Build metric query
    query_parts = [f"{aggregation}:{metric_name}"]
    
    # Add service filter
    filters = [f"service:{service}"]
    
    # Add environment filter if specified
    if environment:
        filters.append(f"env:{environment}")
    
    # Combine filters with proper syntax
    if filters:
        query_parts.append("{" + ",".join(filters) + "}")
    
    query = "".join(query_parts)
    
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


async def fetch_multiple_metrics(
    service: str,
    metric_names: List[str],
    time_range: str = "1h",
    environment: Optional[str] = None,
    aggregation: str = "avg",
) -> Dict[str, Dict[str, Any]]:
    """Fetch multiple metrics for a service."""
    results = {}
    
    for metric_name in metric_names:
        try:
            result = await fetch_service_metrics(
                service=service,
                metric_name=metric_name,
                time_range=time_range,
                environment=environment,
                aggregation=aggregation,
            )
            results[metric_name] = result
        except Exception as e:
            logger.error(f"Error fetching metric {metric_name}: {e}")
            results[metric_name] = {"error": str(e)}
    
    return results
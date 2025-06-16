#!/usr/bin/env python3
"""Test script to check environment variables"""

import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    logger.info("Testing environment variables...")
    
    dd_api_key = os.getenv("DD_API_KEY")
    dd_app_key = os.getenv("DD_APP_KEY")
    
    logger.info(f"DD_API_KEY: {dd_api_key[:10]}..." if dd_api_key else "DD_API_KEY is None/empty")
    logger.info(f"DD_APP_KEY: {dd_app_key[:10]}..." if dd_app_key else "DD_APP_KEY is None/empty")
    logger.info(f"DD_API_KEY length: {len(dd_api_key) if dd_api_key else 0}")
    logger.info(f"DD_APP_KEY length: {len(dd_app_key) if dd_app_key else 0}")
    
    # Test if we can import the datadog client
    try:
        from utils.datadog_client import DATADOG_API_KEY, DATADOG_APP_KEY
        logger.info("Successfully imported datadog client")
        logger.info(f"Client DD_API_KEY: {DATADOG_API_KEY[:10]}..." if DATADOG_API_KEY else "Client DD_API_KEY is None/empty")
        logger.info(f"Client DD_APP_KEY: {DATADOG_APP_KEY[:10]}..." if DATADOG_APP_KEY else "Client DD_APP_KEY is None/empty")
    except Exception as e:
        logger.error(f"Failed to import datadog client: {e}")

if __name__ == "__main__":
    main()
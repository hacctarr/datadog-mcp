#!/usr/bin/env python3
"""
Test script for the Datadog MCP server
"""

import asyncio
import json
import os
from server import fetch_ci_pipelines, extract_pipeline_info, format_as_table

async def test_server():
    """Test the server functionality"""
    print("Testing Datadog MCP Server...")
    
    # Check environment variables
    if not os.getenv("DD_API_KEY") or not os.getenv("DD_APP_KEY"):
        print("❌ DD_API_KEY and DD_APP_KEY environment variables must be set")
        return
    
    print("✅ Environment variables are set")
    
    try:
        # Test fetching pipelines
        print("🔍 Fetching CI pipelines...")
        events = await fetch_ci_pipelines(limit=10)
        print(f"✅ Successfully fetched {len(events)} pipeline events")
        
        # Test extracting pipeline info
        pipelines = extract_pipeline_info(events)
        print(f"✅ Extracted {len(pipelines)} unique pipelines")
        
        # Test table formatting
        table = format_as_table(pipelines[:5])  # Show first 5
        print("✅ Table formatting works")
        print("\nSample output:")
        print(table)
        
        # Test filtering by repository
        print("\n🔍 Testing repository filtering...")
        filtered_events = await fetch_ci_pipelines(repository="shelfio/shelf-api-content", limit=5)
        filtered_pipelines = extract_pipeline_info(filtered_events)
        print(f"✅ Found {len(filtered_pipelines)} pipelines for shelf-api-content")
        
        if filtered_pipelines:
            print("\nFiltered results:")
            print(format_as_table(filtered_pipelines))
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return
    
    print("\n🎉 All tests passed! Server is ready to use.")

if __name__ == "__main__":
    asyncio.run(test_server())
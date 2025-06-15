#!/usr/bin/env python3
"""
Simple test for modular components
"""

import asyncio
import os

async def test_simple():
    """Simple test of imports and basic functionality"""
    print("Testing modular components...")
    
    # Check environment variables
    if not os.getenv("DD_API_KEY") or not os.getenv("DD_APP_KEY"):
        print("❌ DD_API_KEY and DD_APP_KEY environment variables must be set")
        return
    
    print("✅ Environment variables are set")
    
    try:
        # Test imports
        from utils.datadog_client import fetch_ci_pipelines
        from utils.formatters import extract_pipeline_info, format_as_table
        from tools.list_pipelines import get_tool_definition
        print("✅ All imports successful")
        
        # Test tool definition
        tool_def = get_tool_definition()
        print(f"✅ Tool definition: {tool_def.name}")
        
        # Test API call
        print("🔍 Testing API call...")
        events = await fetch_ci_pipelines(limit=5)
        print(f"✅ Fetched {len(events)} events")
        
        # Test data processing
        pipelines = extract_pipeline_info(events)
        print(f"✅ Extracted {len(pipelines)} pipelines")
        
        # Test formatting
        table = format_as_table(pipelines)
        print("✅ Table formatting works")
        print("\nSample output:")
        print(table[:200] + "..." if len(table) > 200 else table)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print("\n🎉 All modular components work!")

if __name__ == "__main__":
    asyncio.run(test_simple())
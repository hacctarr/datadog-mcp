#!/usr/bin/env python3
"""
Test script for the modular Datadog MCP server
"""

import asyncio
import os
from tools.list_pipelines import handle_call, get_tool_definition
from tools.get_fingerprints import handle_call as handle_fingerprints_call
from mcp.types import CallToolRequest

async def test_modular_server():
    """Test the modular server functionality"""
    print("Testing Modular Datadog MCP Server...")
    
    # Check environment variables
    if not os.getenv("DD_API_KEY") or not os.getenv("DD_APP_KEY"):
        print("❌ DD_API_KEY and DD_APP_KEY environment variables must be set")
        return
    
    print("✅ Environment variables are set")
    
    try:
        # Test tool definition
        tool_def = get_tool_definition()
        print(f"✅ Tool definition created: {tool_def.name}")
        
        # Test list_ci_pipelines tool
        print("🔍 Testing list_ci_pipelines tool...")
        request = CallToolRequest(
            method="tools/call",
            params={
                "name": "list_ci_pipelines",
                "arguments": {"limit": 5}
            }
        )
        result = await handle_call(request)
        
        if not result.isError:
            print("✅ list_ci_pipelines tool works")
            content = result.content[0].text
            print("Sample output:")
            print(content[:300] + "..." if len(content) > 300 else content)
        else:
            print(f"❌ list_ci_pipelines tool failed: {result.content[0].text}")
            return
        
        # Test get_pipeline_fingerprints tool
        print("\n🔍 Testing get_pipeline_fingerprints tool...")
        request = CallToolRequest(
            name="get_pipeline_fingerprints",
            arguments={"repositories": ["shelfio/shelf-api-content"]}
        )
        result = await handle_fingerprints_call(request)
        
        if not result.isError:
            print("✅ get_pipeline_fingerprints tool works")
        else:
            print(f"❌ get_pipeline_fingerprints tool failed: {result.content[0].text}")
            return
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return
    
    print("\n🎉 All modular tests passed! Server is ready to use.")

if __name__ == "__main__":
    asyncio.run(test_modular_server())
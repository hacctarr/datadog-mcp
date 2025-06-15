#!/usr/bin/env python3
"""
Test script for the service logs functionality
"""

import asyncio
import os

async def test_logs():
    """Test the logs functionality"""
    print("Testing Service Logs...")
    
    # Check environment variables
    if not os.getenv("DD_API_KEY") or not os.getenv("DD_APP_KEY"):
        print("❌ DD_API_KEY and DD_APP_KEY environment variables must be set")
        return
    
    print("✅ Environment variables are set")
    
    try:
        # Test imports
        from utils.datadog_client import fetch_service_logs
        from utils.formatters import extract_log_info, format_logs_as_table, format_logs_as_text
        from tools.get_service_logs import get_tool_definition
        print("✅ All imports successful")
        
        # Test tool definition
        tool_def = get_tool_definition()
        print(f"✅ Tool definition: {tool_def.name}")
        
        # Test API call for different time ranges
        test_service = "content"
        time_ranges = ["1h", "4h", "8h", "1d"]
        
        for time_range in time_ranges:
            print(f"🔍 Testing {time_range} logs for {test_service}...")
            
            try:
                log_events = await fetch_service_logs(
                    service=test_service,
                    time_range=time_range,
                    limit=5
                )
                
                logs = extract_log_info(log_events)
                print(f"✅ Found {len(logs)} logs for {time_range}")
                
                if logs:
                    # Test table formatting
                    table = format_logs_as_table(logs[:2])  # Show first 2
                    print(f"Sample table format:")
                    print(table[:200] + "..." if len(table) > 200 else table)
                    
                    # Test text formatting
                    text = format_logs_as_text(logs[:1])  # Show first 1
                    print(f"Sample text format:")
                    print(text[:100] + "..." if len(text) > 100 else text)
                    print()
                
            except Exception as e:
                print(f"❌ Error for {time_range}: {e}")
        
        # Test with log level filter
        print("🔍 Testing with error level filter...")
        error_events = await fetch_service_logs(
            service=test_service,
            time_range="1d",
            log_level="error",
            limit=3
        )
        
        error_logs = extract_log_info(error_events)
        print(f"✅ Found {len(error_logs)} error logs")
        
        if error_logs:
            text = format_logs_as_text(error_logs)
            print("Sample error logs:")
            print(text[:300] + "..." if len(text) > 300 else text)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print("\n🎉 Logs functionality works!")

if __name__ == "__main__":
    asyncio.run(test_logs())
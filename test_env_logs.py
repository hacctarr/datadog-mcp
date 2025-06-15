#!/usr/bin/env python3
"""
Test script for environment-specific service logs
"""

import asyncio
import os

async def test_environment_logs():
    """Test environment filtering in logs"""
    print("Testing Environment-Specific Service Logs...")
    
    # Check environment variables
    if not os.getenv("DD_API_KEY") or not os.getenv("DD_APP_KEY"):
        print("❌ DD_API_KEY and DD_APP_KEY environment variables must be set")
        return
    
    print("✅ Environment variables are set")
    
    try:
        from utils.datadog_client import fetch_service_logs
        from utils.formatters import extract_log_info, format_logs_as_table
        print("✅ All imports successful")
        
        test_service = "content"
        environments = ["prod", "staging", "backoffice"]
        
        for env in environments:
            print(f"\n🔍 Testing {env} environment for {test_service}...")
            
            try:
                log_events = await fetch_service_logs(
                    service=test_service,
                    time_range="1d",
                    environment=env,
                    limit=5
                )
                
                logs = extract_log_info(log_events)
                print(f"✅ Found {len(logs)} logs in {env} environment")
                
                if logs:
                    # Show sample log with environment info
                    sample_log = logs[0]
                    print(f"   Sample log: {sample_log.get('timestamp', 'N/A')} - {sample_log.get('message', 'N/A')[:60]}...")
                    
                    # Check if environment is properly extracted
                    if 'environment' in sample_log:
                        print(f"   Environment field: {sample_log['environment']}")
                    else:
                        print("   No environment field in log data")
                
            except Exception as e:
                print(f"❌ Error testing {env}: {e}")
        
        # Test combination of environment and log level
        print(f"\n🔍 Testing prod environment with error level...")
        try:
            error_events = await fetch_service_logs(
                service=test_service,
                time_range="7d",
                environment="prod",
                log_level="error",
                limit=3
            )
            
            error_logs = extract_log_info(error_events)
            print(f"✅ Found {len(error_logs)} error logs in prod environment")
            
            if error_logs:
                table = format_logs_as_table(error_logs)
                print("Sample error logs:")
                print(table[:300] + "..." if len(table) > 300 else table)
            
        except Exception as e:
            print(f"❌ Error testing prod errors: {e}")
        
        # Test with custom query and environment
        print(f"\n🔍 Testing staging environment with custom query...")
        try:
            query_events = await fetch_service_logs(
                service=test_service,
                time_range="1d",
                environment="staging",
                query="lambda OR function",
                limit=3
            )
            
            query_logs = extract_log_info(query_events)
            print(f"✅ Found {len(query_logs)} logs matching query in staging")
            
        except Exception as e:
            print(f"❌ Error testing staging query: {e}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print("\n🎉 Environment filtering works!")

if __name__ == "__main__":
    asyncio.run(test_environment_logs())
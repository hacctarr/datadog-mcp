#!/usr/bin/env python3
"""
Test script for the service metrics functionality
"""

import asyncio
import os

async def test_metrics():
    """Test the metrics functionality"""
    print("Testing Service Metrics...")
    
    # Check environment variables
    if not os.getenv("DD_API_KEY") or not os.getenv("DD_APP_KEY"):
        print("❌ DD_API_KEY and DD_APP_KEY environment variables must be set")
        return
    
    print("✅ Environment variables are set")
    
    try:
        # Test imports
        from utils.datadog_client import fetch_service_metrics, fetch_multiple_metrics
        from utils.formatters import (
            extract_metrics_info,
            format_metrics_table,
            format_metrics_summary,
            format_metrics_timeseries
        )
        from tools.get_service_metrics import get_tool_definition
        print("✅ All imports successful")
        
        # Test tool definition
        tool_def = get_tool_definition()
        print(f"✅ Tool definition: {tool_def.name}")
        
        # Test single metric fetch
        test_service = "content"
        test_metric = "aws.lambda.invocations"
        
        print(f"🔍 Testing single metric fetch for {test_service}...")
        single_result = await fetch_service_metrics(
            service=test_service,
            metric_name=test_metric,
            time_range="1h",
            aggregation="avg"
        )
        
        metric_info = extract_metrics_info(single_result)
        print(f"✅ Single metric fetch successful")
        print(f"   Metric: {metric_info['metric']}")
        print(f"   Points: {len(metric_info['points'])}")
        print(f"   Unit: {metric_info['unit']}")
        
        # Test multiple metrics fetch
        test_metrics = [
            "aws.lambda.invocations",
            "aws.lambda.duration",
            "aws.lambda.errors"
        ]
        
        print(f"\n🔍 Testing multiple metrics fetch...")
        multiple_results = await fetch_multiple_metrics(
            service=test_service,
            metric_names=test_metrics,
            time_range="1h"
        )
        
        print(f"✅ Multiple metrics fetch successful")
        print(f"   Retrieved {len(multiple_results)} metrics")
        
        for metric_name, data in multiple_results.items():
            if "error" in data:
                print(f"   ❌ {metric_name}: {data['error']}")
            else:
                info = extract_metrics_info(data)
                print(f"   ✅ {metric_name}: {len(info['points'])} points")
        
        # Test different time ranges
        time_ranges = ["1h", "4h", "1d"]
        print(f"\n🔍 Testing different time ranges...")
        
        for time_range in time_ranges:
            try:
                result = await fetch_service_metrics(
                    service=test_service,
                    metric_name="aws.lambda.invocations",
                    time_range=time_range
                )
                info = extract_metrics_info(result)
                print(f"   ✅ {time_range}: {len(info['points'])} points")
            except Exception as e:
                print(f"   ❌ {time_range}: {e}")
        
        # Test formatting
        print(f"\n🔍 Testing formatting...")
        
        # Table format
        table_output = format_metrics_table(multiple_results)
        print("✅ Table format works")
        print("Sample table:")
        print(table_output[:300] + "..." if len(table_output) > 300 else table_output)
        
        # Summary format
        summary_output = format_metrics_summary(multiple_results)
        print("\n✅ Summary format works")
        print("Sample summary:")
        print(summary_output[:300] + "..." if len(summary_output) > 300 else summary_output)
        
        # Test with environment filter
        print(f"\n🔍 Testing environment filtering...")
        try:
            env_result = await fetch_service_metrics(
                service=test_service,
                metric_name="aws.lambda.invocations",
                time_range="1h",
                environment="prod"
            )
            env_info = extract_metrics_info(env_result)
            print(f"✅ Environment filtering works: {len(env_info['points'])} points for prod")
        except Exception as e:
            print(f"❌ Environment filtering error: {e}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print("\n🎉 Metrics functionality works!")

if __name__ == "__main__":
    asyncio.run(test_metrics())
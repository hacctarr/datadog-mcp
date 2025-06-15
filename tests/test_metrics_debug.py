#!/usr/bin/env python3
"""
Debug script for metrics API
"""

import asyncio
import os

async def debug_metrics():
    """Debug metrics API calls"""
    print("Debugging Metrics API...")
    
    try:
        from utils.datadog_client import fetch_metrics
        
        # Try different metric names that might exist
        test_metrics = [
            "datadog.estimated_usage.logs.ingested_bytes",
            "datadog.estimated_usage.logs.indexed_logs",
            "trace.servlet.request.duration",
            "trace.servlet.request.hits"
        ]
        
        for metric in test_metrics:
            print(f"\n🔍 Testing metric: {metric}")
            try:
                result = await fetch_metrics(
                    metric_name=metric,
                    time_range="1d",
                    filters={"service": "content"}
                )
                
                print(f"   Status: {result.get('status', 'unknown')}")
                print(f"   Series count: {len(result.get('series', []))}")
                if result.get('series'):
                    series = result['series'][0]
                    print(f"   First series: {series.get('metric', 'unknown')}")
                    print(f"   Points: {len(series.get('pointlist', []))}")
                
            except Exception as e:
                print(f"   Error: {e}")
        
        # Try without service filter
        print(f"\n🔍 Testing without service filter...")
        try:
            result = await fetch_metrics(
                metric_name="datadog.estimated_usage.logs.ingested_bytes",
                time_range="1d"
            )
            print(f"   Status: {result.get('status', 'unknown')}")
            print(f"   Series count: {len(result.get('series', []))}")
            
        except Exception as e:
            print(f"   Error: {e}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_metrics())
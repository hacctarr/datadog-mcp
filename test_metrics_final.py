#!/usr/bin/env python3
"""
Final test script for metrics with real data
"""

import asyncio
import os

async def test_metrics_final():
    """Test metrics with real data"""
    print("Testing Service Metrics with Real Data...")
    
    try:
        from utils.datadog_client import fetch_service_metrics, fetch_multiple_metrics
        from utils.formatters import format_metrics_table, format_metrics_summary
        
        # Test single metric with data
        print("🔍 Testing single metric with data...")
        result = await fetch_service_metrics(
            service="content",
            metric_name="datadog.estimated_usage.logs.ingested_bytes",
            time_range="1d"
        )
        
        print(f"✅ Status: {result.get('status')}")
        if result.get('series'):
            series = result['series'][0]
            points = series.get('pointlist', [])
            print(f"✅ Points: {len(points)}")
            
            if points:
                # Show last few values
                recent_points = points[-3:]
                print("Recent values:")
                for timestamp, value in recent_points:
                    if value is not None:
                        import datetime
                        # Datadog timestamps are in milliseconds
                        dt = datetime.datetime.fromtimestamp(timestamp / 1000)
                        print(f"  {dt.strftime('%H:%M')}: {value:.0f}")
        
        # Test multiple metrics
        print(f"\n🔍 Testing multiple metrics...")
        metrics_to_test = [
            "datadog.estimated_usage.logs.ingested_bytes",
            "datadog.estimated_usage.logs.indexed_logs"
        ]
        
        multiple_results = await fetch_multiple_metrics(
            service="content",
            metric_names=metrics_to_test,
            time_range="4h"
        )
        
        print(f"✅ Retrieved {len(multiple_results)} metrics")
        
        # Test table formatting with real data
        print(f"\n🔍 Testing table formatting...")
        table = format_metrics_table(multiple_results)
        print("Metrics Table:")
        print(table)
        
        # Test summary formatting
        print(f"\n🔍 Testing summary formatting...")
        summary = format_metrics_summary(multiple_results)
        print("Metrics Summary:")
        print(summary[:500] + "..." if len(summary) > 500 else summary)
        
        # Test different time ranges
        print(f"\n🔍 Testing different time ranges...")
        time_ranges = ["1h", "4h", "1d"]
        
        for time_range in time_ranges:
            result = await fetch_service_metrics(
                service="content",
                metric_name="datadog.estimated_usage.logs.ingested_bytes",
                time_range=time_range
            )
            
            if result.get('series'):
                points = result['series'][0].get('pointlist', [])
                print(f"   {time_range}: {len(points)} points")
            else:
                print(f"   {time_range}: No data")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print("\n🎉 Metrics with real data work perfectly!")

if __name__ == "__main__":
    asyncio.run(test_metrics_final())
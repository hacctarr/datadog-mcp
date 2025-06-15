#!/usr/bin/env python3
"""
Test script for the teams functionality
"""

import asyncio
import os

async def test_teams():
    """Test the teams functionality"""
    print("Testing Teams and Members...")
    
    # Check environment variables
    if not os.getenv("DD_API_KEY") or not os.getenv("DD_APP_KEY"):
        print("❌ DD_API_KEY and DD_APP_KEY environment variables must be set")
        return
    
    print("✅ Environment variables are set")
    
    try:
        # Test imports
        from utils.datadog_client import fetch_teams, fetch_team_memberships
        from utils.formatters import extract_team_info, extract_membership_info, format_teams_as_table
        from tools.get_teams import get_tool_definition
        print("✅ All imports successful")
        
        # Test tool definition
        tool_def = get_tool_definition()
        print(f"✅ Tool definition: {tool_def.name}")
        
        # Test fetching teams
        print("🔍 Testing teams API...")
        teams_data = await fetch_teams()
        teams = extract_team_info(teams_data)
        print(f"✅ Found {len(teams)} teams")
        
        if teams:
            # Show teams table
            table = format_teams_as_table(teams[:5])  # Show first 5
            print("Sample teams table:")
            print(table)
            print()
            
            # Test fetching members for first team
            first_team = teams[0]
            team_id = first_team.get("id")
            team_name = first_team.get("name")
            
            if team_id:
                print(f"🔍 Testing memberships for team '{team_name}'...")
                try:
                    memberships_data = await fetch_team_memberships(team_id)
                    members = extract_membership_info(memberships_data)
                    print(f"✅ Found {len(members)} members in team '{team_name}'")
                    
                    if members:
                        print("Sample members:")
                        for member in members[:3]:  # Show first 3
                            role = member.get("role", "unknown")
                            position = member.get("position", "")
                            user_id = member.get("user_id", "")
                            print(f"  • {role}" + (f" - {position}" if position else "") + (f" (ID: {user_id})" if user_id else ""))
                    
                except Exception as e:
                    print(f"❌ Error fetching members: {e}")
            else:
                print("⚠️  No team ID found for membership testing")
        
        # Test team filtering
        if teams:
            print(f"\n🔍 Testing team name filtering...")
            sample_team_name = teams[0].get("name", "").split()[0]  # Get first word of team name
            filtered_teams = [t for t in teams if sample_team_name.lower() in t.get("name", "").lower()]
            print(f"✅ Found {len(filtered_teams)} teams matching '{sample_team_name}'")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print("\n🎉 Teams functionality works!")

if __name__ == "__main__":
    asyncio.run(test_teams())
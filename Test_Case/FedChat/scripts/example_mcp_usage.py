#!/usr/bin/env python3
"""
Example: Using ServiceNow and Splunk MCP integrations
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from services.mcp_service import MCPService


async def servicenow_examples():
    """Demonstrate ServiceNow MCP tools"""
    print("=" * 70)
    print("ServiceNow MCP Integration Examples")
    print("=" * 70)
    
    mcp = MCPService()
    
    # Example 1: Create an incident
    print("\n1. Creating a new incident...")
    result = await mcp.execute_tool(
        tool_name="create_incident",
        args={
            "short_description": "Database performance degradation",
            "description": "Users reporting slow response times. Database queries taking longer than usual.",
            "urgency": "2",
            "impact": "2",
            "category": "Database",
            "assignment_group": "Database Operations"
        },
        server="servicenow"
    )
    
    if result["success"]:
        incident_number = result["data"]["result"]["number"]
        print(f"✅ Incident created: {incident_number}")
        
        # Example 2: Get incident details
        print(f"\n2. Retrieving incident {incident_number}...")
        result = await mcp.execute_tool(
            tool_name="get_incident",
            args={"incident_number": incident_number},
            server="servicenow"
        )
        
        if result["success"]:
            incident = result["data"]["result"][0]
            print(f"✅ Status: {incident.get('state')}")
            print(f"   Priority: {incident.get('priority')}")
            print(f"   Assigned to: {incident.get('assigned_to')}")
        
        # Example 3: Update incident
        print(f"\n3. Updating incident {incident_number}...")
        result = await mcp.execute_tool(
            tool_name="update_incident",
            args={
                "incident_number": incident_number,
                "fields": {
                    "state": "2",  # In Progress
                    "work_notes": "Investigation in progress. Checking database logs."
                }
            },
            server="servicenow"
        )
        
        if result["success"]:
            print("✅ Incident updated successfully")
    else:
        print(f"❌ Error: {result['error']}")
    
    # Example 4: Search incidents
    print("\n4. Searching for open database incidents...")
    result = await mcp.execute_tool(
        tool_name="search_incidents",
        args={
            "query": "database",
            "state": "2",  # In Progress
            "limit": 5
        },
        server="servicenow"
    )
    
    if result["success"]:
        incidents = result["data"]["result"]
        print(f"✅ Found {len(incidents)} incidents")
        for inc in incidents[:3]:
            print(f"   - {inc['number']}: {inc['short_description']}")
    
    # Example 5: Create change request
    print("\n5. Creating a change request...")
    result = await mcp.execute_tool(
        tool_name="create_change_request",
        args={
            "short_description": "Upgrade database server memory",
            "description": "Increase database server RAM from 32GB to 64GB to improve performance",
            "type": "Normal",
            "risk": "Moderate",
            "impact": "2"
        },
        server="servicenow"
    )
    
    if result["success"]:
        change_number = result["data"]["result"]["number"]
        print(f"✅ Change request created: {change_number}")
    else:
        print(f"❌ Error: {result.get('error')}")


async def splunk_examples():
    """Demonstrate Splunk MCP tools"""
    print("\n" + "=" * 70)
    print("Splunk MCP Integration Examples")
    print("=" * 70)
    
    mcp = MCPService()
    
    # Example 1: Search logs
    print("\n1. Searching for application errors...")
    result = await mcp.execute_tool(
        tool_name="search_logs",
        args={
            "query": "index=main sourcetype=application error OR exception",
            "earliest_time": "-1h",
            "latest_time": "now",
            "max_results": 10
        },
        server="splunk"
    )
    
    if result["success"]:
        results = result.get("results", {}).get("results", [])
        print(f"✅ Found {len(results)} error events in last hour")
        if results:
            print(f"   Latest error: {results[0].get('_raw', 'N/A')[:100]}...")
    else:
        print(f"❌ Error: {result['error']}")
    
    # Example 2: Get notable events
    print("\n2. Retrieving high-severity notable events...")
    result = await mcp.execute_tool(
        tool_name="get_notable_events",
        args={
            "time_range": "-24h",
            "severity": "high",
            "limit": 10
        },
        server="splunk"
    )
    
    if result["success"]:
        events = result.get("events", [])
        print(f"✅ Found {len(events)} notable events")
        for event in events[:3]:
            print(f"   - {event.get('title', 'N/A')}")
    else:
        print(f"❌ Error: {result.get('error')}")
    
    # Example 3: Create notable event
    print("\n3. Creating a security notable event...")
    result = await mcp.execute_tool(
        tool_name="create_notable_event",
        args={
            "title": "Suspicious API access pattern detected",
            "description": "Multiple API calls from unexpected IP address range",
            "severity": "medium",
            "owner": "security-operations"
        },
        server="splunk"
    )
    
    if result["success"]:
        print("✅ Notable event created successfully")
    else:
        print(f"❌ Error: {result.get('error')}")
    
    # Example 4: Run saved search
    print("\n4. Running saved search...")
    result = await mcp.execute_tool(
        tool_name="run_saved_search",
        args={
            "search_name": "Daily Security Summary",
            "earliest_time": "-1d"
        },
        server="splunk"
    )
    
    if result["success"]:
        job_id = result.get("job_id")
        print(f"✅ Search job dispatched: {job_id}")
        
        # Example 5: Get search results
        if job_id:
            print("\n5. Retrieving search results...")
            await asyncio.sleep(2)  # Wait for search to complete
            
            result = await mcp.execute_tool(
                tool_name="get_search_job_results",
                args={
                    "job_id": job_id,
                    "count": 5
                },
                server="splunk"
            )
            
            if result["success"]:
                results = result.get("results", [])
                print(f"✅ Retrieved {len(results)} results")
            else:
                print(f"❌ Error: {result.get('error')}")
    else:
        print(f"❌ Error: {result.get('error')}")


async def integrated_workflow():
    """Demonstrate integrated ServiceNow + Splunk workflow"""
    print("\n" + "=" * 70)
    print("Integrated Workflow: Splunk Detection → ServiceNow Incident")
    print("=" * 70)
    
    mcp = MCPService()
    
    # Step 1: Search Splunk for critical errors
    print("\n1. Searching Splunk for critical application errors...")
    splunk_result = await mcp.execute_tool(
        tool_name="search_logs",
        args={
            "query": "index=app level=critical OR level=fatal",
            "earliest_time": "-15m",
            "max_results": 50
        },
        server="splunk"
    )
    
    if splunk_result["success"]:
        error_count = len(splunk_result.get("results", {}).get("results", []))
        print(f"✅ Found {error_count} critical errors")
        
        # Step 2: If errors exceed threshold, create ServiceNow incident
        if error_count > 5:
            print(f"\n2. Error threshold exceeded ({error_count} > 5). Creating incident...")
            
            snow_result = await mcp.execute_tool(
                tool_name="create_incident",
                args={
                    "short_description": f"Critical application errors detected ({error_count} events)",
                    "description": f"Splunk detected {error_count} critical/fatal errors in the last 15 minutes. Immediate investigation required.",
                    "urgency": "1",  # High
                    "impact": "1",   # High
                    "category": "Application",
                    "assignment_group": "Application Support"
                },
                server="servicenow"
            )
            
            if snow_result["success"]:
                incident_number = snow_result["data"]["result"]["number"]
                print(f"✅ Incident created: {incident_number}")
                
                # Step 3: Create Splunk notable event with incident reference
                print(f"\n3. Creating notable event with incident reference...")
                
                splunk_notable = await mcp.execute_tool(
                    tool_name="create_notable_event",
                    args={
                        "title": f"ServiceNow Incident {incident_number} - Critical App Errors",
                        "description": f"Auto-created incident {incident_number} for {error_count} critical errors",
                        "severity": "high",
                        "owner": "incident-response"
                    },
                    server="splunk"
                )
                
                if splunk_notable["success"]:
                    print("✅ Notable event created with incident reference")
                
                print(f"\n🎯 Automated workflow complete!")
                print(f"   - {error_count} errors detected in Splunk")
                print(f"   - ServiceNow incident {incident_number} created")
                print(f"   - Notable event created for tracking")
        else:
            print(f"   Error count within threshold. No action needed.")
    else:
        print(f"❌ Splunk search failed: {splunk_result.get('error')}")


async def main():
    """Run all examples"""
    print("\nFedChat MCP Integration Examples")
    print("=" * 70)
    print("\nThis script demonstrates ServiceNow and Splunk integrations.")
    print("Ensure credentials are configured in your .env file.\n")
    
    try:
        # Run ServiceNow examples
        await servicenow_examples()
        
        # Run Splunk examples
        await splunk_examples()
        
        # Run integrated workflow
        await integrated_workflow()
        
        print("\n" + "=" * 70)
        print("All examples completed!")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n❌ Error running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

# MCP Integrations Guide

## Overview

FedChat includes Model Context Protocol (MCP) integrations for enterprise systems commonly used in federal environments. These integrations allow AI agents to interact with external systems securely and efficiently.

## Available Integrations

### 1. Filesystem
Access and manage files in approved directories.

### 2. Database
Query PostgreSQL database with read-only access.

### 3. API Client
Make HTTP requests to whitelisted APIs.

### 4. ServiceNow
Integration with ServiceNow for IT Service Management (ITSM).

### 5. Splunk
Integration with Splunk for log analysis and security operations.

---

## ServiceNow Integration

ServiceNow is an enterprise IT Service Management (ITSM) platform used for incident management, change management, and IT operations.

### Configuration

Add to your `.env` file:

```bash
# ServiceNow Configuration
SERVICENOW_INSTANCE_URL=https://your-instance.service-now.com
SERVICENOW_USERNAME=your-username
SERVICENOW_PASSWORD=your-password

# Enable in MCP servers list
ENABLED_MCP_SERVERS=filesystem,database,api-client,servicenow
```

### Available Tools

#### create_incident

Create a new incident in ServiceNow.

**Parameters:**
- `short_description` (required): Brief description of the incident
- `description` (optional): Detailed description
- `urgency` (optional): 1 (High), 2 (Medium), 3 (Low) - default: 3
- `impact` (optional): 1 (High), 2 (Medium), 3 (Low) - default: 3
- `category` (optional): Incident category
- `assignment_group` (optional): Group to assign the incident to

**Example:**
```python
result = await mcp_service.execute_tool(
    tool_name="create_incident",
    args={
        "short_description": "Web application not responding",
        "description": "Users cannot access the main application portal. Returns 503 error.",
        "urgency": "2",
        "impact": "2",
        "category": "Web Services",
        "assignment_group": "Web Operations"
    },
    server="servicenow"
)
```

**Response:**
```json
{
  "success": true,
  "data": {
    "result": {
      "number": "INC0010001",
      "sys_id": "abc123...",
      "short_description": "Web application not responding",
      "state": "1",
      "urgency": "2",
      "impact": "2"
    }
  },
  "status_code": 201
}
```

#### get_incident

Retrieve incident details by incident number.

**Parameters:**
- `incident_number` (required): Incident number (e.g., "INC0010001")

**Example:**
```python
result = await mcp_service.execute_tool(
    tool_name="get_incident",
    args={"incident_number": "INC0010001"},
    server="servicenow"
)
```

#### update_incident

Update an existing incident.

**Parameters:**
- `incident_number` (required): Incident number to update
- `fields` (required): Dictionary of fields to update

**Example:**
```python
result = await mcp_service.execute_tool(
    tool_name="update_incident",
    args={
        "incident_number": "INC0010001",
        "fields": {
            "state": "2",  # In Progress
            "assigned_to": "john.doe",
            "work_notes": "Investigation started"
        }
    },
    server="servicenow"
)
```

#### search_incidents

Search for incidents with filters.

**Parameters:**
- `query` (optional): Search query string
- `state` (optional): Incident state (1=New, 2=In Progress, 6=Resolved, 7=Closed)
- `assigned_to` (optional): Username of assigned person
- `limit` (optional): Maximum results (default: 10)

**Example:**
```python
result = await mcp_service.execute_tool(
    tool_name="search_incidents",
    args={
        "query": "network",
        "state": "2",
        "limit": 20
    },
    server="servicenow"
)
```

#### create_change_request

Create a new change request.

**Parameters:**
- `short_description` (required): Brief description of the change
- `description` (optional): Detailed change description
- `type` (optional): Change type (Normal, Standard, Emergency)
- `risk` (optional): Risk level (High, Moderate, Low)
- `impact` (optional): Impact level (1-3)

**Example:**
```python
result = await mcp_service.execute_tool(
    tool_name="create_change_request",
    args={
        "short_description": "Upgrade database server to latest version",
        "description": "Upgrade PostgreSQL from 15 to 16 for security patches",
        "type": "Normal",
        "risk": "Moderate",
        "impact": "2"
    },
    server="servicenow"
)
```

### Use Cases

**Incident Management:**
```
User: "Create an incident for the application timeout issue we're experiencing"

Agent: Uses create_incident to log the incident in ServiceNow and returns the incident number.
```

**Status Checks:**
```
User: "What's the status of incident INC0010001?"

Agent: Uses get_incident to retrieve current status and details.
```

**Bulk Operations:**
```
User: "Show me all high-priority incidents assigned to the web team"

Agent: Uses search_incidents with filters to retrieve matching incidents.
```

---

## Splunk Integration

Splunk is a platform for searching, monitoring, and analyzing machine-generated data through a web-style interface.

### Configuration

Add to your `.env` file:

```bash
# Splunk Configuration
SPLUNK_HOST=splunk.agency.gov
SPLUNK_PORT=8089
SPLUNK_API_TOKEN=your-splunk-api-token

# Enable in MCP servers list
ENABLED_MCP_SERVERS=filesystem,database,api-client,servicenow,splunk
```

### Available Tools

#### search_logs

Execute a Splunk search query using SPL (Search Processing Language).

**Parameters:**
- `query` (required): SPL search query
- `earliest_time` (optional): Start time (default: "-1h")
- `latest_time` (optional): End time (default: "now")
- `max_results` (optional): Maximum results (default: 100)

**Example:**
```python
result = await mcp_service.execute_tool(
    tool_name="search_logs",
    args={
        "query": "index=main sourcetype=access_combined status=500",
        "earliest_time": "-24h",
        "latest_time": "now",
        "max_results": 50
    },
    server="splunk"
)
```

**Response:**
```json
{
  "success": true,
  "job_id": "1234567890.12345",
  "results": {
    "results": [
      {
        "_time": "2024-01-09T10:30:00",
        "status": "500",
        "uri": "/api/users",
        "method": "GET"
      }
    ]
  },
  "status_code": 200
}
```

#### get_notable_events

Retrieve notable security events from Splunk Enterprise Security.

**Parameters:**
- `time_range` (optional): Time range (default: "-24h")
- `severity` (optional): Severity filter (low, medium, high, critical)
- `status` (optional): Status filter (new, in_progress, resolved)
- `limit` (optional): Maximum results (default: 50)

**Example:**
```python
result = await mcp_service.execute_tool(
    tool_name="get_notable_events",
    args={
        "time_range": "-7d",
        "severity": "high",
        "status": "new",
        "limit": 20
    },
    server="splunk"
)
```

#### create_notable_event

Create a notable event in Splunk Enterprise Security.

**Parameters:**
- `title` (required): Event title
- `description` (required): Detailed description
- `severity` (required): Severity level (low, medium, high, critical)
- `owner` (optional): Assigned owner

**Example:**
```python
result = await mcp_service.execute_tool(
    tool_name="create_notable_event",
    args={
        "title": "Unusual login pattern detected",
        "description": "Multiple failed login attempts from unusual IP addresses",
        "severity": "high",
        "owner": "security-team"
    },
    server="splunk"
)
```

#### run_saved_search

Execute a saved Splunk search.

**Parameters:**
- `search_name` (required): Name of the saved search
- `earliest_time` (optional): Override earliest time
- `latest_time` (optional): Override latest time

**Example:**
```python
result = await mcp_service.execute_tool(
    tool_name="run_saved_search",
    args={
        "search_name": "Security Threat Summary",
        "earliest_time": "-1d"
    },
    server="splunk"
)
```

**Response:**
```json
{
  "success": true,
  "job_id": "scheduler_admin_search_RMD59fa94b92b2434_at_1234567890_1",
  "message": "Saved search dispatched successfully"
}
```

#### get_search_job_results

Retrieve results from a Splunk search job.

**Parameters:**
- `job_id` (required): Search job ID
- `offset` (optional): Result offset (default: 0)
- `count` (optional): Number of results (default: 100)

**Example:**
```python
result = await mcp_service.execute_tool(
    tool_name="get_search_job_results",
    args={
        "job_id": "1234567890.12345",
        "offset": 0,
        "count": 50
    },
    server="splunk"
)
```

### Use Cases

**Security Investigation:**
```
User: "Show me all failed SSH login attempts in the last hour"

Agent: Uses search_logs with query "index=linux sourcetype=auth action=failure ssh" 
       and earliest_time="-1h"
```

**Notable Events Analysis:**
```
User: "What are the critical security alerts from yesterday?"

Agent: Uses get_notable_events with severity="critical" and time_range="-1d"
```

**Automated Response:**
```
User: "Create a security alert for the suspicious activity we detected"

Agent: Uses create_notable_event to log the security finding
```

**Scheduled Reporting:**
```
User: "Run the weekly security summary report"

Agent: Uses run_saved_search to execute pre-configured report
```

---

## Security Considerations

### Authentication

- **ServiceNow**: Uses Basic Authentication with username/password
  - Store credentials in environment variables
  - Use service accounts with minimal required permissions
  - Rotate passwords regularly per agency policy

- **Splunk**: Uses Bearer token authentication
  - Generate API tokens through Splunk UI (Settings > Tokens)
  - Store tokens securely in environment variables
  - Set appropriate token expiration

### Authorization

#### ServiceNow Permissions

Required roles for the service account:
- `itil` - Basic ITSM operations
- `incident_manager` - Incident management
- `change_manager` - Change management (if using CR tools)

#### Splunk Permissions

Required capabilities:
- `search` - Run searches
- `rest_properties_get` - Access REST API
- `admin_all_objects` (for notable events in ES)

### Network Security

1. **Use HTTPS only** - Both integrations require HTTPS
2. **Whitelist IPs** - Configure firewall rules to allow FedChat IPs
3. **VPN/Private Network** - Deploy within agency network when possible
4. **Certificate Validation** - Enable SSL certificate verification in production

### Audit Logging

All MCP tool executions are logged with:
- User who initiated the action
- Tool name and parameters
- Timestamp
- Result status
- IP address

Audit logs are retained for 7 years per FISMA requirements.

---

## Error Handling

### Common Errors

**ServiceNow:**
- `401 Unauthorized`: Check credentials
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Incident/record doesn't exist
- `Connection timeout`: Check network connectivity

**Splunk:**
- `401 Unauthorized`: Invalid or expired token
- `400 Bad Request`: Invalid SPL query syntax
- `404 Not Found`: Search job not found (may have expired)
- `Connection refused`: Check host/port configuration

### Example Error Response

```json
{
  "success": false,
  "error": "ServiceNow API error: 401",
  "details": "Invalid username or password"
}
```

---

## Testing

### Test ServiceNow Connection

```python
# Test get_incident with known incident
result = await mcp_service.execute_tool(
    tool_name="get_incident",
    args={"incident_number": "INC0000001"},
    server="servicenow"
)

print(result)
```

### Test Splunk Connection

```python
# Simple search test
result = await mcp_service.execute_tool(
    tool_name="search_logs",
    args={
        "query": "index=* | head 1",
        "max_results": 1
    },
    server="splunk"
)

print(result)
```

---

## Best Practices

### ServiceNow

1. **Use Assignment Groups**: Always specify assignment groups for better routing
2. **Include Work Notes**: Add detailed work notes when updating incidents
3. **Set Proper Priority**: Calculate priority based on urgency × impact matrix
4. **Link Related Items**: Reference related incidents, changes, or problems
5. **Close with Resolution**: Always add resolution notes when closing incidents

### Splunk

1. **Optimize Queries**: Use index and sourcetype filters to improve performance
2. **Limit Time Ranges**: Use specific time ranges to avoid searching all data
3. **Use Saved Searches**: Create saved searches for frequently run queries
4. **Field Extractions**: Define field extractions for common log formats
5. **Monitor Job Status**: Check search job status before retrieving results

---

## Troubleshooting

### ServiceNow "Instance not configured"

Check:
1. `SERVICENOW_INSTANCE_URL` is set correctly
2. URL includes `https://` prefix
3. Instance URL doesn't have trailing slash
4. Instance is accessible from FedChat network

### Splunk "Connection refused"

Check:
1. `SPLUNK_HOST` and `SPLUNK_PORT` are correct
2. Port 8089 is open in firewall
3. Splunk REST API is enabled
4. SSL certificate is valid (or disable verification for testing)

### "Tool not available"

Check:
1. MCP server is enabled in `ENABLED_MCP_SERVERS`
2. Server configuration exists in `mcp-servers/config.json`
3. Server `enabled` flag is set to `true`
4. Backend has been restarted after configuration changes

---

## Example Agent Workflows

### Incident Response Workflow

```python
# 1. Search Splunk for errors
errors = await mcp_service.execute_tool(
    "search_logs",
    {"query": "index=app error OR exception", "earliest_time": "-15m"}
)

# 2. If errors found, create ServiceNow incident
if errors["success"] and errors["results"]:
    incident = await mcp_service.execute_tool(
        "create_incident",
        {
            "short_description": "Application errors detected",
            "description": f"Found {len(errors['results'])} errors in last 15 minutes",
            "urgency": "2",
            "impact": "2"
        }
    )
    
# 3. Create notable event in Splunk
    if incident["success"]:
        await mcp_service.execute_tool(
            "create_notable_event",
            {
                "title": f"Incident {incident['data']['result']['number']} created",
                "description": "Automated incident creation for application errors",
                "severity": "medium"
            }
        )
```

### Security Investigation Workflow

```python
# 1. Get notable events
notables = await mcp_service.execute_tool(
    "get_notable_events",
    {"severity": "high", "time_range": "-1h"}
)

# 2. For each notable, create change request if needed
for event in notables.get("events", []):
    if "firewall" in event.get("title", "").lower():
        await mcp_service.execute_tool(
            "create_change_request",
            {
                "short_description": f"Firewall rule change - {event['title']}",
                "description": f"Change required based on security event: {event['description']}",
                "type": "Emergency",
                "risk": "High"
            }
        )
```

---

## API Reference

### MCPService Methods

```python
async def execute_tool(
    tool_name: str,
    args: Dict[str, Any],
    server: Optional[str] = None
) -> Dict[str, Any]:
    """Execute MCP tool"""
    
async def list_available_tools() -> List[Dict[str, Any]]:
    """List all available MCP tools"""
```

### Tool Response Format

```python
{
    "success": bool,           # Execution success status
    "data": dict,              # Tool-specific result data (if success)
    "error": str,              # Error message (if not success)
    "status_code": int,        # HTTP status code (for API calls)
    "job_id": str             # Job ID (for async operations like Splunk)
}
```

---

## Additional Resources

- [ServiceNow REST API Documentation](https://developer.servicenow.com/dev.do#!/reference/api/latest/rest)
- [Splunk REST API Documentation](https://docs.splunk.com/Documentation/Splunk/latest/RESTREF/RESTprolog)
- [Model Context Protocol Specification](https://modelcontextprotocol.io/)

---

**Last Updated**: January 2026  
**Version**: 1.0.0

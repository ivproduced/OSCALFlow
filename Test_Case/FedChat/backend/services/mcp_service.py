"""
MCP (Model Context Protocol) Service
Integrates with MCP servers for tool execution
"""

from typing import List, Dict, Any, Optional
import json
import asyncio
import structlog
from pathlib import Path

from core.config import settings

logger = structlog.get_logger()


class MCPService:
    """Service for interacting with MCP servers"""
    
    def __init__(self):
        self.enabled = settings.ENABLE_MCP
        self.config_path = Path(settings.MCP_SERVERS_CONFIG)
        self.servers = {}
        self.enabled_servers = settings.enabled_mcp_servers_list
        self._credentials_warned = set()  # Track which servers we've warned about
        
        if self.enabled:
            self._load_config()
            self._validate_credentials()
        
        logger.info(
            "mcp_service_initialized",
            enabled=self.enabled,
            servers=list(self.servers.keys())
        )
    
    def _validate_credentials(self):
        """Validate credentials for enabled servers (log warnings only)"""
        import os
        
        if "servicenow" in self.servers and "servicenow" in self.enabled_servers:
            if not all([os.getenv("SERVICENOW_INSTANCE_URL"), 
                       os.getenv("SERVICENOW_USERNAME"), 
                       os.getenv("SERVICENOW_PASSWORD")]):
                logger.warning("servicenow_credentials_missing", 
                             message="ServiceNow credentials not configured")
        
        if "splunk" in self.servers and "splunk" in self.enabled_servers:
            if not all([os.getenv("SPLUNK_HOST"), 
                       os.getenv("SPLUNK_API_TOKEN")]):
                logger.warning("splunk_credentials_missing", 
                             message="Splunk credentials not configured")
    
    def _load_config(self):
        """Load MCP server configuration"""
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
            
            for server_name, server_config in config.get("mcpServers", {}).items():
                if server_name in self.enabled_servers and server_config.get("enabled", False):
                    self.servers[server_name] = server_config
            
            logger.info("mcp_config_loaded", server_count=len(self.servers))
        except Exception as e:
            logger.error("mcp_config_load_error", error=str(e))
    
    async def execute_tool(
        self,
        tool_name: str,
        args: Dict[str, Any],
        server: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute a tool via MCP
        
        Args:
            tool_name: Name of the tool to execute
            args: Tool arguments
            server: Specific server to use (auto-detect if None)
        
        Returns:
            Tool execution result
        """
        if not self.enabled:
            raise ValueError("MCP is not enabled")
        
        # Determine which server to use
        if not server:
            server = self._determine_server(tool_name)
        
        if server not in self.servers:
            raise ValueError(f"MCP server '{server}' not available")
        
        try:
            logger.info("mcp_tool_execution", tool=tool_name, server=server)
            
            # Execute tool based on server type
            if server == "filesystem":
                result = await self._execute_filesystem_tool(tool_name, args)
            elif server == "database":
                result = await self._execute_database_tool(tool_name, args)
            elif server == "api-client":
                result = await self._execute_api_tool(tool_name, args)
            elif server == "servicenow":
                result = await self._execute_servicenow_tool(tool_name, args)
            elif server == "splunk":
                result = await self._execute_splunk_tool(tool_name, args)
            else:
                result = await self._execute_custom_tool(server, tool_name, args)
            
            logger.info("mcp_tool_success", tool=tool_name, server=server)
            return result
            
        except Exception as e:
            logger.error("mcp_tool_error", tool=tool_name, server=server, error=str(e))
            raise
    
    def _determine_server(self, tool_name: str) -> str:
        """Determine which server should handle the tool"""
        # Map tool names to servers
        tool_server_map = {
            "read_file": "filesystem",
            "write_file": "filesystem",
            "list_directory": "filesystem",
            "query_database": "database",
            "http_request": "api-client",
            # ServiceNow tools
            "create_incident": "servicenow",
            "get_incident": "servicenow",
            "update_incident": "servicenow",
            "search_incidents": "servicenow",
            "create_change_request": "servicenow",
            # Splunk tools
            "search_logs": "splunk",
            "get_notable_events": "splunk",
            "create_notable_event": "splunk",
            "run_saved_search": "splunk",
            "get_search_job_results": "splunk",
        }
        
        return tool_server_map.get(tool_name, "filesystem")
    
    async def _execute_filesystem_tool(
        self,
        tool_name: str,
        args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute filesystem tool"""
        if tool_name == "read_file":
            file_path = args.get("path")
            if not file_path:
                raise ValueError("File path required")
            
            # Security check: ensure path is within allowed directories
            allowed_path = settings.DOCUMENT_STORAGE_PATH
            full_path = Path(file_path)
            
            if not str(full_path).startswith(allowed_path):
                raise PermissionError(f"Access denied to {file_path}")
            
            try:
                with open(full_path, 'r') as f:
                    content = f.read()
                
                return {
                    "success": True,
                    "content": content,
                    "path": str(full_path),
                }
            except Exception as e:
                return {
                    "success": False,
                    "error": str(e),
                }
        
        elif tool_name == "list_directory":
            dir_path = args.get("path", settings.DOCUMENT_STORAGE_PATH)
            full_path = Path(dir_path)
            
            try:
                files = [str(f) for f in full_path.iterdir()]
                return {
                    "success": True,
                    "files": files,
                }
            except Exception as e:
                return {
                    "success": False,
                    "error": str(e),
                }
        
        else:
            raise ValueError(f"Unknown filesystem tool: {tool_name}")
    
    async def _execute_database_tool(
        self,
        tool_name: str,
        args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute database tool"""
        if tool_name == "query_database":
            query = args.get("query")
            if not query:
                raise ValueError("Query required")
            
            # Security: only allow SELECT queries
            if not query.strip().upper().startswith("SELECT"):
                raise PermissionError("Only SELECT queries allowed")
            
            from core.database import AsyncSessionLocal
            from sqlalchemy import text
            
            async with AsyncSessionLocal() as session:
                try:
                    result = await session.execute(text(query))
                    rows = result.fetchall()
                    
                    # Convert to list of dicts
                    data = [dict(row._mapping) for row in rows]
                    
                    return {
                        "success": True,
                        "data": data,
                        "row_count": len(data),
                    }
                except Exception as e:
                    return {
                        "success": False,
                        "error": str(e),
                    }
        else:
            raise ValueError(f"Unknown database tool: {tool_name}")
    
    async def _execute_api_tool(
        self,
        tool_name: str,
        args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute API client tool"""
        import httpx
        
        if tool_name == "http_request":
            url = args.get("url")
            method = args.get("method", "GET").upper()
            headers = args.get("headers", {})
            data = args.get("data")
            
            if not url:
                raise ValueError("URL required")
            
            # Security: check allowed domains
            server_config = self.servers.get("api-client", {})
            allowed_domains = server_config.get("security", {}).get("allowed_domains", [])
            
            from urllib.parse import urlparse
            domain = urlparse(url).netloc
            
            if allowed_domains and domain not in allowed_domains:
                raise PermissionError(f"Domain {domain} not in allowed list")
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                try:
                    if method == "GET":
                        response = await client.get(url, headers=headers)
                    elif method == "POST":
                        response = await client.post(url, headers=headers, json=data)
                    else:
                        raise ValueError(f"Unsupported HTTP method: {method}")
                    
                    return {
                        "success": True,
                        "status_code": response.status_code,
                        "body": response.text,
                        "headers": dict(response.headers),
                    }
                except Exception as e:
                    return {
                        "success": False,
                        "error": str(e),
                    }
        else:
            raise ValueError(f"Unknown API tool: {tool_name}")
    
    async def _execute_servicenow_tool(
        self,
        tool_name: str,
        args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute ServiceNow tool"""
        import httpx
        import os
        from base64 import b64encode
        
        server_config = self.servers.get("servicenow", {})
        instance_url = os.getenv("SERVICENOW_INSTANCE_URL", server_config.get("config", {}).get("instance_url", ""))
        username = os.getenv("SERVICENOW_USERNAME", "")
        password = os.getenv("SERVICENOW_PASSWORD", "")
        
        if not all([instance_url, username, password]):
            return {
                "success": False,
                "error": "ServiceNow credentials not configured"
            }
        
        # Basic auth header
        auth_string = b64encode(f"{username}:{password}".encode()).decode()
        headers = {
            "Authorization": f"Basic {auth_string}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        async with httpx.AsyncClient(timeout=30.0, verify=True) as client:
            try:
                if tool_name == "create_incident":
                    data = {
                        "short_description": args.get("short_description"),
                        "description": args.get("description", ""),
                        "urgency": args.get("urgency", "3"),
                        "impact": args.get("impact", "3"),
                        "category": args.get("category", ""),
                        "assignment_group": args.get("assignment_group", "")
                    }
                    response = await client.post(
                        f"{instance_url}/api/now/table/incident",
                        headers=headers,
                        json=data
                    )
                    
                elif tool_name == "get_incident":
                    incident_number = args.get("incident_number")
                    response = await client.get(
                        f"{instance_url}/api/now/table/incident",
                        headers=headers,
                        params={"sysparm_query": f"number={incident_number}"}
                    )
                    
                elif tool_name == "update_incident":
                    incident_number = args.get("incident_number")
                    fields = args.get("fields", {})
                    
                    # First get the sys_id
                    get_response = await client.get(
                        f"{instance_url}/api/now/table/incident",
                        headers=headers,
                        params={"sysparm_query": f"number={incident_number}"}
                    )
                    incidents = get_response.json().get("result", [])
                    if not incidents:
                        return {"success": False, "error": "Incident not found"}
                    
                    sys_id = incidents[0]["sys_id"]
                    response = await client.patch(
                        f"{instance_url}/api/now/table/incident/{sys_id}",
                        headers=headers,
                        json=fields
                    )
                    
                elif tool_name == "search_incidents":
                    params = {
                        "sysparm_limit": args.get("limit", 10)
                    }
                    
                    query_parts = []
                    if args.get("query"):
                        query_parts.append(f"short_descriptionLIKE{args['query']}")
                    if args.get("state"):
                        query_parts.append(f"state={args['state']}")
                    if args.get("assigned_to"):
                        query_parts.append(f"assigned_to={args['assigned_to']}")
                    
                    if query_parts:
                        params["sysparm_query"] = "^".join(query_parts)
                    
                    response = await client.get(
                        f"{instance_url}/api/now/table/incident",
                        headers=headers,
                        params=params
                    )
                    
                elif tool_name == "create_change_request":
                    data = {
                        "short_description": args.get("short_description"),
                        "description": args.get("description", ""),
                        "type": args.get("type", "Normal"),
                        "risk": args.get("risk", "Moderate"),
                        "impact": args.get("impact", "3")
                    }
                    response = await client.post(
                        f"{instance_url}/api/now/table/change_request",
                        headers=headers,
                        json=data
                    )
                    
                else:
                    return {"success": False, "error": f"Unknown ServiceNow tool: {tool_name}"}
                
                if response.status_code in [200, 201]:
                    return {
                        "success": True,
                        "data": response.json(),
                        "status_code": response.status_code
                    }
                else:
                    return {
                        "success": False,
                        "error": f"ServiceNow API error: {response.status_code}",
                        "details": response.text
                    }
                    
            except Exception as e:
                return {"success": False, "error": str(e)}
    
    async def _execute_splunk_tool(
        self,
        tool_name: str,
        args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute Splunk tool"""
        import httpx
        import os
        
        server_config = self.servers.get("splunk", {})
        config = server_config.get("config", {})
        host = os.getenv("SPLUNK_HOST", config.get("host", ""))
        port = os.getenv("SPLUNK_PORT", config.get("port", "8089"))
        token = os.getenv("SPLUNK_API_TOKEN", "")
        
        if not all([host, token]):
            return {
                "success": False,
                "error": "Splunk credentials not configured"
            }
        
        base_url = f"https://{host}:{port}"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        # Check if we should verify SSL (disable only for dev/test)
        verify_ssl = os.getenv("SPLUNK_VERIFY_SSL", "true").lower() != "false"
        
        async with httpx.AsyncClient(timeout=60.0, verify=verify_ssl) as client:
            try:
                if tool_name == "search_logs":
                    query = args.get("query")
                    earliest_time = args.get("earliest_time", "-1h")
                    latest_time = args.get("latest_time", "now")
                    max_results = args.get("max_results", 100)
                    
                    # Create search job
                    search_data = {
                        "search": f"search {query}",
                        "earliest_time": earliest_time,
                        "latest_time": latest_time,
                        "max_count": max_results
                    }
                    
                    response = await client.post(
                        f"{base_url}/services/search/jobs",
                        headers=headers,
                        data=search_data
                    )
                    
                    if response.status_code == 201:
                        # Extract job ID from response
                        try:
                            import xml.etree.ElementTree as ET
                            root = ET.fromstring(response.text)
                            job_id = root.find(".//sid").text if root.find(".//sid") is not None else None
                        except Exception as parse_error:
                            logger.error("xml_parse_error", error=str(parse_error))
                            return {"success": False, "error": f"Failed to parse job ID: {parse_error}"}
                        
                        if job_id:
                            # Wait for job completion (simplified - should poll)
                            await asyncio.sleep(2)
                            
                            # Get results
                            results_response = await client.get(
                                f"{base_url}/services/search/jobs/{job_id}/results",
                                headers=headers,
                                params={"output_mode": "json", "count": max_results}
                            )
                            
                            return {
                                "success": True,
                                "job_id": job_id,
                                "results": results_response.json() if results_response.status_code == 200 else [],
                                "status_code": results_response.status_code
                            }
                    
                elif tool_name == "get_notable_events":
                    time_range = args.get("time_range", "-24h")
                    severity = args.get("severity")
                    status = args.get("status")
                    limit = args.get("limit", 50)
                    
                    # Build search query for notable events
                    search_query = f'search index=notable earliest={time_range}'
                    if severity:
                        search_query += f' severity="{severity}"'
                    if status:
                        search_query += f' status="{status}"'
                    
                    search_data = {
                        "search": search_query,
                        "max_count": limit
                    }
                    
                    response = await client.post(
                        f"{base_url}/services/search/jobs",
                        headers=headers,
                        data=search_data
                    )
                    
                    if response.status_code == 201:
                        import xml.etree.ElementTree as ET
                        root = ET.fromstring(response.text)
                        job_id = root.find(".//sid").text if root.find(".//sid") is not None else None
                        
                        if job_id:
                            await asyncio.sleep(2)
                            results_response = await client.get(
                                f"{base_url}/services/search/jobs/{job_id}/results",
                                headers=headers,
                                params={"output_mode": "json"}
                            )
                            
                            return {
                                "success": True,
                                "events": results_response.json() if results_response.status_code == 200 else []
                            }
                    
                elif tool_name == "create_notable_event":
                    title = args.get("title")
                    description = args.get("description")
                    severity = args.get("severity", "medium")
                    owner = args.get("owner", "")
                    
                    # Create notable event via modular action
                    event_data = {
                        "title": title,
                        "description": description,
                        "severity": severity,
                        "owner": owner
                    }
                    
                    response = await client.post(
                        f"{base_url}/services/notable_events",
                        headers=headers,
                        json=event_data
                    )
                    
                    return {
                        "success": response.status_code in [200, 201],
                        "status_code": response.status_code,
                        "data": response.json() if response.status_code in [200, 201] else None
                    }
                    
                elif tool_name == "run_saved_search":
                    search_name = args.get("search_name")
                    earliest_time = args.get("earliest_time")
                    latest_time = args.get("latest_time")
                    
                    params = {}
                    if earliest_time:
                        params["earliest_time"] = earliest_time
                    if latest_time:
                        params["latest_time"] = latest_time
                    
                    response = await client.post(
                        f"{base_url}/services/saved/searches/{search_name}/dispatch",
                        headers=headers,
                        data=params
                    )
                    
                    if response.status_code == 201:
                        import xml.etree.ElementTree as ET
                        root = ET.fromstring(response.text)
                        job_id = root.find(".//sid").text if root.find(".//sid") is not None else None
                        
                        return {
                            "success": True,
                            "job_id": job_id,
                            "message": "Saved search dispatched successfully"
                        }
                    
                elif tool_name == "get_search_job_results":
                    job_id = args.get("job_id")
                    offset = args.get("offset", 0)
                    count = args.get("count", 100)
                    
                    response = await client.get(
                        f"{base_url}/services/search/jobs/{job_id}/results",
                        headers=headers,
                        params={
                            "output_mode": "json",
                            "offset": offset,
                            "count": count
                        }
                    )
                    
                    return {
                        "success": response.status_code == 200,
                        "results": response.json() if response.status_code == 200 else [],
                        "status_code": response.status_code
                    }
                    
                else:
                    return {"success": False, "error": f"Unknown Splunk tool: {tool_name}"}
                    
            except Exception as e:
                return {"success": False, "error": str(e)}
    
    async def _execute_custom_tool(
        self,
        server: str,
        tool_name: str,
        args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute custom MCP server tool"""
        # This would integrate with actual MCP protocol
        # For now, return placeholder
        return {
            "success": False,
            "error": f"Custom MCP server execution not yet implemented for {server}",
        }
    
    async def list_available_tools(self) -> List[Dict[str, Any]]:
        """List all available MCP tools"""
        tools = []
        
        for server_name, server_config in self.servers.items():
            if server_name == "filesystem":
                tools.extend([
                    {
                        "name": "read_file",
                        "server": "filesystem",
                        "description": "Read contents of a file",
                        "parameters": {
                            "path": {"type": "string", "required": True}
                        }
                    },
                    {
                        "name": "list_directory",
                        "server": "filesystem",
                        "description": "List files in a directory",
                        "parameters": {
                            "path": {"type": "string", "required": False}
                        }
                    }
                ])
            
            elif server_name == "database":
                tools.append({
                    "name": "query_database",
                    "server": "database",
                    "description": "Execute SELECT query on database",
                    "parameters": {
                        "query": {"type": "string", "required": True}
                    }
                })
            
            elif server_name == "api-client":
                tools.append({
                    "name": "http_request",
                    "server": "api-client",
                    "description": "Make HTTP request to approved APIs",
                    "parameters": {
                        "url": {"type": "string", "required": True},
                        "method": {"type": "string", "required": False},
                        "headers": {"type": "object", "required": False},
                        "data": {"type": "object", "required": False}
                    }
                })
            
            elif server_name == "servicenow":
                tools.extend([
                    {
                        "name": "create_incident",
                        "server": "servicenow",
                        "description": "Create a new incident in ServiceNow",
                        "parameters": {
                            "short_description": {"type": "string", "required": True},
                            "description": {"type": "string", "required": False},
                            "urgency": {"type": "string", "required": False},
                            "impact": {"type": "string", "required": False}
                        }
                    },
                    {
                        "name": "get_incident",
                        "server": "servicenow",
                        "description": "Get incident details by number",
                        "parameters": {
                            "incident_number": {"type": "string", "required": True}
                        }
                    },
                    {
                        "name": "update_incident",
                        "server": "servicenow",
                        "description": "Update an existing incident",
                        "parameters": {
                            "incident_number": {"type": "string", "required": True},
                            "fields": {"type": "object", "required": True}
                        }
                    },
                    {
                        "name": "search_incidents",
                        "server": "servicenow",
                        "description": "Search incidents with filters",
                        "parameters": {
                            "query": {"type": "string", "required": False},
                            "state": {"type": "string", "required": False},
                            "limit": {"type": "number", "required": False}
                        }
                    },
                    {
                        "name": "create_change_request",
                        "server": "servicenow",
                        "description": "Create a new change request",
                        "parameters": {
                            "short_description": {"type": "string", "required": True},
                            "description": {"type": "string", "required": False},
                            "type": {"type": "string", "required": False}
                        }
                    }
                ])
            
            elif server_name == "splunk":
                tools.extend([
                    {
                        "name": "search_logs",
                        "server": "splunk",
                        "description": "Execute Splunk search query",
                        "parameters": {
                            "query": {"type": "string", "required": True},
                            "earliest_time": {"type": "string", "required": False},
                            "latest_time": {"type": "string", "required": False},
                            "max_results": {"type": "number", "required": False}
                        }
                    },
                    {
                        "name": "get_notable_events",
                        "server": "splunk",
                        "description": "Get notable security events from Splunk ES",
                        "parameters": {
                            "time_range": {"type": "string", "required": False},
                            "severity": {"type": "string", "required": False},
                            "limit": {"type": "number", "required": False}
                        }
                    },
                    {
                        "name": "create_notable_event",
                        "server": "splunk",
                        "description": "Create a notable event in Splunk ES",
                        "parameters": {
                            "title": {"type": "string", "required": True},
                            "description": {"type": "string", "required": True},
                            "severity": {"type": "string", "required": True}
                        }
                    },
                    {
                        "name": "run_saved_search",
                        "server": "splunk",
                        "description": "Execute a saved Splunk search",
                        "parameters": {
                            "search_name": {"type": "string", "required": True}
                        }
                    },
                    {
                        "name": "get_search_job_results",
                        "server": "splunk",
                        "description": "Get results from a Splunk search job",
                        "parameters": {
                            "job_id": {"type": "string", "required": True},
                            "offset": {"type": "number", "required": False},
                            "count": {"type": "number", "required": False}
                        }
                    }
                ])
        
        return tools

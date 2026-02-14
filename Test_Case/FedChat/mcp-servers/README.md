# Model Context Protocol (MCP) Servers

MCP servers provide tool integration for agents. Each server exposes specific capabilities that agents can use to interact with systems and data.

## Available Servers

### 1. Filesystem Server
**Purpose**: Read and write files within approved directories

**Capabilities**:
- Read file contents
- Write new files
- List directory contents
- Search for files

**Security**:
- Restricted to `/data/documents` directory
- Cannot access system files or configuration
- All operations audited

**Usage Example**:
```python
# Agent can use this tool to read a document
tool_call = {
    "tool": "read_file",
    "args": {
        "path": "/data/documents/policy.pdf"
    }
}
```

### 2. Database Server
**Purpose**: Query PostgreSQL database for information retrieval

**Capabilities**:
- Execute SELECT queries
- Read-only access
- Schema introspection

**Security**:
- Read-only mode enforced
- Sensitive tables blocked (users, sessions, api_keys)
- All queries logged for audit

**Usage Example**:
```python
# Agent can query for document metadata
tool_call = {
    "tool": "query_database",
    "args": {
        "query": "SELECT title, created_at FROM documents WHERE category = 'policy'"
    }
}
```

### 3. API Client Server
**Purpose**: Make HTTP requests to approved internal APIs

**Capabilities**:
- GET/POST requests to approved domains
- JSON request/response handling
- Header management

**Security**:
- Whitelist of approved domains only
- HTTPS required
- No external internet access
- Rate limiting enforced

**Usage Example**:
```python
# Agent can call internal API
tool_call = {
    "tool": "http_request",
    "args": {
        "url": "https://api.agency.gov/v1/policies",
        "method": "GET"
    }
}
```

## Configuration

### Enable/Disable Servers

Edit [config.json](config.json):
```json
{
  "mcpServers": {
    "filesystem": {
      "enabled": true
    }
  }
}
```

Or use environment variable:
```bash
ENABLED_MCP_SERVERS=filesystem,database
```

### Security Settings

All MCP servers enforce:
- Authentication required
- All calls audited
- Rate limiting (60 calls/minute default)
- 30-second timeout

### Adding Custom Servers

1. Create new server configuration in `config.json`
2. Add to `ENABLED_MCP_SERVERS` environment variable
3. Restart backend service

Example custom server:
```json
{
  "custom-tool": {
    "command": "node",
    "args": ["./custom-server.js"],
    "description": "Custom tool for specific use case",
    "enabled": true,
    "security": {
      "read_only": true
    }
  }
}
```

## Development

### Testing MCP Servers

```bash
# Test filesystem server
npx @modelcontextprotocol/server-filesystem /data/documents

# Test database server
npx @modelcontextprotocol/server-postgres $DATABASE_URL

# Test API client
npx @modelcontextprotocol/server-fetch
```

### Monitoring

MCP server calls are logged in audit logs:
- Tool name
- Arguments (sanitized)
- Response status
- Execution time
- User ID

View logs:
```bash
tail -f /var/log/fedchat/audit.log | grep "mcp_call"
```

## FISMA Compliance

MCP servers are configured for FISMA Moderate:
- All data stays within authorized boundary
- No external internet access
- Complete audit trail
- Principle of least privilege
- Security controls enforced

## Troubleshooting

**Server not responding**:
```bash
# Check if MCP server is enabled
docker-compose exec backend cat /app/mcp-servers/config.json | grep "enabled"

# Check logs
docker-compose logs backend | grep mcp
```

**Permission denied**:
- Verify security configuration in config.json
- Check allowed_paths/allowed_domains
- Review audit logs for detailed error

**Rate limit exceeded**:
- Increase rate_limit_per_minute in config.json
- Implement caching in agent logic
- Batch requests when possible

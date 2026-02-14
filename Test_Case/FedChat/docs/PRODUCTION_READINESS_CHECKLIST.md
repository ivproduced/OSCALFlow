# Production Readiness Checklist

## ServiceNow & Splunk MCP Integration

Before deploying these integrations to production, verify the following:

---

## ✅ Pre-Deployment Checklist

### Configuration

- [ ] **Environment Variables Set**
  - [ ] `SERVICENOW_INSTANCE_URL` configured
  - [ ] `SERVICENOW_USERNAME` configured (service account)
  - [ ] `SERVICENOW_PASSWORD` configured (secure password)
  - [ ] `SPLUNK_HOST` configured
  - [ ] `SPLUNK_PORT` configured (default: 8089)
  - [ ] `SPLUNK_API_TOKEN` configured
  - [ ] `SPLUNK_VERIFY_SSL=true` (for production)
  - [ ] `ENABLED_MCP_SERVERS` includes desired servers

- [ ] **MCP Configuration**
  - [ ] `mcp-servers/config.json` reviewed
  - [ ] ServiceNow server enabled: `"enabled": true`
  - [ ] Splunk server enabled: `"enabled": true`

### ServiceNow Configuration

- [ ] **Service Account Setup**
  - [ ] Dedicated service account created (not personal account)
  - [ ] Account has `itil` role (basic ITSM operations)
  - [ ] Account has `incident_manager` role (if managing incidents)
  - [ ] Account has `change_manager` role (if managing changes)
  - [ ] Account password meets complexity requirements
  - [ ] Account is set to never expire or has long expiration

- [ ] **Instance Configuration**
  - [ ] Instance URL is correct (including https://)
  - [ ] Instance is accessible from FedChat server
  - [ ] IP whitelisting configured (if applicable)
  - [ ] Rate limiting reviewed

- [ ] **Testing**
  - [ ] Can create incidents
  - [ ] Can retrieve incidents by number
  - [ ] Can update incidents
  - [ ] Can search incidents
  - [ ] Can create change requests

### Splunk Configuration

- [ ] **API Token Setup**
  - [ ] API token generated (Settings > Tokens)
  - [ ] Token has `search` capability
  - [ ] Token has `rest_properties_get` capability
  - [ ] Token has appropriate expiration set
  - [ ] Token is not shared across systems

- [ ] **Splunk Configuration**
  - [ ] Splunk REST API is enabled
  - [ ] Port 8089 is open and accessible
  - [ ] SSL certificate is valid
  - [ ] `SPLUNK_VERIFY_SSL=true` in production
  - [ ] Enterprise Security (ES) installed (if using notable events)

- [ ] **Testing**
  - [ ] Can execute searches
  - [ ] Can retrieve search results
  - [ ] Can access notable events (if using ES)
  - [ ] Can create notable events (if using ES)
  - [ ] Can run saved searches

### Security

- [ ] **Credential Security**
  - [ ] Credentials stored in environment variables (not hardcoded)
  - [ ] Credentials encrypted at rest
  - [ ] Credentials not in version control
  - [ ] Using secrets manager (AWS Secrets, Vault, etc.) in production
  - [ ] Credentials have been rotated from defaults

- [ ] **Network Security**
  - [ ] TLS/HTTPS enabled for all connections
  - [ ] SSL certificate verification enabled (`SPLUNK_VERIFY_SSL=true`)
  - [ ] Connections go through VPN or private network
  - [ ] Firewall rules configured
  - [ ] IP whitelisting configured on external systems

- [ ] **Access Controls**
  - [ ] Service accounts use principle of least privilege
  - [ ] Audit logging enabled for all tool executions
  - [ ] Rate limiting configured
  - [ ] Session timeouts configured

### Monitoring & Logging

- [ ] **Audit Logs**
  - [ ] MCP tool execution logged
  - [ ] Logs include user, timestamp, action, result
  - [ ] Logs retained for required period (7 years for FISMA)
  - [ ] Log aggregation configured

- [ ] **Error Handling**
  - [ ] Error logs reviewed
  - [ ] Alert configured for repeated failures
  - [ ] Fallback mechanisms in place

- [ ] **Performance**
  - [ ] Timeout values appropriate (30s ServiceNow, 60s Splunk)
  - [ ] Rate limits not exceeded
  - [ ] Connection pooling configured

---

## 🧪 Testing Procedures

### Unit Testing

Run the example script:
```bash
cd /path/to/fedchat-system
python scripts/example_mcp_usage.py
```

Expected output:
- ServiceNow examples complete without errors
- Splunk examples complete without errors
- Integrated workflow demonstrates cross-system functionality

### Manual Testing

**Test ServiceNow:**
```python
from services.mcp_service import MCPService
import asyncio

async def test():
    mcp = MCPService()
    
    # Test 1: Create incident
    result = await mcp.execute_tool(
        "create_incident",
        {"short_description": "Test incident - please close", "urgency": "3"},
        "servicenow"
    )
    print(f"Create: {result['success']}")
    
    # Test 2: Search
    result = await mcp.execute_tool(
        "search_incidents",
        {"limit": 1},
        "servicenow"
    )
    print(f"Search: {result['success']}")

asyncio.run(test())
```

**Test Splunk:**
```python
from services.mcp_service import MCPService
import asyncio

async def test():
    mcp = MCPService()
    
    # Test: Search
    result = await mcp.execute_tool(
        "search_logs",
        {"query": "index=* | head 1", "max_results": 1},
        "splunk"
    )
    print(f"Search: {result['success']}")

asyncio.run(test())
```

### Integration Testing

Test the complete workflow:
1. Agent detects issue → Searches Splunk
2. Threshold exceeded → Creates ServiceNow incident
3. Incident created → Updates Splunk notable event
4. Verify incident appears in ServiceNow
5. Verify notable event appears in Splunk

---

## 🚨 Known Limitations

### ServiceNow
- **Attachment uploads**: Not yet implemented
- **Complex queries**: Only basic query filters supported
- **Bulk operations**: No batch create/update support
- **Custom fields**: May need customization for agency-specific fields
- **OAuth**: Uses basic auth; OAuth2 recommended for production

### Splunk
- **Search job polling**: Simplified; may need enhancement for long searches
- **Result pagination**: Basic implementation
- **Advanced SPL**: Complex queries may need refinement
- **Streaming results**: Not implemented
- **Search quotas**: No quota management

### General
- **No retry logic**: Failed requests don't automatically retry
- **No circuit breaker**: No protection against cascading failures
- **No caching**: Every request hits the APIs
- **No connection pooling**: New connection per request

---

## 🔧 Issues & Troubleshooting

### Issue: "ServiceNow credentials not configured"

**Cause**: Environment variables not set  
**Fix**: Set `SERVICENOW_INSTANCE_URL`, `SERVICENOW_USERNAME`, `SERVICENOW_PASSWORD`

### Issue: "Splunk credentials not configured"

**Cause**: Environment variables not set  
**Fix**: Set `SPLUNK_HOST`, `SPLUNK_API_TOKEN`

### Issue: SSL Certificate Verification Failed (Splunk)

**Cause**: Self-signed certificate or certificate chain issue  
**Temporary Fix**: Set `SPLUNK_VERIFY_SSL=false` (dev/test only)  
**Proper Fix**: Install proper certificate or add CA cert to trust store

### Issue: "401 Unauthorized" (ServiceNow)

**Solutions**:
- Verify username/password are correct
- Check service account is active
- Ensure account has required roles
- Check if password has expired

### Issue: "401 Unauthorized" (Splunk)

**Solutions**:
- Verify API token is correct
- Check token hasn't expired
- Regenerate token if needed
- Verify token has required capabilities

### Issue: "Connection Timeout"

**Solutions**:
- Check network connectivity
- Verify firewall rules allow connections
- Check if service is running
- Increase timeout values if needed

---

## 📊 Performance Benchmarks

Expected response times (with network latency):

**ServiceNow:**
- Create incident: 500-1500ms
- Get incident: 300-800ms
- Search incidents: 500-2000ms (depends on filters)

**Splunk:**
- Simple search: 2-5 seconds
- Complex search: 5-30+ seconds
- Get notable events: 2-5 seconds
- Get job results: 100-500ms

---

## 🔄 Deployment Steps

### Development Environment

1. Copy `.env.example` to `.env`
2. Configure credentials
3. Start services: `docker-compose up -d`
4. Test integrations: `python scripts/example_mcp_usage.py`

### Production Environment (Docker)

1. Use secrets manager for credentials
2. Set environment variables in docker-compose or swarm
3. Enable `SPLUNK_VERIFY_SSL=true`
4. Configure monitoring and alerting
5. Deploy with: `docker-compose -f docker-compose.prod.yml up -d`

### Production Environment (Kubernetes)

1. Create secrets: `kubectl create secret generic fedchat-mcp-secrets`
2. Update `kubernetes/00-namespace-config.yaml`
3. Apply configs: `kubectl apply -f kubernetes/`
4. Verify pods: `kubectl get pods -n fedchat`
5. Test: `kubectl exec -it deployment/fedchat-backend -n fedchat -- python scripts/example_mcp_usage.py`

---

## 🎯 Success Criteria

Before marking as "production ready":

- [ ] All tests pass
- [ ] Security review completed
- [ ] Credentials properly secured
- [ ] Monitoring configured
- [ ] Documentation reviewed
- [ ] Team trained on usage
- [ ] Incident response plan includes these integrations
- [ ] Backup/recovery procedures documented

---

## 📝 Sign-Off

**Tested by**: _______________  
**Date**: _______________  
**Security reviewed by**: _______________  
**Date**: _______________  
**Approved for production by**: _______________  
**Date**: _______________

---

## 📚 References

- [ServiceNow REST API Docs](https://developer.servicenow.com/dev.do#!/reference/api/latest/rest)
- [Splunk REST API Docs](https://docs.splunk.com/Documentation/Splunk/latest/RESTREF/RESTprolog)
- [MCP Integration Guide](docs/MCP_INTEGRATIONS.md)
- [FedChat Security Documentation](docs/FISMA_COMPLIANCE.md)

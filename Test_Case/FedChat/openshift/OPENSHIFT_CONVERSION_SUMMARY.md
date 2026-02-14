# OpenShift Conversion Summary

## Overview

The FedChat system has been successfully converted to support OpenShift deployment. A complete set of OpenShift-optimized manifests and documentation has been created in the `openshift/` directory.

## What Was Created

### Core Deployment Files (YAML Manifests)

1. **00-namespace-config.yaml** - Project namespace, ServiceAccount, ConfigMap, and Secrets
2. **01-postgres.yaml** - PostgreSQL with pgvector, optimized for OpenShift security
3. **02-redis.yaml** - Redis cache with persistence
4. **03-ollama.yaml** - Local LLM runtime (optional)
5. **04-backend.yaml** - FastAPI backend with LangChain/LangGraph
6. **05-frontend.yaml** - LibreChat UI
7. **06-routes.yaml** - OpenShift Routes (replaces Kubernetes Ingress)
8. **07-security-policies.yaml** - SCCs, NetworkPolicies, ResourceQuotas, LimitRanges, PDBs

### Documentation Files

1. **README.md** - Complete OpenShift deployment guide with examples
2. **MIGRATION_GUIDE.md** - Detailed migration guide from Kubernetes to OpenShift
3. **KUBERNETES_VS_OPENSHIFT.md** - Quick reference comparison table
4. **DEPLOYMENT_CHECKLIST.md** - Step-by-step deployment verification checklist

### Scripts

1. **deploy.sh** - Automated deployment script (executable)

## Key Differences from Kubernetes

### Security Enhancements

| Aspect | Kubernetes | OpenShift |
|--------|-----------|-----------|
| Container Users | Often root | Non-root (UID 1001+) |
| Security | PSP/PSA | SCCs (more restrictive) |
| Capabilities | May run privileged | All capabilities dropped |
| SELinux | Optional | Enforced |
| Privilege Escalation | May be allowed | Disabled |

### Networking Changes

- **Ingress → Routes**: Replaced Kubernetes Ingress with 3 OpenShift Routes:
  - Main route for frontend
  - API route with extended timeout
  - Metrics route with IP whitelist

- **NetworkPolicies**: Enhanced to work with OpenShift DNS and router

### Container Modifications

All containers updated with:
- Non-root user contexts (UID 1001 or 999)
- Security context constraints
- Capability drops (ALL)
- Read-only filesystem support
- EmptyDir volumes for writable paths (/tmp, cache dirs)
- Seccomp profiles (RuntimeDefault)

### Specific Component Changes

**PostgreSQL:**
- Runs as UID 999 (postgres default)
- ConfigMap mounted read-only
- Enhanced health checks

**Redis:**
- Runs as UID 999
- Persistence configured
- Password-protected connection

**Ollama:**
- Runs as UID 1001
- HOME env overridden to /tmp
- Storage path changed from /root/.ollama to /.ollama

**Backend:**
- Init containers use UBI minimal (not busybox)
- Runs as UID 1001
- EmptyDir for /tmp

**Frontend:**
- Runs as UID 1001
- EmptyDir for /tmp and /.npm
- Cache directories properly configured

## Deployment Workflows

### Option 1: Automated (Recommended)
```bash
cd openshift
./deploy.sh
```

### Option 2: Manual
```bash
cd openshift
oc apply -f 00-namespace-config.yaml
oc apply -f 07-security-policies.yaml  # Requires cluster-admin
oc apply -f 01-postgres.yaml
oc apply -f 02-redis.yaml
oc apply -f 03-ollama.yaml
oc apply -f 04-backend.yaml
oc apply -f 05-frontend.yaml
oc apply -f 06-routes.yaml
```

## Pre-Deployment Requirements

### System Requirements
- OpenShift Container Platform 4.12+
- Storage class with RWO support
- Storage class with RWX support (for documents-pvc)
- (Optional) GPU support for Ollama

### Access Requirements
- Cluster admin access (for creating SCCs) OR
- Pre-configured SCC that allows non-root containers

### Configuration Requirements
1. Update secrets in `00-namespace-config.yaml`
2. Update cluster domain in `06-routes.yaml`
3. Update image references in `04-backend.yaml` and `05-frontend.yaml`
4. (Optional) Update storage class names if not using defaults

## Post-Deployment Tasks

1. **Create admin user:**
   ```bash
   oc exec -it deployment/fedchat-backend -n fedchat -- \
     python scripts/create_admin.py
   ```

2. **Generate API keys:**
   ```bash
   oc exec -it deployment/fedchat-backend -n fedchat -- \
     python scripts/create_api_key.py
   ```

3. **Verify deployment:**
   ```bash
   # Check all pods running
   oc get pods -n fedchat
   
   # Test API health
   curl -k https://$(oc get route fedchat-api -n fedchat -o jsonpath='{.spec.host}')/health
   
   # Access frontend
   oc get route fedchat -n fedchat -o jsonpath='{.spec.host}'
   ```

## File Structure

```
openshift/
├── 00-namespace-config.yaml        # Namespace, SA, ConfigMap, Secrets
├── 01-postgres.yaml                 # PostgreSQL with pgvector
├── 02-redis.yaml                    # Redis cache
├── 03-ollama.yaml                   # Local LLM (optional)
├── 04-backend.yaml                  # Backend API + HPA
├── 05-frontend.yaml                 # Frontend UI + HPA
├── 06-routes.yaml                   # Routes + NetworkPolicies
├── 07-security-policies.yaml        # SCC + RBAC + Quotas + Limits
├── deploy.sh                        # Automated deployment script
├── README.md                        # Deployment guide
├── MIGRATION_GUIDE.md              # K8s to OpenShift migration
├── KUBERNETES_VS_OPENSHIFT.md      # Quick comparison
└── DEPLOYMENT_CHECKLIST.md         # Verification checklist
```

## Security Features

### Security Context Constraints (SCC)
- Custom SCC: `fedchat-scc`
- Non-root user required
- No privileged containers
- All capabilities dropped
- Specific volume types allowed

### Network Policies
- Default deny all traffic
- Allow internal pod-to-pod communication
- Allow DNS resolution
- Specific policies for database access
- Allow external HTTPS for APIs

### Resource Controls
- ResourceQuota limiting total namespace resources
- LimitRange controlling individual container resources
- PodDisruptionBudgets ensuring availability during updates

## Monitoring & Operations

### Health Checks
- Liveness and readiness probes on all containers
- Health endpoints on backend (/health)
- Database connectivity verification

### Scaling
- HorizontalPodAutoscalers configured:
  - Backend: 2-10 replicas (CPU/Memory based)
  - Frontend: 2-5 replicas (CPU/Memory based)

### Logging
- All containers log to stdout/stderr
- Accessible via: `oc logs -f deployment/<name> -n fedchat`
- Ready for centralized logging integration

### Metrics
- Prometheus metrics exposed on port 9090
- Accessible via dedicated route (IP restricted)

## Compliance & Security

### FISMA Moderate Compliance
✅ Self-hosted within authorized boundaries
✅ No external API dependencies (with local LLM)
✅ Comprehensive audit logging
✅ Encryption at rest and in transit
✅ Role-based access controls
✅ Network segmentation
✅ Resource quotas and limits
✅ Non-root containers
✅ Security context constraints

### FedRAMP Considerations
- Compatible with FedRAMP High environments
- Can use Azure OpenAI (FedRAMP High) or AWS Bedrock
- Audit logging supports 7-year retention requirements
- Network policies align with federal security requirements

## Troubleshooting Quick Reference

### Common Issues

1. **Pods in CrashLoopBackOff**
   - Check SCC assignment
   - Verify UID/GID configurations
   - Review security contexts

2. **Permission denied errors**
   - Verify fsGroup matches container UID
   - Check PVC permissions
   - Ensure emptyDir volumes for writable paths

3. **Routes not accessible**
   - Verify route creation
   - Check router pod status
   - Verify service endpoints

4. **Database connection failures**
   - Check init containers completed successfully
   - Verify secrets are correct
   - Test connectivity from backend pod

## Next Steps

1. **Review Documentation:**
   - Read [openshift/README.md](./openshift/README.md) for detailed deployment instructions
   - Review [openshift/MIGRATION_GUIDE.md](./openshift/MIGRATION_GUIDE.md) for migration details
   - Use [openshift/DEPLOYMENT_CHECKLIST.md](./openshift/DEPLOYMENT_CHECKLIST.md) during deployment

2. **Prepare for Deployment:**
   - Generate secure secrets
   - Obtain cluster domain information
   - Build and push container images
   - Coordinate with cluster administrator for SCC creation

3. **Deploy:**
   - Use automated script: `./openshift/deploy.sh`
   - Or follow manual steps in README

4. **Verify:**
   - Complete checklist in DEPLOYMENT_CHECKLIST.md
   - Test all functionality
   - Configure monitoring and alerting

## Support

For questions or issues:
- Refer to documentation in `openshift/` directory
- Check [openshift/KUBERNETES_VS_OPENSHIFT.md](./openshift/KUBERNETES_VS_OPENSHIFT.md) for quick reference
- Review [docs/DEPLOYMENT.md](./docs/DEPLOYMENT.md) for general deployment guidance

## Changes to Main Repository

The main README.md has been updated to include:
- Reference to OpenShift deployment option
- Links to OpenShift documentation
- Deployment options section

No changes were made to:
- Kubernetes manifests (remain unchanged in `kubernetes/`)
- Docker Compose configuration
- Application source code
- Original documentation

---

**Created:** January 14, 2026
**Version:** 1.0
**Status:** Ready for deployment

# OpenShift Deployment Guide

This directory contains OpenShift-specific manifests for deploying FedChat in a production OpenShift environment.

## Prerequisites

- OpenShift Container Platform (4.12+)
- oc CLI configured with cluster access
- Cluster admin rights (for creating SCCs) or appropriate SCCs already configured
- Storage class for persistent volumes
- (Optional) GPU support for Ollama workloads

## Key Differences from Kubernetes

This OpenShift deployment includes:
- **Routes** instead of Ingress for external access
- **Security Context Constraints (SCCs)** for pod security
- **DeploymentConfigs** (optional) or standard Deployments
- Non-root user security contexts
- OpenShift-specific security policies
- Integrated image streams and build configs (optional)

## Quick Start

### 1. Login to OpenShift

```bash
oc login https://api.your-cluster.com:6443 --token=YOUR_TOKEN
```

### 2. Configure Secrets

Edit `00-namespace-config.yaml` and update all secret values:

```bash
# Generate secure secrets
openssl rand -hex 32  # For JWT_SECRET
openssl rand -hex 32  # For SESSION_SECRET
openssl rand -hex 16  # For POSTGRES_PASSWORD
openssl rand -hex 16  # For REDIS_PASSWORD
```

**IMPORTANT**: Never commit actual secrets to git!

### 3. Build and Push Images

Build Docker images and push to your container registry (or use OpenShift's integrated registry):

```bash
# Option 1: Using external registry
docker build -t your-registry/fedchat-backend:latest ../backend
docker push your-registry/fedchat-backend:latest

docker build -t your-registry/fedchat-librechat:latest ../librechat
docker push your-registry/fedchat-librechat:latest

# Option 2: Using OpenShift integrated registry
oc new-build --name=fedchat-backend --binary --strategy=docker -n fedchat
oc start-build fedchat-backend --from-dir=../backend --follow

oc new-build --name=fedchat-librechat --binary --strategy=docker -n fedchat
oc start-build fedchat-librechat --from-dir=../librechat --follow
```

Update image names in:
- `04-backend.yaml` 
- `05-frontend.yaml`

### 4. Deploy to OpenShift

Deploy in order:

```bash
# Create project/namespace and configuration
oc apply -f 00-namespace-config.yaml

# Deploy database layer
oc apply -f 01-postgres.yaml
oc apply -f 02-redis.yaml

# Deploy LLM backend
oc apply -f 03-ollama.yaml

# Deploy application layer
oc apply -f 04-backend.yaml
oc apply -f 05-frontend.yaml

# Setup networking
oc apply -f 06-routes.yaml

# Apply security policies
oc apply -f 07-security-policies.yaml
```

### 5. Verify Deployment

```bash
# Check pods
oc get pods -n fedchat

# Check routes
oc get routes -n fedchat

# Check logs
oc logs -f deployment/fedchat-backend -n fedchat
```

### 6. Access the Application

```bash
# Get the route URL
oc get route fedchat -n fedchat -o jsonpath='{.spec.host}'

# Open in browser
echo "https://$(oc get route fedchat -n fedchat -o jsonpath='{.spec.host}')"
```

## Security Context Constraints

This deployment uses a custom SCC that allows:
- Non-root user execution (UID 1001)
- Specific volume types (ConfigMap, Secret, PersistentVolumeClaim)
- No privileged containers
- Read-only root filesystem (where possible)

If you need to create the custom SCC (requires cluster-admin):

```bash
oc apply -f 07-security-policies.yaml
```

## Persistent Storage

Ensure your cluster has a default storage class configured:

```bash
oc get storageclass
```

If needed, update the `storageClassName` in:
- `01-postgres.yaml`
- `04-backend.yaml`

## Monitoring

### View Application Logs

```bash
# Backend logs
oc logs -f deployment/fedchat-backend -n fedchat

# Frontend logs
oc logs -f deployment/fedchat-frontend -n fedchat

# Database logs
oc logs -f deployment/fedchat-postgres -n fedchat
```

### Access Metrics

Metrics are exposed on port 9090 of the backend service:

```bash
oc port-forward svc/fedchat-backend 9090:9090 -n fedchat
# Visit http://localhost:9090/metrics
```

## Scaling

Scale deployments as needed:

```bash
# Scale backend
oc scale deployment/fedchat-backend --replicas=5 -n fedchat

# Scale frontend
oc scale deployment/fedchat-frontend --replicas=3 -n fedchat
```

## Updates

### Rolling Updates

```bash
# Update backend image
oc set image deployment/fedchat-backend backend=your-registry/fedchat-backend:v2.0 -n fedchat

# Update frontend image
oc set image deployment/fedchat-frontend frontend=your-registry/fedchat-librechat:v2.0 -n fedchat
```

### Configuration Updates

```bash
# Edit ConfigMap
oc edit configmap fedchat-config -n fedchat

# Edit Secrets
oc edit secret fedchat-secrets -n fedchat

# Restart deployments to pick up changes
oc rollout restart deployment/fedchat-backend -n fedchat
oc rollout restart deployment/fedchat-frontend -n fedchat
```

## Backup and Restore

### Database Backup

```bash
# Backup PostgreSQL
oc exec -it deployment/fedchat-postgres -n fedchat -- pg_dump -U fedchat_user fedchat > backup.sql

# Restore PostgreSQL
cat backup.sql | oc exec -i deployment/fedchat-postgres -n fedchat -- psql -U fedchat_user fedchat
```

## Troubleshooting

### Pod Not Starting

```bash
# Check pod status
oc describe pod <pod-name> -n fedchat

# Check events
oc get events -n fedchat --sort-by='.lastTimestamp'

# Check SCC issues
oc get pod <pod-name> -n fedchat -o yaml | grep -A 5 securityContext
```

### Permission Denied Errors

If you see permission denied errors, verify:
1. The pod is using the correct service account
2. The service account has the proper SCC
3. Volume permissions match the security context UID

```bash
# Check service account
oc get sa -n fedchat

# Check SCC assignments
oc describe scc fedchat-scc
```

### Network Issues

```bash
# Test connectivity between pods
oc exec -it deployment/fedchat-backend -n fedchat -- curl http://fedchat-postgres:5432

# Check network policies
oc get networkpolicies -n fedchat
```

## Production Considerations

1. **SSL/TLS**: Configure edge or re-encrypt termination on routes
2. **Resource Limits**: Adjust based on actual usage patterns
3. **Backups**: Implement automated database backup solution
4. **Monitoring**: Integrate with OpenShift monitoring stack
5. **HA**: Deploy multiple replicas with pod anti-affinity
6. **Storage**: Use appropriate storage class for workload type
7. **Security**: Regular security scans and updates
8. **Compliance**: Review OpenShift compliance operator

## Related Documentation

- [FISMA Compliance Guide](../docs/FISMA_COMPLIANCE.md)
- [Production Readiness Checklist](../docs/PRODUCTION_READINESS_CHECKLIST.md)
- [Deployment Guide](../docs/DEPLOYMENT.md)

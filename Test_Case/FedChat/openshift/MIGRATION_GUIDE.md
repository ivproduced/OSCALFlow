# OpenShift Migration Guide

## Converting from Kubernetes to OpenShift

This document outlines the key differences between the Kubernetes and OpenShift deployments of FedChat.

## Key Differences

### 1. Security Context Constraints (SCCs)

**Kubernetes:**
- Uses Pod Security Policies (deprecated) or Pod Security Admission
- Less restrictive by default

**OpenShift:**
- Uses Security Context Constraints (SCCs)
- More restrictive by default (no root containers)
- Custom SCC created: `fedchat-scc`
- All containers run as UID 1001 (non-root)

### 2. Networking

**Kubernetes:**
- Uses Ingress resources
- Requires Ingress Controller (e.g., NGINX)

**OpenShift:**
- Uses Routes (OpenShift-native)
- Built-in HAProxy router
- Three routes created:
  - `fedchat` - Main application (frontend)
  - `fedchat-api` - Backend API
  - `fedchat-metrics` - Metrics endpoint

### 3. Image Registry

**Kubernetes:**
- External registry required (e.g., Docker Hub, ECR)

**OpenShift:**
- Integrated image registry available
- Can use `oc new-build` for building images
- Can use ImageStreams for managing images

### 4. Service Accounts

**Kubernetes:**
- Default service account often sufficient

**OpenShift:**
- Custom service account created: `fedchat-sa`
- Bound to custom SCC via RoleBinding

### 5. Storage

**Kubernetes:**
- Storage class varies by cloud provider

**OpenShift:**
- Often uses `gp3-csi` or cloud-specific storage
- Same PVC structure, but may need different storage class

## Migration Steps

### From Kubernetes to OpenShift

1. **Review Security Contexts:**
   ```bash
   # All deployments updated to use:
   runAsUser: 1001
   runAsNonRoot: true
   fsGroup: 1001
   ```

2. **Update Image References:**
   - Change from external registry to OpenShift registry if desired
   - Update image pull policies

3. **Replace Ingress with Routes:**
   ```bash
   # Convert:
   kubectl apply -f kubernetes/06-ingress.yaml
   # To:
   oc apply -f openshift/06-routes.yaml
   ```

4. **Apply SCCs:**
   ```bash
   # Requires cluster-admin
   oc apply -f openshift/07-security-policies.yaml
   ```

5. **Update Init Containers:**
   - Changed from `busybox` to `ubi9/ubi-minimal`
   - Updated health check commands

6. **Deploy:**
   ```bash
   cd openshift
   ./deploy.sh
   ```

## Container Changes

### PostgreSQL
- **UID Changed:** 999 (postgres default)
- **Security:** Drop all capabilities
- **Volumes:** ConfigMap mounted as read-only

### Redis
- **UID Changed:** 999 (redis default in alpine)
- **Security:** Drop all capabilities
- **Command:** Added `--dir /data` for persistence

### Ollama
- **UID Changed:** 1001 (non-root)
- **Home Override:** `HOME=/tmp`
- **Storage Path:** Changed from `/root/.ollama` to `/.ollama`
- **Temp Volume:** Added emptyDir for `/tmp`

### Backend
- **UID Changed:** 1001
- **Init Containers:** Use UBI minimal instead of busybox
- **Volumes:** Added emptyDir for `/tmp`
- **Security:** Full capability drop

### Frontend
- **UID Changed:** 1001
- **Volumes:** Added emptyDir for `/tmp` and `/.npm`
- **Security:** Full capability drop

## Network Policies

Enhanced network policies created:
- Default deny all
- Allow internal pod-to-pod
- Allow DNS (both OpenShift DNS and kube-system)
- Specific policies for:
  - Backend → PostgreSQL (5432)
  - Backend → Redis (6379)
  - Backend → Ollama (11434)
  - Router → Frontend/Backend
  - Backend → External HTTPS (443)

## Resource Management

Same resource quotas and limits, but with additional:
- Pod limits: 50 pods max
- Service limits: 10 services max
- ConfigMap/Secret limits

## Troubleshooting Common Issues

### Issue: Pods stuck in CrashLoopBackOff

**Symptom:**
```bash
oc get pods
# NAME                                READY   STATUS             RESTARTS   AGE
# fedchat-backend-xxx                 0/1     CrashLoopBackOff   5          5m
```

**Solution:**
1. Check SCC assignment:
   ```bash
   oc get pod <pod-name> -o yaml | grep -A 5 "openshift.io/scc"
   ```

2. Verify security context:
   ```bash
   oc describe pod <pod-name> | grep -A 10 "Security Context"
   ```

3. Check logs:
   ```bash
   oc logs <pod-name>
   ```

### Issue: Permission denied on volumes

**Symptom:**
```
Error: EACCES: permission denied, open '/data/file'
```

**Solution:**
1. Verify fsGroup is set:
   ```yaml
   securityContext:
     fsGroup: 1001
   ```

2. Check PVC permissions:
   ```bash
   oc exec -it <pod-name> -- ls -la /data
   ```

### Issue: Cannot pull image

**Symptom:**
```
Failed to pull image: unauthorized
```

**Solution:**
1. Create image pull secret:
   ```bash
   oc create secret docker-registry regcred \
     --docker-server=<registry> \
     --docker-username=<username> \
     --docker-password=<password> \
     -n fedchat
   ```

2. Link to service account:
   ```bash
   oc secrets link fedchat-sa regcred --for=pull -n fedchat
   ```

### Issue: Route not accessible

**Symptom:**
```
curl: (7) Failed to connect to fedchat.apps.cluster.com
```

**Solution:**
1. Check route status:
   ```bash
   oc get route fedchat -n fedchat
   oc describe route fedchat -n fedchat
   ```

2. Verify router pods:
   ```bash
   oc get pods -n openshift-ingress
   ```

3. Check service endpoints:
   ```bash
   oc get endpoints -n fedchat
   ```

## Testing the Migration

### 1. Verify All Pods Running
```bash
oc get pods -n fedchat
# All pods should be in Running state
```

### 2. Test Routes
```bash
# Get route hostname
ROUTE=$(oc get route fedchat -n fedchat -o jsonpath='{.spec.host}')

# Test frontend
curl -k https://$ROUTE

# Test API health
curl -k https://$ROUTE/api/health
```

### 3. Check Logs
```bash
# Backend logs
oc logs -f deployment/fedchat-backend -n fedchat

# Frontend logs
oc logs -f deployment/fedchat-frontend -n fedchat
```

### 4. Verify Database Connectivity
```bash
# Test PostgreSQL connection
oc exec -it deployment/fedchat-backend -n fedchat -- \
  psql $DATABASE_URL -c "SELECT version();"

# Test Redis connection
oc exec -it deployment/fedchat-redis -n fedchat -- \
  redis-cli -a $REDIS_PASSWORD ping
```

## Performance Considerations

1. **PVC Performance:**
   - Use appropriate storage class (e.g., `gp3-csi` for AWS)
   - Consider using separate storage classes for different workloads

2. **Network Performance:**
   - Routes add minimal overhead
   - Consider using service mesh (OpenShift Service Mesh) for advanced routing

3. **Resource Limits:**
   - HPAs configured for backend (2-10 replicas)
   - HPAs configured for frontend (2-5 replicas)
   - Adjust based on load testing

## Additional OpenShift Features

### 1. Using OpenShift Monitoring
```bash
# Enable user workload monitoring
oc apply -f - <<EOF
apiVersion: v1
kind: ConfigMap
metadata:
  name: cluster-monitoring-config
  namespace: openshift-monitoring
data:
  config.yaml: |
    enableUserWorkload: true
EOF
```

### 2. Using OpenShift Logging
```bash
# Install OpenShift Logging Operator
# Then create ClusterLogging instance
```

### 3. Using OpenShift Pipelines (Tekton)
```bash
# Install OpenShift Pipelines Operator
# Create pipeline for CI/CD
```

## References

- [OpenShift Documentation](https://docs.openshift.com/)
- [Understanding SCCs](https://docs.openshift.com/container-platform/latest/authentication/managing-security-context-constraints.html)
- [OpenShift Routes](https://docs.openshift.com/container-platform/latest/networking/routes/route-configuration.html)
- [FedChat Deployment Guide](../docs/DEPLOYMENT.md)

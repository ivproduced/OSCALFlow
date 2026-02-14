# Kubernetes vs OpenShift Quick Reference

## Quick Comparison Table

| Feature | Kubernetes | OpenShift |
|---------|-----------|-----------|
| **Ingress** | Ingress + NGINX Controller | Routes (built-in HAProxy) |
| **Security** | PSP/PSA | Security Context Constraints (SCC) |
| **User Context** | Often runs as root | Non-root by default (UID 1001+) |
| **Image Registry** | External required | Integrated registry available |
| **CLI** | kubectl | oc (superset of kubectl) |
| **Service Account** | default usually sufficient | Custom SA with SCC binding required |

## Command Equivalents

| Kubernetes Command | OpenShift Command |
|-------------------|-------------------|
| `kubectl apply -f ingress.yaml` | `oc apply -f routes.yaml` |
| `kubectl get ingress` | `oc get routes` |
| N/A | `oc new-project fedchat` |
| `kubectl create secret` | `oc create secret` (same) |
| N/A | `oc new-build` |
| N/A | `oc start-build` |
| `kubectl logs` | `oc logs` (same) |
| N/A | `oc adm policy add-scc-to-user` |

## Key File Changes

### 1. Namespace Configuration
- **Added:** ServiceAccount `fedchat-sa`
- **Added:** OpenShift project annotations

### 2. Database Deployments (PostgreSQL, Redis)
- **Changed:** Security contexts with explicit UIDs
- **Changed:** Init container from busybox → UBI minimal
- **Added:** seccompProfile: RuntimeDefault
- **Added:** allowPrivilegeEscalation: false

### 3. Application Deployments (Backend, Frontend)
- **Changed:** All containers run as UID 1001
- **Added:** emptyDir volumes for /tmp
- **Added:** Strict capability drops (DROP ALL)
- **Changed:** Image references can use image streams

### 4. Networking
- **Replaced:** Ingress → 3 separate Routes
  - Main route for frontend
  - API route with longer timeout
  - Metrics route with IP whitelist
- **Added:** NetworkPolicy for OpenShift ingress

### 5. Security Policies
- **Added:** SecurityContextConstraints (SCC)
- **Added:** RBAC for SCC usage
- **Enhanced:** Network policies for OpenShift DNS
- **Added:** Pod Disruption Budgets

## Deployment Workflow

### Kubernetes
```bash
cd kubernetes
kubectl apply -f 00-namespace-config.yaml
kubectl apply -f 01-postgres.yaml
kubectl apply -f 02-redis.yaml
kubectl apply -f 03-ollama.yaml
kubectl apply -f 04-backend.yaml
kubectl apply -f 05-frontend.yaml
kubectl apply -f 06-ingress.yaml
kubectl apply -f 07-security-policies.yaml
```

### OpenShift
```bash
cd openshift
# Option 1: Automated
./deploy.sh

# Option 2: Manual
oc apply -f 00-namespace-config.yaml
oc apply -f 07-security-policies.yaml  # Requires cluster-admin
oc apply -f 01-postgres.yaml
oc apply -f 02-redis.yaml
oc apply -f 03-ollama.yaml
oc apply -f 04-backend.yaml
oc apply -f 05-frontend.yaml
oc apply -f 06-routes.yaml
```

## Access URLs

### Kubernetes
```
https://fedchat.agency.gov/          # Frontend
https://fedchat.agency.gov/api       # Backend API
https://fedchat.agency.gov/metrics   # Metrics
```

### OpenShift
```
https://fedchat.apps.cluster.com/          # Frontend
https://fedchat.apps.cluster.com/api       # Backend API  
https://fedchat-metrics.apps.cluster.com/  # Metrics (separate route)
```

## Security Context Differences

### Kubernetes Deployment (Less Restrictive)
```yaml
spec:
  containers:
  - name: postgres
    image: pgvector/pgvector:pg16
    # Often runs as root or default user
```

### OpenShift Deployment (More Restrictive)
```yaml
spec:
  serviceAccountName: fedchat-sa
  securityContext:
    runAsNonRoot: true
    runAsUser: 999
    fsGroup: 999
    seccompProfile:
      type: RuntimeDefault
  containers:
  - name: postgres
    image: pgvector/pgvector:pg16
    securityContext:
      allowPrivilegeEscalation: false
      capabilities:
        drop:
        - ALL
      runAsNonRoot: true
      runAsUser: 999
```

## Common Gotchas

### 1. Permission Denied Errors
**Kubernetes:** Less common
**OpenShift:** Common due to strict SCCs
**Solution:** Ensure fsGroup matches container UID

### 2. Image Pull Issues
**Kubernetes:** Configure imagePullSecrets
**OpenShift:** Link secrets to service account
```bash
oc secrets link fedchat-sa regcred --for=pull
```

### 3. Home Directory Issues
**Kubernetes:** /root often writable
**OpenShift:** /root not writable (not running as root)
**Solution:** Use /tmp or emptyDir volumes

### 4. Port Binding < 1024
**Kubernetes:** Usually works
**OpenShift:** Requires specific capabilities (usually denied)
**Solution:** Use ports ≥ 1024

## Testing Checklist

- [ ] All pods running: `oc get pods -n fedchat`
- [ ] Routes accessible: `oc get routes -n fedchat`
- [ ] Database connectivity: `oc exec ... -- psql ...`
- [ ] API health check: `curl https://ROUTE/api/health`
- [ ] Logs streaming: `oc logs -f deployment/fedchat-backend`
- [ ] No SCC violations: `oc describe pod POD | grep Warning`
- [ ] Network policies working: Test connectivity
- [ ] PVCs bound: `oc get pvc -n fedchat`

## Migration Checklist

When converting from Kubernetes to OpenShift:

1. Security
   - [ ] Add serviceAccountName to all deployments
   - [ ] Set runAsUser to non-root UID (1001+)
   - [ ] Add seccompProfile
   - [ ] Drop all capabilities
   - [ ] Set allowPrivilegeEscalation: false

2. Storage
   - [ ] Verify storage class exists
   - [ ] Add fsGroup to match container UID
   - [ ] Add emptyDir for /tmp if needed

3. Networking
   - [ ] Convert Ingress to Routes
   - [ ] Update NetworkPolicies for OpenShift DNS
   - [ ] Add route-specific NetworkPolicies

4. Images
   - [ ] Verify images work as non-root
   - [ ] Update base images if needed (e.g., busybox → UBI)
   - [ ] Test image pull credentials

5. Configuration
   - [ ] Update ConfigMaps with OpenShift-specific values
   - [ ] Verify environment variables
   - [ ] Update domain names for routes

## Additional Resources

- Full migration guide: [MIGRATION_GUIDE.md](./MIGRATION_GUIDE.md)
- OpenShift README: [README.md](./README.md)
- Kubernetes README: [../kubernetes/README.md](../kubernetes/README.md)
- Deployment documentation: [../docs/DEPLOYMENT.md](../docs/DEPLOYMENT.md)

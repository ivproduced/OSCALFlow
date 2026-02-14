# OpenShift Deployment Checklist

Use this checklist when deploying FedChat to OpenShift.

## Pre-Deployment

### Prerequisites
- [ ] OpenShift CLI (oc) installed and configured
- [ ] Logged into OpenShift cluster: `oc login`
- [ ] Verify cluster access: `oc whoami`
- [ ] Cluster admin access (for SCCs) or SCCs pre-configured
- [ ] Storage class available: `oc get storageclass`
- [ ] Container images built and pushed to registry

### Configuration
- [ ] Updated secrets in `00-namespace-config.yaml`:
  - [ ] POSTGRES_PASSWORD (use `openssl rand -hex 32`)
  - [ ] REDIS_PASSWORD (use `openssl rand -hex 32`)
  - [ ] JWT_SECRET (use `openssl rand -hex 32`)
  - [ ] SESSION_SECRET (use `openssl rand -hex 32`)
  - [ ] Other API keys as needed
- [ ] Updated cluster domain in `06-routes.yaml`
- [ ] Updated image references in:
  - [ ] `04-backend.yaml`
  - [ ] `05-frontend.yaml`
- [ ] Updated storage class if needed (default: use cluster default)
- [ ] Reviewed and adjusted resource limits based on cluster capacity

### Security Review
- [ ] Reviewed SCC configuration in `07-security-policies.yaml`
- [ ] All containers run as non-root (UID 1001+)
- [ ] No privileged containers
- [ ] Capabilities properly dropped
- [ ] Network policies reviewed and appropriate

## Deployment Steps

### Step 1: Create Project and Configuration
```bash
oc apply -f 00-namespace-config.yaml
```
- [ ] Namespace created: `oc get namespace fedchat`
- [ ] ServiceAccount created: `oc get sa fedchat-sa -n fedchat`
- [ ] ConfigMap created: `oc get configmap fedchat-config -n fedchat`
- [ ] Secret created: `oc get secret fedchat-secrets -n fedchat`

### Step 2: Apply Security Policies (Requires cluster-admin)
```bash
oc apply -f 07-security-policies.yaml
```
- [ ] SCC created: `oc get scc fedchat-scc`
- [ ] Role created: `oc get role fedchat-scc-role -n fedchat`
- [ ] RoleBinding created: `oc get rolebinding fedchat-scc-rolebinding -n fedchat`
- [ ] Network policies created: `oc get networkpolicies -n fedchat`
- [ ] ResourceQuota created: `oc get resourcequota -n fedchat`
- [ ] LimitRange created: `oc get limitrange -n fedchat`

**If you don't have cluster-admin:**
- [ ] Asked cluster admin to create SCC
- [ ] Verified SCC is available: `oc get scc | grep fedchat`

### Step 3: Deploy PostgreSQL
```bash
oc apply -f 01-postgres.yaml
```
- [ ] PVC created: `oc get pvc postgres-pvc -n fedchat`
- [ ] PVC bound (STATUS: Bound)
- [ ] Service created: `oc get svc fedchat-postgres -n fedchat`
- [ ] Deployment created: `oc get deployment fedchat-postgres -n fedchat`
- [ ] Pod running: `oc get pods -l app=postgres -n fedchat`
- [ ] Database accessible: `oc exec deployment/fedchat-postgres -n fedchat -- pg_isready`

### Step 4: Deploy Redis
```bash
oc apply -f 02-redis.yaml
```
- [ ] PVC created and bound: `oc get pvc redis-pvc -n fedchat`
- [ ] Service created: `oc get svc fedchat-redis -n fedchat`
- [ ] Deployment created: `oc get deployment fedchat-redis -n fedchat`
- [ ] Pod running: `oc get pods -l app=redis -n fedchat`
- [ ] Redis accessible: `oc exec deployment/fedchat-redis -n fedchat -- redis-cli ping`

### Step 5: Deploy Ollama (Optional)
```bash
oc apply -f 03-ollama.yaml
```
- [ ] PVC created and bound: `oc get pvc ollama-pvc -n fedchat`
- [ ] Service created: `oc get svc fedchat-ollama -n fedchat`
- [ ] Deployment created: `oc get deployment fedchat-ollama -n fedchat`
- [ ] Pod running (may take time): `oc get pods -l app=ollama -n fedchat`
- [ ] Ollama accessible: `oc exec deployment/fedchat-ollama -n fedchat -- curl http://localhost:11434/api/tags`

**Note:** Skip if using external LLM provider

### Step 6: Deploy Backend
```bash
oc apply -f 04-backend.yaml
```
- [ ] PVCs created and bound:
  - [ ] `backend-logs-pvc`
  - [ ] `documents-pvc`
- [ ] Service created: `oc get svc fedchat-backend -n fedchat`
- [ ] Deployment created: `oc get deployment fedchat-backend -n fedchat`
- [ ] Pods running (all replicas): `oc get pods -l app=backend -n fedchat`
- [ ] HPA created: `oc get hpa fedchat-backend-hpa -n fedchat`
- [ ] Health check passes: `oc exec deployment/fedchat-backend -n fedchat -- curl http://localhost:8000/health`

### Step 7: Deploy Frontend
```bash
oc apply -f 05-frontend.yaml
```
- [ ] Service created: `oc get svc fedchat-frontend -n fedchat`
- [ ] Deployment created: `oc get deployment fedchat-frontend -n fedchat`
- [ ] Pods running (all replicas): `oc get pods -l app=frontend -n fedchat`
- [ ] HPA created: `oc get hpa fedchat-frontend-hpa -n fedchat`

### Step 8: Create Routes
```bash
oc apply -f 06-routes.yaml
```
- [ ] Routes created: `oc get routes -n fedchat`
- [ ] Main route: `fedchat`
- [ ] API route: `fedchat-api`
- [ ] Metrics route: `fedchat-metrics`
- [ ] All routes have hosts assigned

## Post-Deployment Verification

### System Health
- [ ] All pods in Running state:
  ```bash
  oc get pods -n fedchat
  ```
- [ ] No pods restarting frequently
- [ ] All PVCs bound:
  ```bash
  oc get pvc -n fedchat
  ```

### Connectivity Tests
- [ ] Backend can connect to PostgreSQL:
  ```bash
  oc exec deployment/fedchat-backend -n fedchat -- \
    psql $DATABASE_URL -c "SELECT 1"
  ```
- [ ] Backend can connect to Redis:
  ```bash
  oc exec deployment/fedchat-backend -n fedchat -- \
    python -c "import redis; r=redis.from_url('$REDIS_URL'); print(r.ping())"
  ```
- [ ] Backend API health check:
  ```bash
  curl -k https://$(oc get route fedchat-api -n fedchat -o jsonpath='{.spec.host}')/health
  ```
- [ ] Frontend accessible:
  ```bash
  curl -k https://$(oc get route fedchat -n fedchat -o jsonpath='{.spec.host}')
  ```

### Security Verification
- [ ] Pods running with correct SCC:
  ```bash
  oc get pods -n fedchat -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.metadata.annotations.openshift\.io/scc}{"\n"}{end}'
  ```
- [ ] No privileged containers:
  ```bash
  oc get pods -n fedchat -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.spec.containers[*].securityContext.privileged}{"\n"}{end}'
  ```
- [ ] All containers running as non-root:
  ```bash
  oc get pods -n fedchat -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.spec.securityContext.runAsNonRoot}{"\n"}{end}'
  ```

### Application Verification
- [ ] Create admin user:
  ```bash
  oc exec -it deployment/fedchat-backend -n fedchat -- \
    python scripts/create_admin.py
  ```
- [ ] Test login through frontend
- [ ] Test chat functionality
- [ ] Test file upload (if enabled)
- [ ] Test RAG functionality (if enabled)

### Monitoring
- [ ] Check backend logs:
  ```bash
  oc logs -f deployment/fedchat-backend -n fedchat --tail=50
  ```
- [ ] Check frontend logs:
  ```bash
  oc logs -f deployment/fedchat-frontend -n fedchat --tail=50
  ```
- [ ] Check for errors in events:
  ```bash
  oc get events -n fedchat --sort-by='.lastTimestamp' | tail -20
  ```
- [ ] Verify metrics endpoint:
  ```bash
  curl -k https://$(oc get route fedchat-metrics -n fedchat -o jsonpath='{.spec.host}')/metrics
  ```

## Performance Tuning

### Resource Utilization
- [ ] Check pod resource usage:
  ```bash
  oc adm top pods -n fedchat
  ```
- [ ] Verify HPA status:
  ```bash
  oc get hpa -n fedchat
  ```
- [ ] Review resource quotas:
  ```bash
  oc describe resourcequota fedchat-quota -n fedchat
  ```

### Scaling
- [ ] Test manual scaling:
  ```bash
  oc scale deployment/fedchat-backend --replicas=5 -n fedchat
  ```
- [ ] Verify HPA automatic scaling under load
- [ ] Ensure PDB prevents over-disruption:
  ```bash
  oc get pdb -n fedchat
  ```

## Production Readiness

### Backup
- [ ] Database backup strategy in place
- [ ] Document storage backup configured
- [ ] ConfigMaps and Secrets backed up securely

### Monitoring & Alerting
- [ ] Integrated with OpenShift monitoring (if using user-workload-monitoring)
- [ ] External monitoring configured (Prometheus, Grafana)
- [ ] Alerts configured for:
  - [ ] Pod restarts
  - [ ] High resource usage
  - [ ] API errors
  - [ ] Database connectivity

### Logging
- [ ] Centralized logging configured (Splunk, ELK, etc.)
- [ ] Audit logs being captured
- [ ] Log retention policy in place

### Security
- [ ] Secrets rotated from defaults
- [ ] TLS certificates valid and not expiring soon
- [ ] Network policies tested and working
- [ ] Security scanning completed (container images)
- [ ] Compliance requirements met (FISMA, FedRAMP, etc.)

### Documentation
- [ ] Runbook created for operations team
- [ ] Disaster recovery procedure documented
- [ ] Escalation contacts defined
- [ ] Architecture diagram updated

### Testing
- [ ] Load testing completed
- [ ] Failover testing completed
- [ ] Backup/restore tested
- [ ] Upgrade procedure tested in non-prod

## Rollback Procedure

If deployment fails:
1. Check pod logs: `oc logs <pod-name> -n fedchat`
2. Check events: `oc get events -n fedchat`
3. Rollback deployment:
   ```bash
   oc rollout undo deployment/fedchat-backend -n fedchat
   oc rollout undo deployment/fedchat-frontend -n fedchat
   ```
4. Delete namespace (if needed):
   ```bash
   oc delete namespace fedchat
   ```

## Support Contacts

- **OpenShift Cluster Admin:** [Contact Info]
- **Security Team:** [Contact Info]
- **Database Team:** [Contact Info]
- **Application Team:** [Contact Info]

## Additional Resources

- [OpenShift README](./README.md)
- [Migration Guide](./MIGRATION_GUIDE.md)
- [Kubernetes vs OpenShift Comparison](./KUBERNETES_VS_OPENSHIFT.md)
- [Main Deployment Documentation](../docs/DEPLOYMENT.md)
- [FISMA Compliance](../docs/FISMA_COMPLIANCE.md)

---

**Deployment Date:** _________________

**Deployed By:** _________________

**Sign-off:**
- [ ] Technical Lead
- [ ] Security Officer
- [ ] Operations Manager

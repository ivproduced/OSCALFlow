# Kubernetes Deployment Guide

This directory contains Kubernetes manifests for deploying FedChat in a production environment.

## Prerequisites

- Kubernetes cluster (1.25+)
- kubectl configured with cluster access
- Storage class for persistent volumes
- (Optional) NVIDIA GPU support for Ollama
- (Optional) cert-manager for automatic TLS certificates
- (Optional) NGINX Ingress Controller

## Quick Start

### 1. Configure Secrets

Edit `00-namespace-config.yaml` and update all secret values:

```bash
# Generate secure secrets
openssl rand -hex 32  # For JWT_SECRET
openssl rand -hex 32  # For SESSION_SECRET
openssl rand -hex 16  # For POSTGRES_PASSWORD
openssl rand -hex 16  # For REDIS_PASSWORD
```

**IMPORTANT**: Never commit actual secrets to git!

### 2. Build and Push Images

Build Docker images and push to your container registry:

```bash
# Backend
cd ../backend
docker build -t your-registry/fedchat-backend:latest .
docker push your-registry/fedchat-backend:latest

# Frontend (LibreChat)
cd ../frontend
docker build -t your-registry/fedchat-librechat:latest .
docker push your-registry/fedchat-librechat:latest
```

Update image names in:
- `04-backend.yaml` 
- `05-frontend.yaml`

### 3. Deploy to Kubernetes

```bash
# Apply all manifests in order
kubectl apply -f 00-namespace-config.yaml
kubectl apply -f 01-postgres.yaml
kubectl apply -f 02-redis.yaml
kubectl apply -f 03-ollama.yaml
kubectl apply -f 04-backend.yaml
kubectl apply -f 05-frontend.yaml
kubectl apply -f 06-ingress.yaml
kubectl apply -f 07-security-policies.yaml

# Or apply all at once
kubectl apply -f .
```

### 4. Initialize Database

```bash
# Wait for backend pods to be ready
kubectl wait --for=condition=ready pod -l app=backend -n fedchat --timeout=300s

# Initialize database
kubectl exec -it deployment/fedchat-backend -n fedchat -- python scripts/init_db.py

# Create admin user
kubectl exec -it deployment/fedchat-backend -n fedchat -- python scripts/create_admin.py
```

### 5. Pull Ollama Models

```bash
# Pull required models
kubectl exec -it deployment/fedchat-ollama -n fedchat -- ollama pull llama3:70b
kubectl exec -it deployment/fedchat-ollama -n fedchat -- ollama pull nomic-embed-text
```

## Configuration

### Environment Variables

All configuration is in `00-namespace-config.yaml`:

- **Agency Configuration**: Agency name, classification level
- **LLM Provider**: Choose local (Ollama), Azure OpenAI, or AWS Bedrock
- **RAG Settings**: Chunk size, overlap, similarity threshold
- **Security**: Guardrails, PII detection, content filtering
- **Features**: Enable/disable file upload, conversation export, etc.

### Storage Classes

Update storage class names in PVC definitions based on your cluster:

- AWS: `gp3`, `ebs-sc`
- GCP: `standard`, `ssd`
- Azure: `managed-premium`
- On-prem: Custom storage class

### Resource Requirements

Minimum cluster resources:
- **CPU**: 10 cores
- **Memory**: 32 GB
- **Storage**: 200 GB persistent
- **GPU** (optional): 1x NVIDIA GPU for Ollama

Adjust resource requests/limits in deployment files based on your needs.

## GPU Support for Ollama

If using GPU nodes:

1. Install NVIDIA device plugin:
```bash
kubectl create -f https://raw.githubusercontent.com/NVIDIA/k8s-device-plugin/main/nvidia-device-plugin.yml
```

2. Label GPU nodes:
```bash
kubectl label nodes <node-name> nvidia.com/gpu=true
```

3. Verify GPU is available to Ollama:
```bash
kubectl exec -it deployment/fedchat-ollama -n fedchat -- nvidia-smi
```

## TLS Certificates

### Option 1: cert-manager (Recommended)

Install cert-manager:
```bash
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml
```

Create ClusterIssuer:
```yaml
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: your-email@agency.gov
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: nginx
```

cert-manager will automatically provision certificates.

### Option 2: Manual TLS

Provide your own certificate in `06-ingress.yaml`:

```bash
# Create secret from certificate files
kubectl create secret tls fedchat-tls \
  --cert=path/to/tls.crt \
  --key=path/to/tls.key \
  -n fedchat
```

## Monitoring

### Prometheus Metrics

Backend exposes metrics on `:9090/metrics`:

```bash
# Port forward to access metrics
kubectl port-forward service/fedchat-backend 9090:9090 -n fedchat
curl http://localhost:9090/metrics
```

### View Logs

```bash
# All logs
kubectl logs -f deployment/fedchat-backend -n fedchat

# Specific pod
kubectl logs -f <pod-name> -n fedchat

# Previous container (if crashed)
kubectl logs -p <pod-name> -n fedchat
```

### Health Checks

```bash
# Check all pod status
kubectl get pods -n fedchat

# Check specific service health
kubectl port-forward service/fedchat-backend 8000:8000 -n fedchat
curl http://localhost:8000/health
```

## Scaling

### Manual Scaling

```bash
# Scale backend
kubectl scale deployment fedchat-backend --replicas=5 -n fedchat

# Scale frontend
kubectl scale deployment fedchat-frontend --replicas=3 -n fedchat
```

### Auto-scaling

HorizontalPodAutoscaler is configured in `04-backend.yaml`:
- Min replicas: 2
- Max replicas: 10
- Target CPU: 70%
- Target Memory: 80%

Monitor HPA:
```bash
kubectl get hpa -n fedchat
kubectl describe hpa fedchat-backend-hpa -n fedchat
```

## Security

### Network Policies

Network policies restrict pod-to-pod communication:
- Only ingress controller can access frontend
- Frontend and backend are isolated
- Database only accessible from backend
- External HTTPS allowed for FedRAMP APIs

### Pod Security

Apply pod security standards:

```bash
kubectl label namespace fedchat pod-security.kubernetes.io/enforce=restricted
```

### Secrets Management

**Production Best Practices**:

1. Use external secrets manager:
   - AWS Secrets Manager
   - Azure Key Vault
   - HashiCorp Vault
   - Kubernetes External Secrets Operator

2. Enable secret encryption at rest in etcd

3. Use RBAC to restrict secret access

## Backup and Recovery

### Database Backup

```bash
# Create backup
kubectl exec -it deployment/fedchat-postgres -n fedchat -- \
  pg_dump -U fedchat_user fedchat > backup.sql

# Restore backup
kubectl exec -i deployment/fedchat-postgres -n fedchat -- \
  psql -U fedchat_user fedchat < backup.sql
```

### Automated Backups

Consider using:
- Velero for cluster-level backups
- Database-specific backup solutions (e.g., pgBackRest)

## Troubleshooting

### Pods Not Starting

```bash
# Check pod status
kubectl describe pod <pod-name> -n fedchat

# Check events
kubectl get events -n fedchat --sort-by='.lastTimestamp'
```

### Database Connection Issues

```bash
# Check PostgreSQL logs
kubectl logs deployment/fedchat-postgres -n fedchat

# Test connection from backend
kubectl exec -it deployment/fedchat-backend -n fedchat -- \
  python -c "import asyncio; from core.database import test_connection; asyncio.run(test_connection())"
```

### Ollama Not Responding

```bash
# Check Ollama logs
kubectl logs deployment/fedchat-ollama -n fedchat

# Check if models are loaded
kubectl exec -it deployment/fedchat-ollama -n fedchat -- ollama list

# Test Ollama API
kubectl exec -it deployment/fedchat-ollama -n fedchat -- \
  curl http://localhost:11434/api/tags
```

### Image Pull Errors

```bash
# Check image pull secrets
kubectl get secrets -n fedchat

# Create image pull secret if needed
kubectl create secret docker-registry regcred \
  --docker-server=<your-registry> \
  --docker-username=<username> \
  --docker-password=<password> \
  -n fedchat
```

## Updates and Rollbacks

### Rolling Update

```bash
# Update backend image
kubectl set image deployment/fedchat-backend \
  backend=your-registry/fedchat-backend:v2.0 \
  -n fedchat

# Check rollout status
kubectl rollout status deployment/fedchat-backend -n fedchat
```

### Rollback

```bash
# Rollback to previous version
kubectl rollout undo deployment/fedchat-backend -n fedchat

# Rollback to specific revision
kubectl rollout undo deployment/fedchat-backend --to-revision=2 -n fedchat

# View rollout history
kubectl rollout history deployment/fedchat-backend -n fedchat
```

## FISMA Compliance Checklist

- [ ] All secrets stored in external secrets manager
- [ ] TLS enabled with valid certificates
- [ ] Network policies enforced
- [ ] Pod security policies/standards applied
- [ ] Resource limits configured
- [ ] Logging aggregation enabled
- [ ] Monitoring and alerting configured
- [ ] Regular vulnerability scanning
- [ ] Backup and disaster recovery tested
- [ ] Access controls (RBAC) configured
- [ ] Audit logging enabled
- [ ] Data encryption at rest and in transit

## Support

For issues or questions:
1. Check logs: `kubectl logs -f deployment/fedchat-backend -n fedchat`
2. Check events: `kubectl get events -n fedchat`
3. Review documentation in `/docs`
4. Contact your system administrator

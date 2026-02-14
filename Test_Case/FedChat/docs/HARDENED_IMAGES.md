# Docker Hardened Images Guide

This guide explains how to use hardened Docker images for FedChat in federal/FISMA environments.

## Quick Start

### Automated Build (Recommended)

```bash
# Build Red Hat UBI images (recommended for most federal agencies)
./scripts/build_hardened.sh ubi

# Build Iron Bank images (DoD requirements)
./scripts/build_hardened.sh ironbank

# Build Distroless images (maximum security)
./scripts/build_hardened.sh distroless
```

### Deploy with Hardened Images

```bash
# Set your image preferences
export HARDENED_TYPE=ubi  # or ironbank, distroless
export REGISTRY=registry.access.redhat.com/yourorg  # optional

# Start with hardened images
docker-compose -f docker-compose.hardened.yml up -d
```

## Overview

Hardened Docker images are security-enhanced base images that:
- ✅ Have minimal attack surface (reduced package count)
- ✅ Are regularly scanned for CVEs
- ✅ Follow DISA STIGs and security benchmarks
- ✅ Include security patches and updates
- ✅ Are authorized for federal use

## Hardened Image Sources

### 1. Platform One Iron Bank (Recommended for DoD)

**Iron Bank** is the DoD's centralized repository of hardened container images.

```dockerfile
# Backend - Python hardened image
FROM registry1.dso.mil/ironbank/opensource/python/python311:latest

# Frontend - Node.js hardened image  
FROM registry1.dso.mil/ironbank/opensource/nodejs/nodejs20:latest
```

**Access Requirements:**
- DoD CAC/PKI certificate
- Iron Bank account and approval
- Registry: `registry1.dso.mil`

**Documentation:** https://repo1.dso.mil/

### 2. Red Hat Universal Base Image (UBI)

**Red Hat UBI** images are free, hardened, and suitable for federal use.

```dockerfile
# Backend - Python UBI
FROM registry.access.redhat.com/ubi9/python-311:latest

# Frontend - Node.js UBI
FROM registry.access.redhat.com/ubi9/nodejs-20:latest
```

**Benefits:**
- ✅ Free for any use (even in production)
- ✅ Security-focused with minimal packages
- ✅ Regular CVE scanning and patches
- ✅ FedRAMP compatible

**Documentation:** https://catalog.redhat.com/software/containers/explore

### 3. Google Distroless (Minimal Attack Surface)

**Distroless** images contain only application and runtime dependencies.

```dockerfile
# Backend - Python distroless
FROM gcr.io/distroless/python3-debian12:latest

# Note: Distroless images don't include shell or package managers
# Use multi-stage builds to install dependencies
```

**Benefits:**
- ✅ Minimal attack surface (no shell, package manager)
- ✅ Smaller image size
- ✅ Reduced CVE exposure

**Limitations:**
- ❌ Harder to debug (no shell access)
- ❌ Requires multi-stage builds

### 4. Chainguard Images

**Chainguard** provides minimal, hardened images with SBOM.

```dockerfile
# Backend - Python
FROM cgr.dev/chainguard/python:latest

# Frontend - Node.js
FROM cgr.dev/chainguard/node:latest
```

**Benefits:**
- ✅ Minimal CVEs (often zero)
- ✅ SBOM (Software Bill of Materials) included
- ✅ Regular updates

## Implementation Options

### Option 1: Direct Base Image Replacement

Update existing Dockerfiles to use hardened base images.

#### Backend Dockerfile (Iron Bank)

```dockerfile
FROM registry1.dso.mil/ironbank/opensource/python/python311:latest

WORKDIR /app

# Iron Bank images are minimal - install only required packages
RUN microdnf install -y \
    gcc \
    postgresql-devel \
    && microdnf clean all

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Iron Bank enforces non-root users
USER 1001

EXPOSE 8000 9090

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### Frontend Dockerfile (Iron Bank)

```dockerfile
# Builder stage
FROM registry1.dso.mil/ironbank/opensource/nodejs/nodejs20:latest AS builder

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm ci --legacy-peer-deps

# Copy source and build
COPY . .
RUN npm run frontend

# Production stage
FROM registry1.dso.mil/ironbank/opensource/nodejs/nodejs20:latest

WORKDIR /app

COPY --from=builder /app/package*.json ./
RUN npm ci --omit=dev --legacy-peer-deps && npm cache clean --force

COPY --from=builder /app .

USER 1001

EXPOSE 3000

CMD ["npm", "start"]
```

### Option 2: Red Hat UBI (Easier Access)

#### Backend Dockerfile (UBI)

```dockerfile
FROM registry.access.redhat.com/ubi9/python-311:latest

USER 0

WORKDIR /app

# UBI uses dnf package manager
RUN dnf install -y \
    gcc \
    postgresql-devel \
    && dnf clean all

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# UBI default user is 1001
USER 1001

EXPOSE 8000 9090

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### Frontend Dockerfile (UBI)

```dockerfile
# Builder stage
FROM registry.access.redhat.com/ubi9/nodejs-20:latest AS builder

USER 0
WORKDIR /app

RUN dnf install -y git && dnf clean all

COPY package*.json ./
RUN npm ci --legacy-peer-deps

COPY . .
RUN npm run frontend

# Production stage
FROM registry.access.redhat.com/ubi9/nodejs-20-minimal:latest

USER 0
WORKDIR /app

COPY --from=builder /app/package*.json ./
RUN npm ci --omit=dev --legacy-peer-deps && npm cache clean --force

COPY --from=builder /app .

USER 1001

EXPOSE 3000

CMD ["npm", "start"]
```

### Option 3: Distroless (Maximum Security)

#### Backend Dockerfile (Distroless)

```dockerfile
# Builder stage with full tooling
FROM python:3.11-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

COPY . .

# Production stage - distroless
FROM gcr.io/distroless/python3-debian12:latest

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /root/.local /root/.local
COPY --from=builder /app .

# Set PATH for pip-installed packages
ENV PATH=/root/.local/bin:$PATH

# Distroless runs as non-root by default
USER nonroot

EXPOSE 8000 9090

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Note:** Distroless doesn't support HEALTHCHECK with curl. Use TCP socket check instead.

## Security Scanning

### Scan Images for Vulnerabilities

```bash
# Using Trivy (recommended)
trivy image fedchat-backend:latest

# Using Grype
grype fedchat-backend:latest

# Using Docker Scout
docker scout cves fedchat-backend:latest

# Using Anchore
anchore-cli image add fedchat-backend:latest
anchore-cli image vuln fedchat-backend:latest all
```

### Automated Scanning in CI/CD

```yaml
# GitHub Actions example
- name: Scan Docker image
  uses: aquasecurity/trivy-action@master
  with:
    image-ref: 'fedchat-backend:latest'
    format: 'sarif'
    output: 'trivy-results.sarif'
    severity: 'CRITICAL,HIGH'
```

## Configuration Updates

### Docker Compose with Hardened Images

```yaml
services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile.hardened  # Use hardened Dockerfile
    image: fedchat-backend:hardened
    security_opt:
      - no-new-privileges:true
    cap_drop:
      - ALL
    cap_add:
      - NET_BIND_SERVICE
    read_only: true
    tmpfs:
      - /tmp
      - /var/tmp
```

### OpenShift Deployment

OpenShift enforces security by default and works well with hardened images:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: fedchat-backend
spec:
  template:
    spec:
      securityContext:
        runAsNonRoot: true
        seccompProfile:
          type: RuntimeDefault
      containers:
      - name: backend
        image: registry1.dso.mil/yourorg/fedchat-backend:latest
        imagePullPolicy: Always
        securityContext:
          allowPrivilegeEscalation: false
          runAsUser: 1001
          capabilities:
            drop:
              - ALL
        readOnlyRootFilesystem: true
        volumeMounts:
        - name: tmp
          mountPath: /tmp
      volumes:
      - name: tmp
        emptyDir: {}
```

## Best Practices

### 1. Use Multi-Stage Builds

Separate build dependencies from runtime:

```dockerfile
# Build stage - full tools
FROM python:3.11 AS builder
RUN pip install --user -r requirements.txt

# Runtime stage - minimal
FROM gcr.io/distroless/python3
COPY --from=builder /root/.local /root/.local
```

### 2. Run as Non-Root User

Always run containers as non-root:

```dockerfile
# Create user
RUN useradd -m -u 1001 appuser

# Switch to non-root
USER 1001
```

### 3. Minimize Attack Surface

```dockerfile
# Remove unnecessary packages
RUN apt-get remove -y build-essential && \
    apt-get autoremove -y && \
    rm -rf /var/lib/apt/lists/*
```

### 4. Use Specific Image Tags

Avoid `latest` tags in production:

```dockerfile
# Bad
FROM python:latest

# Good
FROM registry1.dso.mil/ironbank/opensource/python/python311:v3.11.8
```

### 5. Scan Before Deployment

```bash
# Fail build on HIGH/CRITICAL CVEs
trivy image --severity HIGH,CRITICAL --exit-code 1 fedchat-backend:latest
```

## Image Registry Configuration

### Private Registry Authentication

```bash
# Docker login to Iron Bank
docker login registry1.dso.mil -u <USERNAME>

# Pull hardened image
docker pull registry1.dso.mil/ironbank/opensource/python/python311:latest
```

### Configure Kubernetes Image Pull Secrets

```bash
# Create secret
kubectl create secret docker-registry ironbank-pull-secret \
  --docker-server=registry1.dso.mil \
  --docker-username=<USERNAME> \
  --docker-password=<PASSWORD> \
  -n fedchat

# Reference in deployment
spec:
  imagePullSecrets:
  - name: ironbank-pull-secret
```

## STIG Compliance

Hardened images should follow DISA STIGs:

- ✅ Container Platform STIG
- ✅ Application STIG
- ✅ OS STIG (for base image)

**Key STIG Requirements:**
1. Run as non-root user
2. Read-only root filesystem
3. No privileged containers
4. Resource limits defined
5. Regular vulnerability scanning
6. Audit logging enabled

## Comparison Matrix

| Image Type | Security | Ease of Use | CVE Count | Federal Auth |
|------------|----------|-------------|-----------|--------------|
| **Iron Bank** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | Very Low | DoD Only |
| **Red Hat UBI** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | Low | Yes |
| **Distroless** | ⭐⭐⭐⭐⭐ | ⭐⭐ | Very Low | No |
| **Chainguard** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | Zero/Low | No |
| **Alpine** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Varies | No |

## Migration Checklist

- [ ] Choose hardened base image (Iron Bank, UBI, etc.)
- [ ] Update Dockerfiles with new base images
- [ ] Test builds locally
- [ ] Configure registry authentication
- [ ] Run vulnerability scans
- [ ] Update CI/CD pipeline
- [ ] Test deployments in dev environment
- [ ] Document image sources and versions
- [ ] Update docker-compose.yml
- [ ] Update Kubernetes/OpenShift manifests
- [ ] Train team on new image usage
- [ ] Set up automated scanning
- [ ] Deploy to production

## Resources

- **Iron Bank**: https://repo1.dso.mil/
- **Red Hat UBI**: https://catalog.redhat.com/software/containers/explore
- **Distroless**: https://github.com/GoogleContainerTools/distroless
- **Chainguard**: https://www.chainguard.dev/
- **Trivy Scanner**: https://github.com/aquasecurity/trivy
- **DISA STIGs**: https://public.cyber.mil/stigs/
- **CIS Benchmarks**: https://www.cisecurity.org/cis-benchmarks

## Support

For federal environment-specific guidance:
- Contact your security team for approved base images
- Check your organization's container registry
- Review agency-specific security requirements
- Consult with DevSecOps team for CI/CD integration

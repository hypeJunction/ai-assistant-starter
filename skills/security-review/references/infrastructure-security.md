# Infrastructure Security Reference

Covers Docker, Kubernetes, Terraform, and CI/CD infrastructure security. Load this reference when reviewing Dockerfiles, deployment manifests, infrastructure-as-code, or cloud configuration.

## Docker Security

### Dockerfile Checks

```dockerfile
# BAD: Running as root (default)
FROM node:20
COPY . .
RUN npm ci
CMD ["node", "server.js"]

# GOOD: Non-root user, minimal base, no secrets in layers
FROM node:20-slim AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci --omit=dev

FROM node:20-slim
RUN addgroup --system app && adduser --system --ingroup app app
WORKDIR /app
COPY --from=build /app/node_modules ./node_modules
COPY . .
USER app
EXPOSE 3000
CMD ["node", "server.js"]
```

### Checklist

| Check | Risk |
|-------|------|
| `USER` directive present and non-root | Privilege escalation |
| Base image is slim/alpine/distroless | Reduced attack surface |
| Multi-stage build (build deps not in final image) | Smaller image, fewer vulns |
| No `COPY . .` before dependency install | Cache invalidation, secret leak |
| No secrets in `ENV`, `ARG`, or `COPY` | Secret exposure in image layers |
| `HEALTHCHECK` defined | Availability monitoring |
| `.dockerignore` excludes `.env`, `.git`, `node_modules` | Secret and bloat prevention |
| No `--privileged` flag in docker-compose | Container escape |
| Read-only filesystem where possible | Tamper prevention |
| No `latest` tag for base images | Reproducibility |

### Secrets in Layers

```dockerfile
# BAD: Secret baked into layer (visible in image history)
COPY .env /app/.env
ENV API_KEY=sk_live_abc123

# BAD: Secret in build arg (visible in image metadata)
ARG DATABASE_URL
ENV DATABASE_URL=$DATABASE_URL

# GOOD: Use runtime secrets
# Mount secrets at runtime via docker-compose or orchestrator
# docker run -e API_KEY=$API_KEY myapp
# Or use Docker secrets / external secret managers
```

### Image Scanning

```bash
# Scan for known vulnerabilities
docker scout cves myimage:latest
trivy image myimage:latest
grype myimage:latest
```

## Kubernetes Security

### Pod Security

```yaml
# GOOD: Restricted security context
apiVersion: v1
kind: Pod
spec:
  securityContext:
    runAsNonRoot: true
    runAsUser: 1000
    fsGroup: 1000
  containers:
    - name: app
      image: myapp:1.2.3  # Pinned version, not :latest
      securityContext:
        allowPrivilegeEscalation: false
        readOnlyRootFilesystem: true
        capabilities:
          drop: ["ALL"]
      resources:
        limits:
          cpu: "500m"
          memory: "256Mi"
        requests:
          cpu: "100m"
          memory: "128Mi"
```

### Checklist

| Check | Risk |
|-------|------|
| `runAsNonRoot: true` | Privilege escalation |
| `allowPrivilegeEscalation: false` | Container breakout |
| `readOnlyRootFilesystem: true` | Tamper prevention |
| `capabilities.drop: ["ALL"]` | Reduced kernel attack surface |
| Resource limits set (cpu, memory) | DoS via resource exhaustion |
| Image tags pinned to digest or version | Supply chain attack |
| `hostNetwork: false` (default) | Network isolation |
| `hostPID: false` (default) | Process isolation |
| No `privileged: true` | Full host access |
| NetworkPolicy applied | Lateral movement |

### Secrets Management

```yaml
# BAD: Secret in plain YAML
apiVersion: v1
kind: Secret
metadata:
  name: api-creds
data:
  api-key: c2tfbGl2ZV9hYmMxMjM=  # Just base64, not encrypted

# GOOD: Use external secret operator or sealed secrets
# External Secrets Operator, Vault, AWS Secrets Manager, etc.
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
spec:
  secretStoreRef:
    name: vault-backend
  data:
    - secretKey: api-key
      remoteRef:
        key: secret/api-creds
        property: api-key
```

### RBAC

```yaml
# BAD: Overly permissive ClusterRole
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
rules:
  - apiGroups: ["*"]
    resources: ["*"]
    verbs: ["*"]

# GOOD: Minimal permissions
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  namespace: app
rules:
  - apiGroups: [""]
    resources: ["pods", "services"]
    verbs: ["get", "list"]
```

## Terraform Security

### State File Protection

```hcl
# GOOD: Remote state with encryption
terraform {
  backend "s3" {
    bucket         = "terraform-state"
    key            = "prod/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-locks"
  }
}
```

### Checklist

| Check | Risk |
|-------|------|
| State file stored remotely with encryption | Secret exposure (state contains all values) |
| State locking enabled (DynamoDB, etc.) | Race conditions on apply |
| No hardcoded secrets in `.tf` files | Secret exposure |
| Variables marked `sensitive = true` | Prevents accidental logging |
| Provider versions pinned | Supply chain |
| `.terraform.lock.hcl` committed | Reproducibility |
| No `terraform.tfstate` in git | Full infrastructure secret exposure |

### IAM / Least Privilege

```hcl
# BAD: Overly permissive IAM
resource "aws_iam_policy" "bad" {
  policy = jsonencode({
    Statement = [{
      Effect   = "Allow"
      Action   = "*"
      Resource = "*"
    }]
  })
}

# GOOD: Minimal permissions
resource "aws_iam_policy" "good" {
  policy = jsonencode({
    Statement = [{
      Effect   = "Allow"
      Action   = ["s3:GetObject", "s3:PutObject"]
      Resource = "arn:aws:s3:::my-bucket/*"
    }]
  })
}
```

### Dangerous Patterns

```hcl
# Flag these:
ingress {
  from_port   = 0
  to_port     = 0
  protocol    = "-1"
  cidr_blocks = ["0.0.0.0/0"]  # Open to entire internet
}

# Public S3 bucket
resource "aws_s3_bucket_public_access_block" "bad" {
  block_public_acls       = false  # Should be true
  block_public_policy     = false
  ignore_public_acls      = false
  restrict_public_buckets = false
}

# Unencrypted storage
resource "aws_db_instance" "bad" {
  storage_encrypted = false  # Should be true
}
```

## CI/CD Security

### GitHub Actions

```yaml
# GOOD: Minimal permissions, pinned actions, no secret leaks
name: CI
on: [push]

permissions:
  contents: read

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683 # v4.2.2
      - uses: actions/setup-node@39370e3970a6d050c480ffad4ff0ed4d3fdee5af # v4.1.0
        with:
          node-version: 20
      - run: npm ci
      - run: npm test
```

### Checklist

| Check | Risk |
|-------|------|
| `permissions` explicitly set (not default) | Excessive token scope |
| Actions pinned to SHA (not tag) | Action supply chain attack |
| No `pull_request_target` with PR checkout | Secret exposure to forks |
| Secrets not in `echo` or artifact uploads | Secret leak |
| Self-hosted runners are ephemeral | Persistent compromise |
| `CODEOWNERS` protects workflow files | Unauthorized pipeline changes |
| Branch protection on main/release branches | Unauthorized deployments |
| OIDC for cloud auth (not long-lived keys) | Credential rotation |

### GitLab CI

```yaml
# GOOD: Protected variables, minimal image
image: node:20-slim

variables:
  NODE_ENV: production
  # Secrets should be in CI/CD Variables (protected + masked)

stages:
  - test
  - deploy

test:
  stage: test
  script:
    - npm ci --frozen-lockfile
    - npm test
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
```

## Cloud Security Patterns

### Common Misconfigurations

| Service | Misconfiguration | Risk |
|---------|------------------|------|
| S3/GCS | Public bucket | Data exposure |
| RDS/Cloud SQL | Public access enabled | Database compromise |
| IAM | Wildcard permissions (`*`) | Full account takeover |
| Security Groups | 0.0.0.0/0 on management ports | Unauthorized access |
| KMS | Key rotation disabled | Key compromise impact |
| CloudFront/CDN | No WAF association | Direct attack surface |
| Lambda/Cloud Functions | Overprivileged execution role | Lateral movement |
| API Gateway | No authentication | Unauthorized API access |

### What to Check

- Are cloud resources using encryption at rest and in transit?
- Are IAM roles following least privilege?
- Are security groups/firewalls restrictive (no 0.0.0.0/0 on SSH/RDP)?
- Are logging and monitoring enabled (CloudTrail, VPC Flow Logs)?
- Is MFA enforced for console access?
- Are secrets managed via a secrets manager (not env vars or config files)?

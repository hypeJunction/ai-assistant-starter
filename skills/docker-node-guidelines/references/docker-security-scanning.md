# Docker Security: Read-Only Filesystem and Vulnerability Scanning

Reference for running containers with read-only filesystems and scanning images for vulnerabilities.

## Read-Only Filesystem

```dockerfile
# In docker-compose or runtime
docker run --read-only --tmpfs /tmp myapp
```

## Scan for Vulnerabilities

```bash
# Scan image
docker scout cves myapp:latest

# Or use Trivy
trivy image myapp:latest

# In CI
- name: Scan image
  uses: aquasecurity/trivy-action@master
  with:
    image-ref: myapp:latest
    severity: 'CRITICAL,HIGH'
    exit-code: '1'
```

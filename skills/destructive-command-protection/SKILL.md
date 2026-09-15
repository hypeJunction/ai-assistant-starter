---
name: destructive-command-protection
description: Runtime enforcement hook that blocks destructive system and database commands. Prevents accidental rm -rf, database drops, and other irreversible operations. Auto-loaded for all command execution.
category: enforcement
user-invocable: false
---

# Destructive Command Protection

Runtime enforcement hook for Claude Code's PreToolUse hook system. Intercepts Bash tool calls and blocks commands that could cause irreversible damage.

## Blocked Operations

### Filesystem

| Command Pattern | Risk | Action |
|----------------|------|--------|
| `rm -rf /` or `rm -rf ~` or `rm -rf .` | Filesystem destruction | Block |
| `rm -rf /etc`, `/usr`, `/var`, `/boot`, `/home` | System directory deletion | Block |
| `rm -rf $HOME` | Home directory deletion | Block |

**Safe targets (allowed):** `node_modules`, `dist/`, `build/`, `.next/`, `.cache/`, `coverage/`, `.turbo/`, `tmp/`, `.tmp/`, `out/`

### Database & Data Stores

| Command Pattern | Risk | Action |
|----------------|------|--------|
| `DROP DATABASE` / `DROP SCHEMA` | Database destruction | Block |
| `TRUNCATE TABLE` (without IF EXISTS) | Mass data deletion | Block |
| `redis-cli FLUSHALL` / `FLUSHDB` | Wipes all Redis data | Block |
| `mongosh db.dropDatabase()` / `.drop()` | MongoDB destruction | Block |

### Git

| Command Pattern | Risk | Action |
|----------------|------|--------|
| `git stash drop` | Permanently deletes a stash entry | Block |
| `git stash clear` | Permanently deletes all stashes | Block |

### System

| Command Pattern | Risk | Action |
|----------------|------|--------|
| `mkfs` / `dd if= of=/dev/` | Disk formatting/overwrite | Block |
| `> /dev/sda` or writes to block devices | Disk corruption | Block |
| `chmod -R 777 /` | Security degradation | Block |
| `:(){ :|:& };:` (fork bomb) | System crash | Block |
| `kill -9 1` / `kill -9 -1` | System process termination | Block |

### Containers

| Command Pattern | Risk | Action |
|----------------|------|--------|
| `docker system prune` | Removes all unused containers, images, volumes | Block |
| `docker volume prune` | Removes all unused volumes with data | Block |
| `docker container prune` / `image prune` | Mass container/image removal | Block |
| `docker compose down -v` | Removes volumes with persistent data | Block |

### Infrastructure as Code

| Command Pattern | Risk | Action |
|----------------|------|--------|
| `terraform destroy` | Tears down infrastructure | Block |
| `terraform apply -auto-approve` | Applies without review | Block |
| `pulumi destroy` | Tears down infrastructure | Block |

### Package Publishing

| Command Pattern | Risk | Action |
|----------------|------|--------|
| `npm publish` / `yarn publish` | Irreversible public release | Block |
| `gem push` / `twine upload` / `cargo publish` | Irreversible public release | Block |

### Cloud Resources

| Command Pattern | Risk | Action |
|----------------|------|--------|
| `aws ec2 terminate-instances` | Destroys EC2 instances | Block |
| `aws rds delete-db-instance` | Destroys RDS database | Block |
| `aws cloudformation delete-stack` | Destroys CloudFormation stack | Block |
| `aws secretsmanager delete-secret` | Destroys secrets | Block |
| `aws iam delete-role` | Removes IAM role | Block |
| `gcloud compute instances delete` | Destroys GCE instance | Block |
| `gcloud sql instances delete` | Destroys Cloud SQL instance | Block |
| `gcloud projects delete` | Destroys GCP project | Block |
| `az vm delete` / `az group delete` | Destroys Azure resources | Block |
| `az storage account delete` / `az keyvault delete` | Destroys Azure storage/keys | Block |

### Kubernetes

| Command Pattern | Risk | Action |
|----------------|------|--------|
| `kubectl delete namespace` / `ns` | Mass resource deletion | Block |
| `kubectl delete ... --all` | Mass resource deletion | Block |
| `kubectl drain` | Evicts all pods from node | Block |

### Network & Storage

| Command Pattern | Risk | Action |
|----------------|------|--------|
| `rsync --delete` | Removes destination files not in source | Block |
| `aws s3 rm --recursive` / `aws s3 rb --recursive` | Mass S3 deletion | Block |
| `gsutil rm -r` | Mass GCS deletion | Block |
| `azcopy remove --recursive` | Mass Azure blob deletion | Block |

### Bypass Prevention

| Technique | Detection | Action |
|-----------|-----------|--------|
| `bash -c "blocked command"` | Shell wrapper extraction | Block |
| `sh -c 'blocked command'` | Shell wrapper extraction | Block |
| `python -c "os.system(...)"` | Interpreter one-liner scan | Block |
| `node -e "execSync(...)"` | Interpreter one-liner scan | Block |
| `ruby -e "system(...)"` | Interpreter one-liner scan | Block |

## When a Legitimate Operation Is Blocked

The hook blocks the command outright and does not execute it — it never runs a destructive command with hidden safety flags. If a blocked operation is genuinely needed (e.g. a real `DROP DATABASE` on a decommissioned dev DB), do not try to bypass the hook (no alternate quoting, interpreter one-liners, or disabling the hook). Instead:

1. Take a backup/snapshot first (e.g. `pg_dump`, an RDS/Cloud SQL snapshot, an EBS/volume snapshot, `terraform state pull`, an S3/GCS bucket sync to a backup location) appropriate to the resource.
2. Explain to the user what's blocked and why, and confirm the backup is in place.
3. Have the user run the command themselves outside the hooked environment, or explicitly ask them to temporarily disable the hook for that one command.

Never advise disabling this hook globally or permanently to work around a single blocked command.

## Installation

Add to your Claude Code settings (`~/.claude/settings.json` or project `.claude/settings.json`):

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "node .claude/skills/destructive-command-protection/references/hook.js"
          }
        ]
      }
    ]
  }
}
```

## Acceptance Tests

| ID | Type | Condition | Expected |
|----|------|-----------|----------|
| DC-T1 | Block | `rm -rf /` | Blocked |
| DC-T2 | Block | `rm -rf ~` | Blocked |
| DC-T3 | Block | `DROP DATABASE production` | Blocked |
| DC-T4 | Block | `chmod -R 777 /` | Blocked |
| DC-T5 | Allow | `rm -rf ./node_modules` | Allowed (safe target) |
| DC-T6 | Allow | `rm -rf dist/` | Allowed (build artifact) |
| DC-T7 | Allow | `DROP TABLE IF EXISTS temp_migration` | Allowed (TABLE not matched) |
| DC-T8 | Block | `dd if=/dev/zero of=/dev/sda` | Blocked |
| DC-T9 | Block | `git stash clear` | Blocked |
| DC-T10 | Allow | `git stash pop` | Allowed (not destructive) |
| DC-T11 | Block | `bash -c "rm -rf /"` | Blocked (shell wrapper) |
| DC-T12 | Block | `python -c "import shutil; shutil.rmtree(...)"` | Blocked (interpreter) |
| DC-T13 | Block | `docker system prune` | Blocked |
| DC-T14 | Allow | `docker compose down` | Allowed (no -v) |
| DC-T15 | Block | `terraform destroy` | Blocked |
| DC-T16 | Allow | `terraform plan` | Allowed (read-only) |
| DC-T17 | Block | `npm publish` | Blocked |
| DC-T18 | Block | `aws ec2 terminate-instances` | Blocked |
| DC-T19 | Block | `kubectl delete namespace production` | Blocked |
| DC-T20 | Allow | `kubectl get pods` | Allowed (read-only) |
| DC-T21 | Block | `rsync --delete src/ dest/` | Blocked |
| DC-T22 | Block | `aws s3 rm --recursive` | Blocked |
| DC-T23 | Block | `redis-cli FLUSHALL` | Blocked |
| DC-T24 | Block | `mongosh --eval "db.dropDatabase()"` | Blocked |

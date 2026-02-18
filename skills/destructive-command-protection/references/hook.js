#!/usr/bin/env node

/**
 * Destructive Command Protection Hook for Claude Code
 *
 * Intercepts Bash tool calls and blocks commands that could cause
 * irreversible system or data damage.
 *
 * Hook protocol: reads tool input from stdin as JSON,
 * outputs JSON decision to stdout.
 *
 * Rule categories:
 *   1. Filesystem destruction (rm -rf)
 *   2. Database destruction (DROP, TRUNCATE, FLUSHALL)
 *   3. Disk operations (mkfs, dd, block device writes)
 *   4. System abuse (chmod 777, fork bomb, kill init)
 *   5. Git data destruction (stash drop/clear)
 *   6. Shell wrapper bypass (bash -c, sh -c wrapping blocked commands)
 *   7. Interpreter one-liners (python -c, node -e with destructive calls)
 *   8. Container destruction (docker system prune, volume prune, compose down -v)
 *   9. Infrastructure destruction (terraform destroy, pulumi destroy)
 *  10. Package publishing (npm publish, etc.)
 *  11. Cloud resource destruction (aws, gcloud, az mass delete)
 *  12. Kubernetes mass deletion (kubectl delete namespace, drain)
 *  13. Rsync with --delete
 *  14. Cloud storage mass deletion (s3 rm --recursive, gsutil rm -r)
 */

function getInput() {
  return new Promise((resolve) => {
    let data = '';
    process.stdin.setEncoding('utf8');
    process.stdin.on('data', (chunk) => { data += chunk; });
    process.stdin.on('end', () => {
      try {
        resolve(JSON.parse(data));
      } catch {
        resolve(null);
      }
    });
  });
}

function extractCommand(input) {
  if (!input) return '';
  const cmd = input.tool_input?.command || input.input?.command || '';
  return cmd.trim();
}

const DANGEROUS_RM_TARGETS = [
  /^\/$/,
  /^\/\s/,
  /^~\/?$/,
  /^\$HOME\/?$/i,
  /^\/home\/?$/,
  /^\/etc\/?$/,
  /^\/usr\/?$/,
  /^\/var\/?$/,
  /^\/boot\/?$/,
  /^\.\.\/\.\.\//,
  /^\.\/?$/,
];

const SAFE_RM_TARGETS = [
  /node_modules/,
  /dist\/?$/,
  /build\/?$/,
  /\.next\/?$/,
  /\.cache\/?$/,
  /coverage\/?$/,
  /\.turbo\/?$/,
  /tmp\/?$/,
  /\.tmp\/?$/,
  /out\/?$/,
];

/**
 * Extract the inner command from shell wrappers like:
 *   bash -c "rm -rf /"
 *   sh -c 'git stash clear'
 *   zsh -c "dangerous command"
 * Returns the inner command string, or null if not a wrapper.
 */
function extractShellWrapper(cmd) {
  // Try double-quoted wrapper first, then single-quoted
  const dq = cmd.match(
    /(?:^|&&|\|\||;)\s*(?:bash|sh|zsh)\s+-c\s+"([^"]+)"/
  );
  if (dq) return dq[1];
  const sq = cmd.match(
    /(?:^|&&|\|\||;)\s*(?:bash|sh|zsh)\s+-c\s+'([^']+)'/
  );
  return sq ? sq[1] : null;
}

/**
 * Check for destructive patterns inside interpreter one-liners:
 *   python -c 'import os; os.system("rm -rf /")'
 *   node -e 'require("child_process").execSync("rm -rf /")'
 *   ruby -e 'system("rm -rf /")'
 */
function checkInterpreterOneliner(cmd) {
  const lower = cmd.toLowerCase();

  // python -c / python3 -c
  if (/(?:python3?|python3?\.\d+)\s+-c\s+/.test(lower)) {
    const dangerousPatterns = [
      /shutil\.rmtree/i,
      /os\.system\s*\(/i,
      /os\.remove/i,
      /os\.unlink/i,
      /subprocess\.\w+\s*\(/i,
      /pathlib\..*\.unlink/i,
    ];
    if (dangerousPatterns.some((p) => p.test(cmd))) {
      return {
        decision: 'block',
        reason:
          'Destructive Python one-liner blocked. Avoid inline destructive operations — use a script file instead.',
      };
    }
  }

  // node -e / node --eval
  if (/node\s+(-e|--eval)\s+/.test(lower)) {
    const dangerousPatterns = [
      /execSync\s*\(/i,
      /exec\s*\(/i,
      /rmSync\s*\(/i,
      /rmdirSync\s*\(/i,
      /unlinkSync\s*\(/i,
      /rm\s*\(\s*.*recursive/i,
    ];
    if (dangerousPatterns.some((p) => p.test(cmd))) {
      return {
        decision: 'block',
        reason:
          'Destructive Node.js one-liner blocked. Avoid inline destructive operations — use a script file instead.',
      };
    }
  }

  // ruby -e
  if (/ruby\s+-e\s+/.test(lower)) {
    const dangerousPatterns = [
      /FileUtils\.rm_rf/i,
      /FileUtils\.remove/i,
      /system\s*\(/i,
      /`[^`]*rm\s/i,
    ];
    if (dangerousPatterns.some((p) => p.test(cmd))) {
      return {
        decision: 'block',
        reason:
          'Destructive Ruby one-liner blocked. Avoid inline destructive operations — use a script file instead.',
      };
    }
  }

  return null;
}

function checkDestructiveCommand(cmd, _depth) {
  const depth = _depth || 0;
  const lower = cmd.toLowerCase();

  // ── 1. Filesystem destruction: rm -rf ──
  const rmMatch = lower.match(
    /rm\s+(-[a-z]*r[a-z]*f[a-z]*|-[a-z]*f[a-z]*r[a-z]*)\s+(.*)/
  );
  if (rmMatch) {
    const target = rmMatch[2].trim().split(/\s/)[0];
    const isSafe = SAFE_RM_TARGETS.some((p) => p.test(target));
    if (isSafe) return null;
    const isDangerous = DANGEROUS_RM_TARGETS.some((p) => p.test(target));
    if (isDangerous) {
      return {
        decision: 'block',
        reason: `Destructive command blocked: 'rm -rf ${target}' targets a critical path. Specify a safe, scoped path instead.`,
      };
    }
  }

  // ── 2. Database destruction ──

  // DROP DATABASE / DROP SCHEMA
  if (/drop\s+(database|schema)\s+/i.test(cmd)) {
    return {
      decision: 'block',
      reason:
        'DROP DATABASE/SCHEMA blocked. This is an irreversible operation. Ask the user to confirm and run manually.',
    };
  }

  // TRUNCATE TABLE (without IF EXISTS)
  if (/truncate\s+table\s+/i.test(cmd) && !/where\s+/i.test(cmd)) {
    if (/if\s+exists/i.test(cmd)) return null;
    return {
      decision: 'block',
      reason:
        'TRUNCATE TABLE blocked as a safety measure. Ask the user to confirm this data deletion.',
    };
  }

  // Redis FLUSHALL / FLUSHDB
  if (/\bredis-cli\b/.test(lower) && /\b(flushall|flushdb)\b/.test(lower)) {
    return {
      decision: 'block',
      reason:
        'Redis FLUSHALL/FLUSHDB blocked. This wipes all data. Ask the user to confirm and run manually.',
    };
  }

  // MongoDB dropDatabase / drop()
  if (
    /\bmongo(?:sh)?\b/.test(lower) &&
    /\.(dropdatabase|drop)\s*\(/.test(lower)
  ) {
    return {
      decision: 'block',
      reason:
        'MongoDB drop operation blocked. This is irreversible. Ask the user to confirm and run manually.',
    };
  }

  // ── 3. Disk operations ──
  if (/mkfs[\s.]/.test(lower) || /dd\s+if=.*of=\/dev\//.test(lower)) {
    return {
      decision: 'block',
      reason:
        'Disk format/overwrite operation blocked. This is an irreversible operation.',
    };
  }

  // Block: writes to block devices
  if (/>\s*\/dev\/[sh]d[a-z]/.test(lower)) {
    return {
      decision: 'block',
      reason: 'Write to block device blocked. This would corrupt the disk.',
    };
  }

  // ── 4. System abuse ──

  // chmod 777 on system paths
  if (/chmod\s+(-R\s+)?777\s+\//.test(cmd)) {
    return {
      decision: 'block',
      reason:
        'chmod -R 777 on system paths blocked. This is a security risk. Use specific permissions instead.',
    };
  }

  // Fork bomb
  if (/:\(\)\s*\{.*\|.*&\s*\}\s*;?\s*:/.test(cmd)) {
    return {
      decision: 'block',
      reason: 'Fork bomb pattern detected and blocked.',
    };
  }

  // Kill init/all
  if (/kill\s+(-9\s+)?(-1|1)\b/.test(lower)) {
    return {
      decision: 'block',
      reason:
        'Killing init/all processes blocked. Specify a specific process ID.',
    };
  }

  // ── 5. Git data destruction ──

  // git stash drop / git stash clear
  if (/git\s+stash\s+(drop|clear)\b/.test(lower)) {
    return {
      decision: 'block',
      reason:
        'git stash drop/clear blocked. This permanently deletes stashed work. Ask the user to confirm.',
    };
  }

  // ── 6. Shell wrapper bypass ──
  if (depth < 2) {
    const innerCmd = extractShellWrapper(lower);
    if (innerCmd) {
      const innerResult = checkDestructiveCommand(innerCmd, depth + 1);
      if (innerResult) {
        return {
          decision: 'block',
          reason: `Shell wrapper detected: ${innerResult.reason}`,
        };
      }
    }
  }

  // ── 7. Interpreter one-liners ──
  const interpreterResult = checkInterpreterOneliner(cmd);
  if (interpreterResult) return interpreterResult;

  // ── 8. Container destruction ──

  // docker system prune / docker volume prune / docker container prune
  if (
    /docker\s+(system|volume|container|image|builder)\s+prune/.test(lower)
  ) {
    return {
      decision: 'block',
      reason:
        'Docker prune blocked. This permanently removes containers, volumes, or images. Ask the user to confirm.',
    };
  }

  // docker compose down -v (removes volumes)
  if (/docker\s+compose\s+down\s+.*-v|docker-compose\s+down\s+.*-v/.test(lower)) {
    return {
      decision: 'block',
      reason:
        'docker compose down -v blocked. The -v flag removes volumes with persistent data. Ask the user to confirm.',
    };
  }

  // ── 9. Infrastructure destruction ──

  // terraform destroy / terraform apply -auto-approve
  if (/terraform\s+destroy/.test(lower)) {
    return {
      decision: 'block',
      reason:
        'terraform destroy blocked. This tears down infrastructure. Ask the user to confirm and run manually.',
    };
  }

  if (/terraform\s+apply\s+.*-auto-approve/.test(lower)) {
    return {
      decision: 'block',
      reason:
        'terraform apply -auto-approve blocked. This applies changes without review. Remove -auto-approve to review the plan first.',
    };
  }

  // pulumi destroy
  if (/pulumi\s+destroy/.test(lower)) {
    return {
      decision: 'block',
      reason:
        'pulumi destroy blocked. This tears down infrastructure. Ask the user to confirm and run manually.',
    };
  }

  // ── 10. Package publishing ──
  if (
    /\bnpm\s+publish\b/.test(lower) ||
    /\byarn\s+publish\b/.test(lower) ||
    /\bgem\s+push\b/.test(lower) ||
    /\btwine\s+upload\b/.test(lower) ||
    /\bcargo\s+publish\b/.test(lower)
  ) {
    return {
      decision: 'block',
      reason:
        'Package publish blocked. Publishing is irreversible for most registries. Ask the user to confirm and run manually.',
    };
  }

  // ── 11. Cloud resource destruction ──

  // AWS destructive operations
  if (
    /\baws\s+/.test(lower) &&
    (/ec2\s+terminate-instances/.test(lower) ||
      /rds\s+delete-db-instance/.test(lower) ||
      /cloudformation\s+delete-stack/.test(lower) ||
      /secretsmanager\s+delete-secret/.test(lower) ||
      /iam\s+delete-role/.test(lower))
  ) {
    return {
      decision: 'block',
      reason:
        'Destructive AWS operation blocked. This deletes cloud resources. Ask the user to confirm and run manually.',
    };
  }

  // GCP destructive operations
  if (
    /\bgcloud\s+/.test(lower) &&
    (/compute\s+instances\s+delete/.test(lower) ||
      /sql\s+instances\s+delete/.test(lower) ||
      /projects\s+delete/.test(lower))
  ) {
    return {
      decision: 'block',
      reason:
        'Destructive GCP operation blocked. This deletes cloud resources. Ask the user to confirm and run manually.',
    };
  }

  // Azure destructive operations
  if (
    /\baz\s+/.test(lower) &&
    (/vm\s+delete/.test(lower) ||
      /group\s+delete/.test(lower) ||
      /storage\s+account\s+delete/.test(lower) ||
      /keyvault\s+delete/.test(lower))
  ) {
    return {
      decision: 'block',
      reason:
        'Destructive Azure operation blocked. This deletes cloud resources. Ask the user to confirm and run manually.',
    };
  }

  // ── 12. Kubernetes mass deletion ──
  if (/\bkubectl\s+/.test(lower)) {
    if (
      /delete\s+(namespace|ns)\b/.test(lower) ||
      /delete\s+.*--all\b/.test(lower) ||
      /drain\b/.test(lower)
    ) {
      return {
        decision: 'block',
        reason:
          'Destructive Kubernetes operation blocked. Namespace deletion, --all deletion, and drain are high-impact. Ask the user to confirm.',
      };
    }
  }

  // ── 13. Rsync with --delete ──
  if (/\brsync\b/.test(lower) && /--delete/.test(lower)) {
    return {
      decision: 'block',
      reason:
        'rsync --delete blocked. This removes files at the destination that do not exist at the source. Ask the user to confirm.',
    };
  }

  // ── 14. Cloud storage mass deletion ──

  // AWS S3 recursive delete
  if (/\baws\s+s3\s+(rm|rb)\b/.test(lower) && /--recursive/.test(lower)) {
    return {
      decision: 'block',
      reason:
        'AWS S3 recursive deletion blocked. This permanently removes cloud storage objects. Ask the user to confirm.',
    };
  }

  // GCS recursive delete
  if (/\bgsutil\s+/.test(lower) && /\brm\s+.*-r/.test(lower)) {
    return {
      decision: 'block',
      reason:
        'GCS recursive deletion blocked. This permanently removes cloud storage objects. Ask the user to confirm.',
    };
  }

  // Azure blob recursive delete
  if (/\bazcopy\s+remove\b/.test(lower) && /--recursive/.test(lower)) {
    return {
      decision: 'block',
      reason:
        'Azure blob recursive deletion blocked. This permanently removes cloud storage objects. Ask the user to confirm.',
    };
  }

  return null;
}

async function main() {
  const input = await getInput();
  const cmd = extractCommand(input);

  if (!cmd) {
    process.exit(0);
  }

  const result = checkDestructiveCommand(cmd);
  if (result) {
    console.log(JSON.stringify(result));
    process.exit(0);
  }

  process.exit(0);
}

// Allow testing when required as a module
if (require.main === module) {
  main();
}

module.exports = {
  checkDestructiveCommand,
  extractCommand,
  extractShellWrapper,
  checkInterpreterOneliner,
  DANGEROUS_RM_TARGETS,
  SAFE_RM_TARGETS,
};

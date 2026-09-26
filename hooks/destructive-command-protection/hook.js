#!/usr/bin/env node

/**
 * Destructive Command Protection Hook for Claude Code
 *
 * Intercepts Bash tool calls and blocks commands that risk irreversible
 * damage to the filesystem, a database, cloud infrastructure, or version
 * control history. See ../SKILL.md for the full pattern table.
 *
 * Hook protocol: reads tool input from stdin as JSON, outputs
 * `hookSpecificOutput.permissionDecision` JSON to stdout (allow/ask/deny).
 * Every match here is a hard `deny` — this hook never runs a destructive
 * command with hidden safety flags, and never falls back to `ask` for
 * patterns on the blocked list.
 *
 * Fails open on any error reading stdin — this hook should never be the
 * reason a command is blocked when there's no real signal behind it.
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
  return (input.tool_input?.command || input.input?.command || '').trim();
}

const DANGEROUS_RM_TARGETS = new Set(['/', '~', '.', '/etc', '/usr', '/var', '/boot', '/home', '$HOME']);
const DANGEROUS_RM_TRAVERSAL = /^(\.\.\/)*\.\.$/;

function checkFilesystem(cmd) {
  const rmMatch = cmd.match(/\brm\s+((?:-\S+\s+)*)((?:\S+\s*)+)/);
  if (!rmMatch || !/\brm\s+-\S*[rR]\S*[fF]\S*\b|\brm\s+-\S*[fF]\S*[rR]\S*\b/.test(cmd)) return null;
  const targets = rmMatch[2].trim().split(/\s+/).map((t) => (t.length > 1 ? t.replace(/\/+$/, '') : t));
  for (const target of targets) {
    const expanded = target === '$HOME' ? '$HOME' : target;
    if (DANGEROUS_RM_TARGETS.has(expanded) || DANGEROUS_RM_TRAVERSAL.test(target)) {
      return { reason: `Destructive command protection: "rm -rf ${target}" targets a critical path and is blocked.` };
    }
  }
  return null;
}

function checkDatabase(cmd) {
  if (/\bdrop\s+(database|schema)\b/i.test(cmd)) {
    return { reason: 'Destructive command protection: DROP DATABASE/SCHEMA destroys data irreversibly and is blocked.' };
  }
  if (/\btruncate\s+table\b/i.test(cmd) && !/\bif\s+exists\b/i.test(cmd)) {
    return { reason: 'Destructive command protection: TRUNCATE TABLE without IF EXISTS is blocked.' };
  }
  if (/\bredis-cli\s+.*\b(flushall|flushdb)\b/i.test(cmd)) {
    return { reason: 'Destructive command protection: Redis FLUSHALL/FLUSHDB wipes all data and is blocked.' };
  }
  if (/\bdropdatabase\s*\(\s*\)|(?:\bdb\.\w+\.)?\bdrop\s*\(\s*\)/i.test(cmd) && /mongo/i.test(cmd)) {
    return { reason: 'Destructive command protection: MongoDB dropDatabase()/drop() is blocked.' };
  }
  return null;
}

function checkGit(cmd) {
  if (/\bgit\s+stash\s+(drop|clear)\b/.test(cmd)) {
    return { reason: 'Destructive command protection: "git stash drop/clear" permanently deletes stash entries and is blocked.' };
  }
  return null;
}

function checkSystem(cmd) {
  if (/\bmkfs\b/.test(cmd)) {
    return { reason: 'Destructive command protection: mkfs formats a disk and is blocked.' };
  }
  if (/\bdd\b[^|]*\bof=\/dev\//.test(cmd)) {
    return { reason: 'Destructive command protection: "dd" writing directly to a block device is blocked.' };
  }
  if (/[>]{1,2}\s*\/dev\/(sd[a-z]|nvme\d+n\d+|hd[a-z])\b/.test(cmd)) {
    return { reason: 'Destructive command protection: writing directly to a block device is blocked.' };
  }
  if (/\bchmod\s+(-R\s+)?777\s+(\/|\/etc|\/usr|\/var|\/boot|\/home)(\/|\s|$)/.test(cmd)) {
    return { reason: 'Destructive command protection: chmod 777 on a system path degrades system security and is blocked.' };
  }
  if (/:\(\)\s*\{\s*:\|:&?\s*\};?\s*:/.test(cmd)) {
    return { reason: 'Destructive command protection: fork bomb pattern detected and blocked.' };
  }
  if (/\bkill\s+(-\d+\s+)?-?1\b/.test(cmd)) {
    return { reason: 'Destructive command protection: "kill 1"/"kill -1" targets init or all processes and can crash the system, and is blocked.' };
  }
  return null;
}

function checkContainers(cmd) {
  if (/\bdocker\s+system\s+prune\b/.test(cmd)) {
    return { reason: 'Destructive command protection: "docker system prune" removes all unused containers/images/volumes and is blocked.' };
  }
  if (/\bdocker\s+volume\s+prune\b/.test(cmd)) {
    return { reason: 'Destructive command protection: "docker volume prune" removes all unused volumes and their data, and is blocked.' };
  }
  if (/\bdocker\s+(container|image)\s+prune\b/.test(cmd)) {
    return { reason: 'Destructive command protection: mass docker container/image removal is blocked.' };
  }
  if (/\bdocker(?:-compose|\s+compose)\s+down\b.*(-v\b|--volumes\b)/.test(cmd)) {
    return { reason: 'Destructive command protection: "docker compose down -v" removes volumes with persistent data and is blocked.' };
  }
  return null;
}

function checkIac(cmd) {
  if (/\bterraform\s+destroy\b/.test(cmd)) {
    return { reason: 'Destructive command protection: "terraform destroy" tears down infrastructure and is blocked.' };
  }
  if (/\bterraform\s+apply\b.*-auto-approve\b/.test(cmd)) {
    return { reason: 'Destructive command protection: "terraform apply -auto-approve" applies without review and is blocked.' };
  }
  if (/\bpulumi\s+destroy\b/.test(cmd)) {
    return { reason: 'Destructive command protection: "pulumi destroy" tears down infrastructure and is blocked.' };
  }
  return null;
}

function checkPublishing(cmd) {
  if (/\b(npm|yarn|pnpm)\s+publish\b/.test(cmd)) {
    return { reason: 'Destructive command protection: package publish is an irreversible public release and is blocked.' };
  }
  if (/\bgem\s+push\b/.test(cmd) || /\btwine\s+upload\b/.test(cmd) || /\bcargo\s+publish\b/.test(cmd)) {
    return { reason: 'Destructive command protection: package publish is an irreversible public release and is blocked.' };
  }
  return null;
}

function checkCloud(cmd) {
  const patterns = [
    /\baws\s+ec2\s+terminate-instances\b/,
    /\baws\s+rds\s+delete-db-instance\b/,
    /\baws\s+cloudformation\s+delete-stack\b/,
    /\baws\s+secretsmanager\s+delete-secret\b/,
    /\baws\s+iam\s+delete-role\b/,
    /\bgcloud\s+compute\s+instances\s+delete\b/,
    /\bgcloud\s+sql\s+instances\s+delete\b/,
    /\bgcloud\s+projects\s+delete\b/,
    /\baz\s+vm\s+delete\b/,
    /\baz\s+group\s+delete\b/,
    /\baz\s+storage\s+account\s+delete\b/,
    /\baz\s+keyvault\s+delete\b/,
  ];
  if (patterns.some((re) => re.test(cmd))) {
    return { reason: 'Destructive command protection: this command destroys a cloud resource and is blocked.' };
  }
  return null;
}

function checkKubernetes(cmd) {
  if (/\bkubectl\s+delete\s+(namespace|ns)\b/.test(cmd)) {
    return { reason: 'Destructive command protection: "kubectl delete namespace" mass-deletes resources and is blocked.' };
  }
  if (/\bkubectl\s+delete\b.*--all\b/.test(cmd)) {
    return { reason: 'Destructive command protection: "kubectl delete ... --all" mass-deletes resources and is blocked.' };
  }
  if (/\bkubectl\s+drain\b/.test(cmd)) {
    return { reason: 'Destructive command protection: "kubectl drain" evicts all pods from a node and is blocked.' };
  }
  return null;
}

function checkNetworkStorage(cmd) {
  if (/\brsync\b.*--delete\b/.test(cmd)) {
    return { reason: 'Destructive command protection: "rsync --delete" removes destination files not in source and is blocked.' };
  }
  if (/\baws\s+s3\s+(rm|rb)\b.*--recursive\b/.test(cmd)) {
    return { reason: 'Destructive command protection: mass S3 deletion is blocked.' };
  }
  if (/\bgsutil\s+rm\s+-r\b/.test(cmd)) {
    return { reason: 'Destructive command protection: mass GCS deletion is blocked.' };
  }
  if (/\bazcopy\s+remove\b.*--recursive\b/.test(cmd)) {
    return { reason: 'Destructive command protection: mass Azure blob deletion is blocked.' };
  }
  return null;
}

const DIRECT_CHECKS = [
  checkFilesystem,
  checkDatabase,
  checkGit,
  checkSystem,
  checkContainers,
  checkIac,
  checkPublishing,
  checkCloud,
  checkKubernetes,
  checkNetworkStorage,
];

function checkDirect(cmd) {
  for (const check of DIRECT_CHECKS) {
    const result = check(cmd);
    if (result) return result;
  }
  return null;
}

function checkInterpreterOneLiner(inner) {
  if (/shutil\.rmtree\s*\(/.test(inner)) {
    return { reason: 'Destructive command protection: interpreter one-liner calling shutil.rmtree is blocked.' };
  }
  if (/\bos\.system\s*\(/.test(inner) && /\brm\s+-rf\b/.test(inner)) {
    return { reason: 'Destructive command protection: interpreter one-liner shelling out to "rm -rf" is blocked.' };
  }
  if (/\bsubprocess\.(run|call|check_call|check_output|Popen)\s*\(/.test(inner) && /\brm\s+-rf\b|\bdrop\s+(database|schema)\b/i.test(inner)) {
    return { reason: 'Destructive command protection: interpreter one-liner shelling out via subprocess to a destructive command is blocked.' };
  }
  if (/\bexecSync\s*\(/.test(inner) || /\bchild_process\b/.test(inner)) {
    if (/\brm\s+-rf\b|\bdrop\s+(database|schema)\b/i.test(inner)) {
      return { reason: 'Destructive command protection: interpreter one-liner shelling out to a destructive command is blocked.' };
    }
  }
  if (/\bfs\.rmSync\s*\(/.test(inner) && /\brecursive\s*:\s*true/.test(inner)) {
    return { reason: 'Destructive command protection: interpreter one-liner calling fs.rmSync recursively is blocked.' };
  }
  if (/\bFileUtils\.rm_rf\s*\(/.test(inner)) {
    return { reason: 'Destructive command protection: interpreter one-liner calling FileUtils.rm_rf is blocked.' };
  }
  if (/\bsystem\s*\(/.test(inner) && /\brm\s+-rf\b/.test(inner)) {
    return { reason: 'Destructive command protection: interpreter one-liner shelling out to "rm -rf" is blocked.' };
  }
  return null;
}

function checkBypass(cmd) {
  const shellMatch = cmd.match(/\b(?:bash|sh)\s+-c\s+(['"])([\s\S]*)\1/);
  if (shellMatch) {
    const inner = shellMatch[2];
    const innerResult = checkDirect(inner) || checkBypass(inner);
    if (innerResult) {
      return { reason: `Destructive command protection: shell-wrapper bypass detected — ${innerResult.reason}` };
    }
  }

  const interpMatch = cmd.match(/\b(?:python3?|node|ruby)\s+(?:-c|-e|--eval)\s+(['"])([\s\S]*)\1/);
  if (interpMatch) {
    const inner = interpMatch[2];
    const innerResult = checkInterpreterOneLiner(inner);
    if (innerResult) {
      return { reason: `Destructive command protection: interpreter-wrapper bypass detected — ${innerResult.reason}` };
    }
  }

  return null;
}

function decide(cmd) {
  if (!cmd) return null;
  return checkDirect(cmd) || checkBypass(cmd);
}

async function main() {
  const input = await getInput();
  const cmd = extractCommand(input);
  const result = decide(cmd);

  if (result) {
    console.log(JSON.stringify({
      hookSpecificOutput: {
        hookEventName: 'PreToolUse',
        permissionDecision: 'deny',
        permissionDecisionReason: result.reason,
      },
    }));
  }
  process.exit(0);
}

if (require.main === module) {
  main();
}

module.exports = {
  decide,
  checkFilesystem,
  checkDatabase,
  checkGit,
  checkSystem,
  checkContainers,
  checkIac,
  checkPublishing,
  checkCloud,
  checkKubernetes,
  checkNetworkStorage,
  checkBypass,
};

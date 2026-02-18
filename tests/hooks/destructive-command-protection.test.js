const { describe, it } = require('node:test');
const assert = require('node:assert/strict');

const {
  checkDestructiveCommand,
  extractCommand,
  extractShellWrapper,
  checkInterpreterOneliner,
} = require('../../skills/destructive-command-protection/references/hook.js');

// ── extractCommand ──

describe('extractCommand', () => {
  it('extracts from tool_input.command', () => {
    const result = extractCommand({ tool_input: { command: 'rm -rf /' } });
    assert.equal(result, 'rm -rf /');
  });

  it('extracts from input.command fallback', () => {
    const result = extractCommand({ input: { command: 'rm -rf /' } });
    assert.equal(result, 'rm -rf /');
  });

  it('returns empty string for null input', () => {
    assert.equal(extractCommand(null), '');
  });

  it('preserves original casing', () => {
    const result = extractCommand({ tool_input: { command: 'DROP DATABASE Prod' } });
    assert.equal(result, 'DROP DATABASE Prod');
  });
});

// ── extractShellWrapper ──

describe('extractShellWrapper', () => {
  it('extracts inner command from bash -c "..."', () => {
    assert.equal(extractShellWrapper('bash -c "rm -rf /"'), 'rm -rf /');
  });

  it('extracts inner command from sh -c \'...\'', () => {
    assert.equal(extractShellWrapper("sh -c 'git stash clear'"), 'git stash clear');
  });

  it('returns null for non-wrapper commands', () => {
    assert.equal(extractShellWrapper('git status'), null);
  });
});

// ── 1. Filesystem destruction: rm -rf ──

describe('checkDestructiveCommand — rm -rf dangerous targets', () => {
  it('blocks rm -rf /', () => {
    const result = checkDestructiveCommand('rm -rf /');
    assert.notEqual(result, null);
    assert.equal(result.decision, 'block');
  });

  it('blocks rm -rf ~/', () => {
    const result = checkDestructiveCommand('rm -rf ~/');
    assert.notEqual(result, null);
    assert.equal(result.decision, 'block');
  });

  it('blocks rm -rf $HOME', () => {
    const result = checkDestructiveCommand('rm -rf $HOME');
    assert.notEqual(result, null);
    assert.equal(result.decision, 'block');
  });

  it('blocks rm -rf /etc', () => {
    const result = checkDestructiveCommand('rm -rf /etc');
    assert.notEqual(result, null);
    assert.equal(result.decision, 'block');
  });

  it('blocks rm -rf /usr', () => {
    const result = checkDestructiveCommand('rm -rf /usr');
    assert.notEqual(result, null);
    assert.equal(result.decision, 'block');
  });

  it('blocks rm -rf /var', () => {
    const result = checkDestructiveCommand('rm -rf /var');
    assert.notEqual(result, null);
    assert.equal(result.decision, 'block');
  });

  it('blocks rm -rf /boot', () => {
    const result = checkDestructiveCommand('rm -rf /boot');
    assert.notEqual(result, null);
    assert.equal(result.decision, 'block');
  });

  it('blocks rm -rf /home', () => {
    const result = checkDestructiveCommand('rm -rf /home');
    assert.notEqual(result, null);
    assert.equal(result.decision, 'block');
  });

  it('blocks rm -rf .', () => {
    const result = checkDestructiveCommand('rm -rf .');
    assert.notEqual(result, null);
    assert.equal(result.decision, 'block');
  });

  it('blocks rm -rf ../../', () => {
    const result = checkDestructiveCommand('rm -rf ../../');
    assert.notEqual(result, null);
    assert.equal(result.decision, 'block');
  });

  it('blocks rm -fr / (flag order reversed)', () => {
    const result = checkDestructiveCommand('rm -fr /');
    assert.notEqual(result, null);
    assert.equal(result.decision, 'block');
  });
});

describe('checkDestructiveCommand — rm -rf safe targets', () => {
  it('allows rm -rf node_modules', () => {
    assert.equal(checkDestructiveCommand('rm -rf node_modules'), null);
  });

  it('allows rm -rf ./node_modules', () => {
    assert.equal(checkDestructiveCommand('rm -rf ./node_modules'), null);
  });

  it('allows rm -rf dist/', () => {
    assert.equal(checkDestructiveCommand('rm -rf dist/'), null);
  });

  it('allows rm -rf .next', () => {
    assert.equal(checkDestructiveCommand('rm -rf .next'), null);
  });

  it('allows rm -rf coverage', () => {
    assert.equal(checkDestructiveCommand('rm -rf coverage'), null);
  });

  it('allows rm -rf build/', () => {
    assert.equal(checkDestructiveCommand('rm -rf build/'), null);
  });

  it('allows rm -rf .cache/', () => {
    assert.equal(checkDestructiveCommand('rm -rf .cache/'), null);
  });
});

describe('checkDestructiveCommand — rm -rf unknown targets', () => {
  it('allows rm -rf on unknown paths (documents current behavior)', () => {
    assert.equal(checkDestructiveCommand('rm -rf /some/random/path'), null);
  });
});

// ── 2. Database destruction ──

describe('checkDestructiveCommand — database operations', () => {
  it('blocks DROP DATABASE production', () => {
    const result = checkDestructiveCommand('DROP DATABASE production');
    assert.notEqual(result, null);
    assert.equal(result.decision, 'block');
  });

  it('blocks DROP SCHEMA myschema', () => {
    const result = checkDestructiveCommand('DROP SCHEMA myschema');
    assert.notEqual(result, null);
    assert.equal(result.decision, 'block');
  });

  it('blocks drop database (case insensitive)', () => {
    const result = checkDestructiveCommand('drop database test_db');
    assert.notEqual(result, null);
    assert.equal(result.decision, 'block');
  });

  it('allows DROP TABLE (regex only matches DATABASE/SCHEMA)', () => {
    assert.equal(checkDestructiveCommand('DROP TABLE IF EXISTS temp_migration'), null);
  });
});

describe('checkDestructiveCommand — TRUNCATE TABLE', () => {
  it('blocks TRUNCATE TABLE users', () => {
    const result = checkDestructiveCommand('TRUNCATE TABLE users');
    assert.notEqual(result, null);
    assert.equal(result.decision, 'block');
  });

  it('allows TRUNCATE TABLE IF EXISTS (escape clause)', () => {
    assert.equal(checkDestructiveCommand('TRUNCATE TABLE IF EXISTS something'), null);
  });
});

describe('checkDestructiveCommand — Redis flush', () => {
  it('blocks redis-cli FLUSHALL', () => {
    const result = checkDestructiveCommand('redis-cli FLUSHALL');
    assert.notEqual(result, null);
    assert.equal(result.decision, 'block');
  });

  it('blocks redis-cli FLUSHDB', () => {
    const result = checkDestructiveCommand('redis-cli FLUSHDB');
    assert.notEqual(result, null);
    assert.equal(result.decision, 'block');
  });

  it('blocks redis-cli -h host FLUSHALL', () => {
    const result = checkDestructiveCommand('redis-cli -h redis.example.com FLUSHALL');
    assert.notEqual(result, null);
    assert.equal(result.decision, 'block');
  });

  it('allows redis-cli GET key', () => {
    assert.equal(checkDestructiveCommand('redis-cli GET mykey'), null);
  });
});

describe('checkDestructiveCommand — MongoDB destruction', () => {
  it('blocks mongosh with dropDatabase()', () => {
    const result = checkDestructiveCommand('mongosh --eval "db.dropDatabase()"');
    assert.notEqual(result, null);
    assert.equal(result.decision, 'block');
  });

  it('blocks mongo with .drop()', () => {
    const result = checkDestructiveCommand('mongo mydb --eval "db.users.drop()"');
    assert.notEqual(result, null);
    assert.equal(result.decision, 'block');
  });

  it('allows mongosh with find()', () => {
    assert.equal(checkDestructiveCommand('mongosh --eval "db.users.find()"'), null);
  });
});

// ── 3. Disk operations ──

describe('checkDestructiveCommand — disk operations', () => {
  it('blocks mkfs.ext4 /dev/sdb', () => {
    const result = checkDestructiveCommand('mkfs.ext4 /dev/sdb');
    assert.notEqual(result, null);
    assert.equal(result.decision, 'block');
  });

  it('blocks dd if=/dev/zero of=/dev/sda', () => {
    const result = checkDestructiveCommand('dd if=/dev/zero of=/dev/sda');
    assert.notEqual(result, null);
    assert.equal(result.decision, 'block');
  });

  it('blocks > /dev/sda', () => {
    const result = checkDestructiveCommand('> /dev/sda');
    assert.notEqual(result, null);
    assert.equal(result.decision, 'block');
  });

  it('blocks > /dev/hda', () => {
    const result = checkDestructiveCommand('> /dev/hda');
    assert.notEqual(result, null);
    assert.equal(result.decision, 'block');
  });
});

// ── 4. System abuse ──

describe('checkDestructiveCommand — chmod', () => {
  it('blocks chmod -R 777 /', () => {
    const result = checkDestructiveCommand('chmod -R 777 /');
    assert.notEqual(result, null);
    assert.equal(result.decision, 'block');
  });

  it('blocks chmod 777 /etc', () => {
    const result = checkDestructiveCommand('chmod 777 /etc');
    assert.notEqual(result, null);
    assert.equal(result.decision, 'block');
  });

  it('allows chmod 777 on non-root paths (e.g., ./tmp)', () => {
    assert.equal(checkDestructiveCommand('chmod 777 ./tmp'), null);
  });
});

describe('checkDestructiveCommand — fork bomb', () => {
  it('blocks :(){ :|:& };:', () => {
    const result = checkDestructiveCommand(':(){ :|:& };:');
    assert.notEqual(result, null);
    assert.equal(result.decision, 'block');
  });
});

describe('checkDestructiveCommand — kill', () => {
  it('blocks kill 1', () => {
    const result = checkDestructiveCommand('kill 1');
    assert.notEqual(result, null);
    assert.equal(result.decision, 'block');
  });

  it('blocks kill -9 1', () => {
    const result = checkDestructiveCommand('kill -9 1');
    assert.notEqual(result, null);
    assert.equal(result.decision, 'block');
  });

  it('blocks kill -1 (all processes)', () => {
    const result = checkDestructiveCommand('kill -1');
    assert.notEqual(result, null);
    assert.equal(result.decision, 'block');
  });

  it('blocks kill -9 -1', () => {
    const result = checkDestructiveCommand('kill -9 -1');
    assert.notEqual(result, null);
    assert.equal(result.decision, 'block');
  });

  it('allows kill with a specific PID', () => {
    assert.equal(checkDestructiveCommand('kill 12345'), null);
    assert.equal(checkDestructiveCommand('kill -9 12345'), null);
  });
});

// ── 5. Git data destruction ──

describe('checkDestructiveCommand — git stash destruction', () => {
  it('blocks git stash drop', () => {
    const result = checkDestructiveCommand('git stash drop');
    assert.notEqual(result, null);
    assert.equal(result.decision, 'block');
  });

  it('blocks git stash drop stash@{0}', () => {
    const result = checkDestructiveCommand('git stash drop stash@{0}');
    assert.notEqual(result, null);
    assert.equal(result.decision, 'block');
  });

  it('blocks git stash clear', () => {
    const result = checkDestructiveCommand('git stash clear');
    assert.notEqual(result, null);
    assert.equal(result.decision, 'block');
  });

  it('allows git stash (save)', () => {
    assert.equal(checkDestructiveCommand('git stash'), null);
  });

  it('allows git stash pop', () => {
    assert.equal(checkDestructiveCommand('git stash pop'), null);
  });

  it('allows git stash list', () => {
    assert.equal(checkDestructiveCommand('git stash list'), null);
  });

  it('allows git stash show', () => {
    assert.equal(checkDestructiveCommand('git stash show'), null);
  });
});

// ── 6. Shell wrapper bypass ──

describe('checkDestructiveCommand — shell wrapper bypass', () => {
  it('blocks bash -c "rm -rf /"', () => {
    const result = checkDestructiveCommand('bash -c "rm -rf /"');
    assert.notEqual(result, null);
    assert.equal(result.decision, 'block');
    assert.ok(result.reason.includes('Shell wrapper'));
  });

  it('blocks sh -c "git stash clear"', () => {
    const result = checkDestructiveCommand('sh -c "git stash clear"');
    assert.notEqual(result, null);
    assert.equal(result.decision, 'block');
  });

  it('blocks bash -c "DROP DATABASE prod"', () => {
    const result = checkDestructiveCommand('bash -c "DROP DATABASE prod"');
    assert.notEqual(result, null);
    assert.equal(result.decision, 'block');
  });

  it('allows bash -c "echo hello"', () => {
    assert.equal(checkDestructiveCommand('bash -c "echo hello"'), null);
  });

  it('allows sh -c "ls -la"', () => {
    assert.equal(checkDestructiveCommand('sh -c "ls -la"'), null);
  });

  it('blocks nested shell wrappers (bash -c wrapping sh -c)', () => {
    // bash -c "sh -c 'rm -rf /'" — outer extracts inner, inner extracts rm -rf /
    const result = checkDestructiveCommand("bash -c \"sh -c 'rm -rf /'\"");
    assert.notEqual(result, null);
    assert.equal(result.decision, 'block');
  });
});

// ── 7. Interpreter one-liners ──

describe('checkDestructiveCommand — Python one-liners', () => {
  it('blocks python -c with os.system()', () => {
    const result = checkDestructiveCommand('python -c "import os; os.system(\'rm -rf /\')"');
    assert.notEqual(result, null);
    assert.equal(result.decision, 'block');
  });

  it('blocks python3 -c with shutil.rmtree', () => {
    const result = checkDestructiveCommand('python3 -c "import shutil; shutil.rmtree(\'/tmp/data\')"');
    assert.notEqual(result, null);
    assert.equal(result.decision, 'block');
  });

  it('blocks python -c with subprocess.run', () => {
    const result = checkDestructiveCommand('python -c "import subprocess; subprocess.run([\'rm\', \'-rf\', \'/\'])"');
    assert.notEqual(result, null);
    assert.equal(result.decision, 'block');
  });

  it('allows python -c with print()', () => {
    assert.equal(checkDestructiveCommand('python -c "print(\'hello\')"'), null);
  });
});

describe('checkDestructiveCommand — Node.js one-liners', () => {
  it('blocks node -e with execSync', () => {
    const result = checkDestructiveCommand('node -e "require(\'child_process\').execSync(\'rm -rf /\')"');
    assert.notEqual(result, null);
    assert.equal(result.decision, 'block');
  });

  it('blocks node --eval with rmSync', () => {
    const result = checkDestructiveCommand('node --eval "require(\'fs\').rmSync(\'/tmp\', {recursive: true})"');
    assert.notEqual(result, null);
    assert.equal(result.decision, 'block');
  });

  it('allows node -e with console.log', () => {
    assert.equal(checkDestructiveCommand('node -e "console.log(\'hello\')"'), null);
  });
});

describe('checkDestructiveCommand — Ruby one-liners', () => {
  it('blocks ruby -e with FileUtils.rm_rf', () => {
    const result = checkDestructiveCommand('ruby -e "require \'fileutils\'; FileUtils.rm_rf(\'/tmp\')"');
    assert.notEqual(result, null);
    assert.equal(result.decision, 'block');
  });

  it('blocks ruby -e with system()', () => {
    const result = checkDestructiveCommand('ruby -e "system(\'rm -rf /\')"');
    assert.notEqual(result, null);
    assert.equal(result.decision, 'block');
  });

  it('allows ruby -e with puts', () => {
    assert.equal(checkDestructiveCommand('ruby -e "puts \'hello\'"'), null);
  });
});

// ── 8. Container destruction ──

describe('checkDestructiveCommand — Docker destruction', () => {
  it('blocks docker system prune', () => {
    const result = checkDestructiveCommand('docker system prune');
    assert.notEqual(result, null);
    assert.equal(result.decision, 'block');
  });

  it('blocks docker system prune -a --volumes', () => {
    const result = checkDestructiveCommand('docker system prune -a --volumes');
    assert.notEqual(result, null);
    assert.equal(result.decision, 'block');
  });

  it('blocks docker volume prune', () => {
    const result = checkDestructiveCommand('docker volume prune');
    assert.notEqual(result, null);
    assert.equal(result.decision, 'block');
  });

  it('blocks docker container prune', () => {
    const result = checkDestructiveCommand('docker container prune');
    assert.notEqual(result, null);
    assert.equal(result.decision, 'block');
  });

  it('blocks docker image prune', () => {
    const result = checkDestructiveCommand('docker image prune');
    assert.notEqual(result, null);
    assert.equal(result.decision, 'block');
  });

  it('blocks docker compose down -v', () => {
    const result = checkDestructiveCommand('docker compose down -v');
    assert.notEqual(result, null);
    assert.equal(result.decision, 'block');
  });

  it('blocks docker-compose down -v', () => {
    const result = checkDestructiveCommand('docker-compose down -v');
    assert.notEqual(result, null);
    assert.equal(result.decision, 'block');
  });

  it('allows docker compose down (without -v)', () => {
    assert.equal(checkDestructiveCommand('docker compose down'), null);
  });

  it('allows docker ps', () => {
    assert.equal(checkDestructiveCommand('docker ps'), null);
  });

  it('allows docker build', () => {
    assert.equal(checkDestructiveCommand('docker build .'), null);
  });
});

// ── 9. Infrastructure destruction ──

describe('checkDestructiveCommand — Infrastructure destruction', () => {
  it('blocks terraform destroy', () => {
    const result = checkDestructiveCommand('terraform destroy');
    assert.notEqual(result, null);
    assert.equal(result.decision, 'block');
  });

  it('blocks terraform destroy -auto-approve', () => {
    const result = checkDestructiveCommand('terraform destroy -auto-approve');
    assert.notEqual(result, null);
    assert.equal(result.decision, 'block');
  });

  it('blocks terraform apply -auto-approve', () => {
    const result = checkDestructiveCommand('terraform apply -auto-approve');
    assert.notEqual(result, null);
    assert.equal(result.decision, 'block');
  });

  it('allows terraform plan', () => {
    assert.equal(checkDestructiveCommand('terraform plan'), null);
  });

  it('allows terraform apply (without -auto-approve)', () => {
    assert.equal(checkDestructiveCommand('terraform apply'), null);
  });

  it('blocks pulumi destroy', () => {
    const result = checkDestructiveCommand('pulumi destroy');
    assert.notEqual(result, null);
    assert.equal(result.decision, 'block');
  });

  it('allows pulumi up', () => {
    assert.equal(checkDestructiveCommand('pulumi up'), null);
  });
});

// ── 10. Package publishing ──

describe('checkDestructiveCommand — package publishing', () => {
  it('blocks npm publish', () => {
    const result = checkDestructiveCommand('npm publish');
    assert.notEqual(result, null);
    assert.equal(result.decision, 'block');
  });

  it('blocks npm publish --access public', () => {
    const result = checkDestructiveCommand('npm publish --access public');
    assert.notEqual(result, null);
    assert.equal(result.decision, 'block');
  });

  it('blocks yarn publish', () => {
    const result = checkDestructiveCommand('yarn publish');
    assert.notEqual(result, null);
    assert.equal(result.decision, 'block');
  });

  it('blocks gem push', () => {
    const result = checkDestructiveCommand('gem push my-gem-1.0.0.gem');
    assert.notEqual(result, null);
    assert.equal(result.decision, 'block');
  });

  it('blocks twine upload', () => {
    const result = checkDestructiveCommand('twine upload dist/*');
    assert.notEqual(result, null);
    assert.equal(result.decision, 'block');
  });

  it('blocks cargo publish', () => {
    const result = checkDestructiveCommand('cargo publish');
    assert.notEqual(result, null);
    assert.equal(result.decision, 'block');
  });

  it('allows npm install', () => {
    assert.equal(checkDestructiveCommand('npm install'), null);
  });

  it('allows npm test', () => {
    assert.equal(checkDestructiveCommand('npm test'), null);
  });
});

// ── 11. Cloud resource destruction ──

describe('checkDestructiveCommand — AWS destruction', () => {
  it('blocks aws ec2 terminate-instances', () => {
    const result = checkDestructiveCommand('aws ec2 terminate-instances --instance-ids i-123');
    assert.notEqual(result, null);
    assert.equal(result.decision, 'block');
  });

  it('blocks aws rds delete-db-instance', () => {
    const result = checkDestructiveCommand('aws rds delete-db-instance --db-instance-identifier mydb');
    assert.notEqual(result, null);
    assert.equal(result.decision, 'block');
  });

  it('blocks aws cloudformation delete-stack', () => {
    const result = checkDestructiveCommand('aws cloudformation delete-stack --stack-name mystack');
    assert.notEqual(result, null);
    assert.equal(result.decision, 'block');
  });

  it('blocks aws secretsmanager delete-secret', () => {
    const result = checkDestructiveCommand('aws secretsmanager delete-secret --secret-id mysecret');
    assert.notEqual(result, null);
    assert.equal(result.decision, 'block');
  });

  it('blocks aws iam delete-role', () => {
    const result = checkDestructiveCommand('aws iam delete-role --role-name myrole');
    assert.notEqual(result, null);
    assert.equal(result.decision, 'block');
  });

  it('allows aws s3 ls', () => {
    assert.equal(checkDestructiveCommand('aws s3 ls'), null);
  });

  it('allows aws ec2 describe-instances', () => {
    assert.equal(checkDestructiveCommand('aws ec2 describe-instances'), null);
  });
});

describe('checkDestructiveCommand — GCP destruction', () => {
  it('blocks gcloud compute instances delete', () => {
    const result = checkDestructiveCommand('gcloud compute instances delete my-vm');
    assert.notEqual(result, null);
    assert.equal(result.decision, 'block');
  });

  it('blocks gcloud sql instances delete', () => {
    const result = checkDestructiveCommand('gcloud sql instances delete mydb');
    assert.notEqual(result, null);
    assert.equal(result.decision, 'block');
  });

  it('blocks gcloud projects delete', () => {
    const result = checkDestructiveCommand('gcloud projects delete my-project');
    assert.notEqual(result, null);
    assert.equal(result.decision, 'block');
  });

  it('allows gcloud compute instances list', () => {
    assert.equal(checkDestructiveCommand('gcloud compute instances list'), null);
  });
});

describe('checkDestructiveCommand — Azure destruction', () => {
  it('blocks az vm delete', () => {
    const result = checkDestructiveCommand('az vm delete --name myvm --resource-group myrg');
    assert.notEqual(result, null);
    assert.equal(result.decision, 'block');
  });

  it('blocks az group delete', () => {
    const result = checkDestructiveCommand('az group delete --name myrg');
    assert.notEqual(result, null);
    assert.equal(result.decision, 'block');
  });

  it('blocks az storage account delete', () => {
    const result = checkDestructiveCommand('az storage account delete --name mystorage');
    assert.notEqual(result, null);
    assert.equal(result.decision, 'block');
  });

  it('blocks az keyvault delete', () => {
    const result = checkDestructiveCommand('az keyvault delete --name myvault');
    assert.notEqual(result, null);
    assert.equal(result.decision, 'block');
  });

  it('allows az vm list', () => {
    assert.equal(checkDestructiveCommand('az vm list'), null);
  });
});

// ── 12. Kubernetes mass deletion ──

describe('checkDestructiveCommand — Kubernetes destruction', () => {
  it('blocks kubectl delete namespace', () => {
    const result = checkDestructiveCommand('kubectl delete namespace production');
    assert.notEqual(result, null);
    assert.equal(result.decision, 'block');
  });

  it('blocks kubectl delete ns', () => {
    const result = checkDestructiveCommand('kubectl delete ns staging');
    assert.notEqual(result, null);
    assert.equal(result.decision, 'block');
  });

  it('blocks kubectl delete pods --all', () => {
    const result = checkDestructiveCommand('kubectl delete pods --all');
    assert.notEqual(result, null);
    assert.equal(result.decision, 'block');
  });

  it('blocks kubectl drain', () => {
    const result = checkDestructiveCommand('kubectl drain node-1');
    assert.notEqual(result, null);
    assert.equal(result.decision, 'block');
  });

  it('allows kubectl get pods', () => {
    assert.equal(checkDestructiveCommand('kubectl get pods'), null);
  });

  it('allows kubectl delete pod specific-pod', () => {
    assert.equal(checkDestructiveCommand('kubectl delete pod my-pod'), null);
  });
});

// ── 13. Rsync --delete ──

describe('checkDestructiveCommand — rsync --delete', () => {
  it('blocks rsync --delete', () => {
    const result = checkDestructiveCommand('rsync -avz --delete src/ dest/');
    assert.notEqual(result, null);
    assert.equal(result.decision, 'block');
  });

  it('blocks rsync with --delete-before', () => {
    // --delete-before contains --delete
    const result = checkDestructiveCommand('rsync --delete-before src/ dest/');
    assert.notEqual(result, null);
    assert.equal(result.decision, 'block');
  });

  it('allows rsync without --delete', () => {
    assert.equal(checkDestructiveCommand('rsync -avz src/ dest/'), null);
  });
});

// ── 14. Cloud storage mass deletion ──

describe('checkDestructiveCommand — cloud storage deletion', () => {
  it('blocks aws s3 rm --recursive', () => {
    const result = checkDestructiveCommand('aws s3 rm s3://my-bucket --recursive');
    assert.notEqual(result, null);
    assert.equal(result.decision, 'block');
  });

  it('blocks aws s3 rb --recursive (remove bucket)', () => {
    const result = checkDestructiveCommand('aws s3 rb s3://my-bucket --recursive');
    assert.notEqual(result, null);
    assert.equal(result.decision, 'block');
  });

  it('blocks gsutil rm -r', () => {
    const result = checkDestructiveCommand('gsutil rm -r gs://my-bucket');
    assert.notEqual(result, null);
    assert.equal(result.decision, 'block');
  });

  it('blocks azcopy remove --recursive', () => {
    const result = checkDestructiveCommand('azcopy remove "https://account.blob.core.windows.net/container" --recursive');
    assert.notEqual(result, null);
    assert.equal(result.decision, 'block');
  });

  it('allows aws s3 ls', () => {
    assert.equal(checkDestructiveCommand('aws s3 ls s3://my-bucket'), null);
  });

  it('allows aws s3 cp (non-recursive single file)', () => {
    assert.equal(checkDestructiveCommand('aws s3 cp file.txt s3://my-bucket/'), null);
  });
});

// ── Edge cases ──

describe('checkDestructiveCommand — edge cases', () => {
  it('returns null for empty command', () => {
    assert.equal(checkDestructiveCommand(''), null);
  });

  it('returns null for safe commands', () => {
    assert.equal(checkDestructiveCommand('npm test'), null);
    assert.equal(checkDestructiveCommand('ls -la'), null);
    assert.equal(checkDestructiveCommand('git status'), null);
  });
});

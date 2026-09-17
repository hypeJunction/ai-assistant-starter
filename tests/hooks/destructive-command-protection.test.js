const { describe, it } = require('node:test');
const assert = require('node:assert/strict');

const {
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
} = require('../../skills/destructive-command-protection/references/hook.js');

// ── 1. Filesystem destruction: rm -rf ──

describe('checkFilesystem / decide — rm -rf dangerous targets', () => {
  it('blocks rm -rf /', () => {
    const result = decide('rm -rf /');
    assert.notEqual(result, null);
  });

  it('blocks rm -rf ~/', () => {
    const result = decide('rm -rf ~/');
    assert.notEqual(result, null);
  });

  it('blocks rm -rf $HOME', () => {
    const result = decide('rm -rf $HOME');
    assert.notEqual(result, null);
  });

  it('blocks rm -rf /etc', () => {
    const result = decide('rm -rf /etc');
    assert.notEqual(result, null);
  });

  it('blocks rm -rf /usr', () => {
    const result = decide('rm -rf /usr');
    assert.notEqual(result, null);
  });

  it('blocks rm -rf /var', () => {
    const result = decide('rm -rf /var');
    assert.notEqual(result, null);
  });

  it('blocks rm -rf /boot', () => {
    const result = decide('rm -rf /boot');
    assert.notEqual(result, null);
  });

  it('blocks rm -rf /home', () => {
    const result = decide('rm -rf /home');
    assert.notEqual(result, null);
  });

  it('blocks rm -rf .', () => {
    const result = decide('rm -rf .');
    assert.notEqual(result, null);
  });

  it('blocks rm -rf ../../ (relative-path traversal)', () => {
    const result = decide('rm -rf ../../');
    assert.notEqual(result, null);
  });

  it('blocks rm -rf ../..', () => {
    const result = decide('rm -rf ../..');
    assert.notEqual(result, null);
  });

  it('blocks rm -rf ..', () => {
    const result = decide('rm -rf ..');
    assert.notEqual(result, null);
  });

  it('blocks rm -fr / (flag order reversed)', () => {
    const result = decide('rm -fr /');
    assert.notEqual(result, null);
  });

  it('checkFilesystem returns the same verdict directly', () => {
    assert.notEqual(checkFilesystem('rm -rf /'), null);
    assert.equal(checkFilesystem('rm -rf node_modules'), null);
  });
});

describe('decide — rm -rf safe targets', () => {
  it('allows rm -rf node_modules', () => {
    assert.equal(decide('rm -rf node_modules'), null);
  });

  it('allows rm -rf ./node_modules', () => {
    assert.equal(decide('rm -rf ./node_modules'), null);
  });

  it('allows rm -rf dist/', () => {
    assert.equal(decide('rm -rf dist/'), null);
  });

  it('allows rm -rf .next', () => {
    assert.equal(decide('rm -rf .next'), null);
  });

  it('allows rm -rf coverage', () => {
    assert.equal(decide('rm -rf coverage'), null);
  });

  it('allows rm -rf build/', () => {
    assert.equal(decide('rm -rf build/'), null);
  });

  it('allows rm -rf .cache/', () => {
    assert.equal(decide('rm -rf .cache/'), null);
  });
});

describe('decide — rm -rf unknown targets', () => {
  it('allows rm -rf on unknown paths (documents current behavior)', () => {
    assert.equal(decide('rm -rf /some/random/path'), null);
  });
});

// ── 2. Database destruction ──

describe('checkDatabase / decide — database operations', () => {
  it('blocks DROP DATABASE production', () => {
    const result = decide('DROP DATABASE production');
    assert.notEqual(result, null);
  });

  it('blocks DROP SCHEMA myschema', () => {
    const result = decide('DROP SCHEMA myschema');
    assert.notEqual(result, null);
  });

  it('blocks drop database (case insensitive)', () => {
    const result = decide('drop database test_db');
    assert.notEqual(result, null);
  });

  it('allows DROP TABLE (regex only matches DATABASE/SCHEMA)', () => {
    assert.equal(decide('DROP TABLE IF EXISTS temp_migration'), null);
  });

  it('checkDatabase returns the same verdict directly', () => {
    assert.notEqual(checkDatabase('DROP DATABASE production'), null);
  });
});

describe('decide — TRUNCATE TABLE', () => {
  it('blocks TRUNCATE TABLE users', () => {
    const result = decide('TRUNCATE TABLE users');
    assert.notEqual(result, null);
  });

  it('allows TRUNCATE TABLE IF EXISTS (escape clause)', () => {
    assert.equal(decide('TRUNCATE TABLE IF EXISTS something'), null);
  });
});

describe('decide — Redis flush', () => {
  it('blocks redis-cli FLUSHALL', () => {
    const result = decide('redis-cli FLUSHALL');
    assert.notEqual(result, null);
  });

  it('blocks redis-cli FLUSHDB', () => {
    const result = decide('redis-cli FLUSHDB');
    assert.notEqual(result, null);
  });

  it('blocks redis-cli -h host FLUSHALL', () => {
    const result = decide('redis-cli -h redis.example.com FLUSHALL');
    assert.notEqual(result, null);
  });

  it('allows redis-cli GET key', () => {
    assert.equal(decide('redis-cli GET mykey'), null);
  });
});

describe('decide — MongoDB destruction', () => {
  it('blocks mongosh with dropDatabase()', () => {
    const result = decide('mongosh --eval "db.dropDatabase()"');
    assert.notEqual(result, null);
  });

  it('blocks mongo with .drop()', () => {
    const result = decide('mongo mydb --eval "db.users.drop()"');
    assert.notEqual(result, null);
  });

  it('allows mongosh with find()', () => {
    assert.equal(decide('mongosh --eval "db.users.find()"'), null);
  });
});

// ── 3. Disk operations ──

describe('checkSystem / decide — disk operations', () => {
  it('blocks mkfs.ext4 /dev/sdb', () => {
    const result = decide('mkfs.ext4 /dev/sdb');
    assert.notEqual(result, null);
  });

  it('blocks dd if=/dev/zero of=/dev/sda', () => {
    const result = decide('dd if=/dev/zero of=/dev/sda');
    assert.notEqual(result, null);
  });

  it('blocks > /dev/sda', () => {
    const result = decide('> /dev/sda');
    assert.notEqual(result, null);
  });

  it('blocks > /dev/hda', () => {
    const result = decide('> /dev/hda');
    assert.notEqual(result, null);
  });
});

// ── 4. System abuse ──

describe('decide — chmod', () => {
  it('blocks chmod -R 777 /', () => {
    const result = decide('chmod -R 777 /');
    assert.notEqual(result, null);
  });

  it('blocks chmod 777 /etc (non-recursive on a system path)', () => {
    const result = decide('chmod 777 /etc');
    assert.notEqual(result, null);
  });

  it('allows chmod 777 on non-root paths (e.g., ./tmp)', () => {
    assert.equal(decide('chmod 777 ./tmp'), null);
  });

  it('allows chmod 755 /etc (non-777 mode on a system path)', () => {
    assert.equal(decide('chmod 755 /etc'), null);
  });
});

describe('decide — fork bomb', () => {
  it('blocks :(){ :|:& };:', () => {
    const result = decide(':(){ :|:& };:');
    assert.notEqual(result, null);
  });
});

describe('decide — kill', () => {
  it('blocks kill 1 (targets init, even without -9)', () => {
    const result = decide('kill 1');
    assert.notEqual(result, null);
  });

  it('blocks kill -9 1', () => {
    const result = decide('kill -9 1');
    assert.notEqual(result, null);
  });

  it('blocks kill -1 (targets all processes, even without -9)', () => {
    const result = decide('kill -1');
    assert.notEqual(result, null);
  });

  it('blocks kill -9 -1', () => {
    const result = decide('kill -9 -1');
    assert.notEqual(result, null);
  });

  it('blocks kill -15 1', () => {
    const result = decide('kill -15 1');
    assert.notEqual(result, null);
  });

  it('allows kill with a specific PID', () => {
    assert.equal(decide('kill 12345'), null);
    assert.equal(decide('kill -9 12345'), null);
  });

  it('allows kill 100 / kill -9 100 (pid does not resolve to 1/-1)', () => {
    assert.equal(decide('kill 100'), null);
    assert.equal(decide('kill -9 100'), null);
  });

  it('checkSystem returns the same verdict directly', () => {
    assert.notEqual(checkSystem('kill -9 1'), null);
    assert.notEqual(checkSystem('kill 1'), null);
    assert.equal(checkSystem('kill 100'), null);
  });
});

// ── 5. Git data destruction ──

describe('checkGit / decide — git stash destruction', () => {
  it('blocks git stash drop', () => {
    const result = decide('git stash drop');
    assert.notEqual(result, null);
  });

  it('blocks git stash drop stash@{0}', () => {
    const result = decide('git stash drop stash@{0}');
    assert.notEqual(result, null);
  });

  it('blocks git stash clear', () => {
    const result = decide('git stash clear');
    assert.notEqual(result, null);
  });

  it('allows git stash (save)', () => {
    assert.equal(decide('git stash'), null);
  });

  it('allows git stash pop', () => {
    assert.equal(decide('git stash pop'), null);
  });

  it('allows git stash list', () => {
    assert.equal(decide('git stash list'), null);
  });

  it('allows git stash show', () => {
    assert.equal(decide('git stash show'), null);
  });

  it('checkGit returns the same verdict directly', () => {
    assert.notEqual(checkGit('git stash clear'), null);
    assert.equal(checkGit('git stash pop'), null);
  });
});

// ── 6. Shell wrapper bypass ──

describe('checkBypass / decide — shell wrapper bypass', () => {
  it('blocks bash -c "rm -rf /"', () => {
    const result = decide('bash -c "rm -rf /"');
    assert.notEqual(result, null);
    assert.ok(result.reason.includes('shell-wrapper'));
  });

  it('blocks sh -c "git stash clear"', () => {
    const result = decide('sh -c "git stash clear"');
    assert.notEqual(result, null);
  });

  it('blocks bash -c "DROP DATABASE prod"', () => {
    const result = decide('bash -c "DROP DATABASE prod"');
    assert.notEqual(result, null);
  });

  it('allows bash -c "echo hello"', () => {
    assert.equal(decide('bash -c "echo hello"'), null);
  });

  it('allows sh -c "ls -la"', () => {
    assert.equal(decide('sh -c "ls -la"'), null);
  });

  it('blocks nested shell wrappers (bash -c wrapping sh -c)', () => {
    const result = decide("bash -c \"sh -c 'rm -rf /'\"");
    assert.notEqual(result, null);
  });

  it('checkBypass returns the same verdict directly', () => {
    assert.notEqual(checkBypass('bash -c "rm -rf /"'), null);
    assert.equal(checkBypass('bash -c "echo hello"'), null);
  });
});

// ── 7. Interpreter one-liners ──

describe('decide — Python one-liners', () => {
  it('blocks python -c with os.system()', () => {
    const result = decide('python -c "import os; os.system(\'rm -rf /\')"');
    assert.notEqual(result, null);
  });

  it('blocks python3 -c with shutil.rmtree', () => {
    const result = decide('python3 -c "import shutil; shutil.rmtree(\'/tmp/data\')"');
    assert.notEqual(result, null);
  });

  it('blocks python -c with subprocess.call shelling out to a "rm -rf" string', () => {
    const result = decide('python -c "import subprocess; subprocess.call(\'rm -rf /\')"');
    assert.notEqual(result, null);
  });

  it('allows python -c with subprocess.run(list-form) args (the "rm -rf" substring is split across list elements; documents current behavior)', () => {
    assert.equal(decide('python -c "import subprocess; subprocess.run([\'rm\', \'-rf\', \'/\'])"'), null);
  });

  it('allows python -c with print()', () => {
    assert.equal(decide('python -c "print(\'hello\')"'), null);
  });
});

describe('decide — Node.js one-liners', () => {
  it('blocks node -e with execSync', () => {
    const result = decide('node -e "require(\'child_process\').execSync(\'rm -rf /\')"');
    assert.notEqual(result, null);
  });

  it('blocks node --eval with fs.rmSync recursive', () => {
    const result = decide('node --eval "fs.rmSync(\'/tmp\', {recursive: true})"');
    assert.notEqual(result, null);
  });

  it('allows node --eval with rmSync via require(\'fs\').rmSync (the "fs.rmSync(" substring is not literally present; documents current behavior)', () => {
    assert.equal(decide('node --eval "require(\'fs\').rmSync(\'/tmp\', {recursive: true})"'), null);
  });

  it('allows node -e with console.log', () => {
    assert.equal(decide('node -e "console.log(\'hello\')"'), null);
  });
});

describe('decide — Ruby one-liners', () => {
  it('blocks ruby -e with FileUtils.rm_rf', () => {
    const result = decide('ruby -e "require \'fileutils\'; FileUtils.rm_rf(\'/tmp\')"');
    assert.notEqual(result, null);
  });

  it('blocks ruby -e with system()', () => {
    const result = decide('ruby -e "system(\'rm -rf /\')"');
    assert.notEqual(result, null);
  });

  it('allows ruby -e with puts', () => {
    assert.equal(decide('ruby -e "puts \'hello\'"'), null);
  });
});

// ── 8. Container destruction ──

describe('checkContainers / decide — Docker destruction', () => {
  it('blocks docker system prune', () => {
    const result = decide('docker system prune');
    assert.notEqual(result, null);
  });

  it('blocks docker system prune -a --volumes', () => {
    const result = decide('docker system prune -a --volumes');
    assert.notEqual(result, null);
  });

  it('blocks docker volume prune', () => {
    const result = decide('docker volume prune');
    assert.notEqual(result, null);
  });

  it('blocks docker container prune', () => {
    const result = decide('docker container prune');
    assert.notEqual(result, null);
  });

  it('blocks docker image prune', () => {
    const result = decide('docker image prune');
    assert.notEqual(result, null);
  });

  it('blocks docker compose down -v', () => {
    const result = decide('docker compose down -v');
    assert.notEqual(result, null);
  });

  it('blocks docker-compose down -v', () => {
    const result = decide('docker-compose down -v');
    assert.notEqual(result, null);
  });

  it('allows docker compose down (without -v)', () => {
    assert.equal(decide('docker compose down'), null);
  });

  it('allows docker ps', () => {
    assert.equal(decide('docker ps'), null);
  });

  it('allows docker build', () => {
    assert.equal(decide('docker build .'), null);
  });
});

// ── 9. Infrastructure destruction ──

describe('checkIac / decide — Infrastructure destruction', () => {
  it('blocks terraform destroy', () => {
    const result = decide('terraform destroy');
    assert.notEqual(result, null);
  });

  it('blocks terraform destroy -auto-approve', () => {
    const result = decide('terraform destroy -auto-approve');
    assert.notEqual(result, null);
  });

  it('blocks terraform apply -auto-approve', () => {
    const result = decide('terraform apply -auto-approve');
    assert.notEqual(result, null);
  });

  it('allows terraform plan', () => {
    assert.equal(decide('terraform plan'), null);
  });

  it('allows terraform apply (without -auto-approve)', () => {
    assert.equal(decide('terraform apply'), null);
  });

  it('blocks pulumi destroy', () => {
    const result = decide('pulumi destroy');
    assert.notEqual(result, null);
  });

  it('allows pulumi up', () => {
    assert.equal(decide('pulumi up'), null);
  });
});

// ── 10. Package publishing ──

describe('checkPublishing / decide — package publishing', () => {
  it('blocks npm publish', () => {
    const result = decide('npm publish');
    assert.notEqual(result, null);
  });

  it('blocks npm publish --access public', () => {
    const result = decide('npm publish --access public');
    assert.notEqual(result, null);
  });

  it('blocks yarn publish', () => {
    const result = decide('yarn publish');
    assert.notEqual(result, null);
  });

  it('blocks gem push', () => {
    const result = decide('gem push my-gem-1.0.0.gem');
    assert.notEqual(result, null);
  });

  it('blocks twine upload', () => {
    const result = decide('twine upload dist/*');
    assert.notEqual(result, null);
  });

  it('blocks cargo publish', () => {
    const result = decide('cargo publish');
    assert.notEqual(result, null);
  });

  it('allows npm install', () => {
    assert.equal(decide('npm install'), null);
  });

  it('allows npm test', () => {
    assert.equal(decide('npm test'), null);
  });
});

// ── 11. Cloud resource destruction ──

describe('checkCloud / decide — AWS destruction', () => {
  it('blocks aws ec2 terminate-instances', () => {
    const result = decide('aws ec2 terminate-instances --instance-ids i-123');
    assert.notEqual(result, null);
  });

  it('blocks aws rds delete-db-instance', () => {
    const result = decide('aws rds delete-db-instance --db-instance-identifier mydb');
    assert.notEqual(result, null);
  });

  it('blocks aws cloudformation delete-stack', () => {
    const result = decide('aws cloudformation delete-stack --stack-name mystack');
    assert.notEqual(result, null);
  });

  it('blocks aws secretsmanager delete-secret', () => {
    const result = decide('aws secretsmanager delete-secret --secret-id mysecret');
    assert.notEqual(result, null);
  });

  it('blocks aws iam delete-role', () => {
    const result = decide('aws iam delete-role --role-name myrole');
    assert.notEqual(result, null);
  });

  it('allows aws s3 ls', () => {
    assert.equal(decide('aws s3 ls'), null);
  });

  it('allows aws ec2 describe-instances', () => {
    assert.equal(decide('aws ec2 describe-instances'), null);
  });
});

describe('checkCloud / decide — GCP destruction', () => {
  it('blocks gcloud compute instances delete', () => {
    const result = decide('gcloud compute instances delete my-vm');
    assert.notEqual(result, null);
  });

  it('blocks gcloud sql instances delete', () => {
    const result = decide('gcloud sql instances delete mydb');
    assert.notEqual(result, null);
  });

  it('blocks gcloud projects delete', () => {
    const result = decide('gcloud projects delete my-project');
    assert.notEqual(result, null);
  });

  it('allows gcloud compute instances list', () => {
    assert.equal(decide('gcloud compute instances list'), null);
  });
});

describe('checkCloud / decide — Azure destruction', () => {
  it('blocks az vm delete', () => {
    const result = decide('az vm delete --name myvm --resource-group myrg');
    assert.notEqual(result, null);
  });

  it('blocks az group delete', () => {
    const result = decide('az group delete --name myrg');
    assert.notEqual(result, null);
  });

  it('blocks az storage account delete', () => {
    const result = decide('az storage account delete --name mystorage');
    assert.notEqual(result, null);
  });

  it('blocks az keyvault delete', () => {
    const result = decide('az keyvault delete --name myvault');
    assert.notEqual(result, null);
  });

  it('allows az vm list', () => {
    assert.equal(decide('az vm list'), null);
  });
});

// ── 12. Kubernetes mass deletion ──

describe('checkKubernetes / decide — Kubernetes destruction', () => {
  it('blocks kubectl delete namespace', () => {
    const result = decide('kubectl delete namespace production');
    assert.notEqual(result, null);
  });

  it('blocks kubectl delete ns', () => {
    const result = decide('kubectl delete ns staging');
    assert.notEqual(result, null);
  });

  it('blocks kubectl delete pods --all', () => {
    const result = decide('kubectl delete pods --all');
    assert.notEqual(result, null);
  });

  it('blocks kubectl drain', () => {
    const result = decide('kubectl drain node-1');
    assert.notEqual(result, null);
  });

  it('allows kubectl get pods', () => {
    assert.equal(decide('kubectl get pods'), null);
  });

  it('allows kubectl delete pod specific-pod', () => {
    assert.equal(decide('kubectl delete pod my-pod'), null);
  });
});

// ── 13. Rsync --delete ──

describe('checkNetworkStorage / decide — rsync --delete', () => {
  it('blocks rsync --delete', () => {
    const result = decide('rsync -avz --delete src/ dest/');
    assert.notEqual(result, null);
  });

  it('blocks rsync with --delete-before', () => {
    // --delete-before contains --delete
    const result = decide('rsync --delete-before src/ dest/');
    assert.notEqual(result, null);
  });

  it('allows rsync without --delete', () => {
    assert.equal(decide('rsync -avz src/ dest/'), null);
  });
});

// ── 14. Cloud storage mass deletion ──

describe('checkNetworkStorage / decide — cloud storage deletion', () => {
  it('blocks aws s3 rm --recursive', () => {
    const result = decide('aws s3 rm s3://my-bucket --recursive');
    assert.notEqual(result, null);
  });

  it('blocks aws s3 rb --recursive (remove bucket)', () => {
    const result = decide('aws s3 rb s3://my-bucket --recursive');
    assert.notEqual(result, null);
  });

  it('blocks gsutil rm -r', () => {
    const result = decide('gsutil rm -r gs://my-bucket');
    assert.notEqual(result, null);
  });

  it('blocks azcopy remove --recursive', () => {
    const result = decide('azcopy remove "https://account.blob.core.windows.net/container" --recursive');
    assert.notEqual(result, null);
  });

  it('allows aws s3 ls', () => {
    assert.equal(decide('aws s3 ls s3://my-bucket'), null);
  });

  it('allows aws s3 cp (non-recursive single file)', () => {
    assert.equal(decide('aws s3 cp file.txt s3://my-bucket/'), null);
  });
});

// ── Edge cases ──

describe('decide — edge cases', () => {
  it('returns null for empty command', () => {
    assert.equal(decide(''), null);
  });

  it('returns null for safe commands', () => {
    assert.equal(decide('npm test'), null);
    assert.equal(decide('ls -la'), null);
    assert.equal(decide('git status'), null);
  });
});

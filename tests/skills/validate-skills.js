#!/usr/bin/env node

/**
 * Skill Validation Script
 *
 * Validates all skills in the skills/ directory for:
 * - Valid YAML frontmatter with required fields
 * - Name matching directory name
 * - Valid category values
 * - Background skills have user-invocable: false
 * - Workflow skills have triggers array
 * - Referenced files in references/ exist
 */

const fs = require('node:fs');
const path = require('node:path');

const SKILLS_DIR = path.join(__dirname, '..', '..', 'skills');
const VALID_CATEGORIES = ['process', 'meta', 'guideline', 'protocol', 'enforcement'];

let errors = 0;
let warnings = 0;
let skillCount = 0;

function error(skill, msg) {
  console.error(`  ERROR [${skill}]: ${msg}`);
  errors++;
}

function warn(skill, msg) {
  console.warn(`  WARN  [${skill}]: ${msg}`);
  warnings++;
}

function parseFrontmatter(content) {
  const match = content.match(/^---\n([\s\S]*?)\n---/);
  if (!match) return null;

  const yaml = match[1];
  const fields = {};

  for (const line of yaml.split('\n')) {
    // Handle simple key: value pairs
    const kvMatch = line.match(/^(\w[\w-]*)\s*:\s*(.+)$/);
    if (kvMatch) {
      const key = kvMatch[1];
      let value = kvMatch[2].trim();

      // Parse booleans
      if (value === 'true') value = true;
      else if (value === 'false') value = false;

      fields[key] = value;
      continue;
    }

    // Handle array items (triggers)
    const arrayMatch = line.match(/^\s+-\s+(.+)$/);
    if (arrayMatch && fields._lastArrayKey) {
      if (!Array.isArray(fields[fields._lastArrayKey])) {
        fields[fields._lastArrayKey] = [];
      }
      fields[fields._lastArrayKey].push(arrayMatch[1].trim());
      continue;
    }

    // Handle key with no inline value (start of array or block)
    const blockMatch = line.match(/^(\w[\w-]*)\s*:\s*$/);
    if (blockMatch) {
      fields._lastArrayKey = blockMatch[1];
      fields[blockMatch[1]] = [];
    }
  }

  delete fields._lastArrayKey;
  return fields;
}

function validateSkill(dirName) {
  const skillPath = path.join(SKILLS_DIR, dirName, 'SKILL.md');

  if (!fs.existsSync(skillPath)) {
    error(dirName, 'Missing SKILL.md');
    return;
  }

  const content = fs.readFileSync(skillPath, 'utf8');
  const frontmatter = parseFrontmatter(content);

  if (!frontmatter) {
    error(dirName, 'Missing or invalid YAML frontmatter');
    return;
  }

  // Required fields
  if (!frontmatter.name) {
    error(dirName, 'Missing required field: name');
  } else if (frontmatter.name !== dirName) {
    error(dirName, `name "${frontmatter.name}" does not match directory "${dirName}"`);
  }

  if (!frontmatter.description) {
    error(dirName, 'Missing required field: description');
  }

  if (!frontmatter.category) {
    error(dirName, 'Missing required field: category');
  } else if (!VALID_CATEGORIES.includes(frontmatter.category)) {
    error(dirName, `Invalid category "${frontmatter.category}". Must be one of: ${VALID_CATEGORIES.join(', ')}`);
  }

  // Background vs workflow checks
  const isBackground = frontmatter['user-invocable'] === false;
  const isWorkflow = !isBackground;

  if (isWorkflow) {
    const triggers = frontmatter.triggers;
    if (!triggers || (Array.isArray(triggers) && triggers.length === 0)) {
      // Only warn for process/meta categories (workflow skills)
      if (['process', 'meta'].includes(frontmatter.category)) {
        warn(dirName, 'Workflow skill missing triggers array');
      }
    }
  }

  // Check that guideline/protocol/enforcement skills are marked as background
  if (['guideline', 'protocol', 'enforcement'].includes(frontmatter.category) && !isBackground) {
    warn(dirName, `Category "${frontmatter.category}" should have user-invocable: false`);
  }

  // Check references/ directory
  const refsDir = path.join(SKILLS_DIR, dirName, 'references');
  if (fs.existsSync(refsDir)) {
    const refFiles = fs.readdirSync(refsDir);

    // Check that referenced files from SKILL.md exist
    const bodyText = content.replace(/^---[\s\S]*?---/, '');
    const refsPattern = /references\/([\w][\w.-]*\.(?:md|js|json|yaml|yml|ts))/g;
    let match;
    const checkedRefs = new Set();
    while ((match = refsPattern.exec(bodyText)) !== null) {
      const refFile = match[1];
      if (checkedRefs.has(refFile)) continue;
      checkedRefs.add(refFile);
      const refPath = path.join(refsDir, refFile);
      if (!fs.existsSync(refPath)) {
        error(dirName, `Referenced file does not exist: references/${refFile}`);
      }
    }
  }

  skillCount++;
}

// Main
console.log('Validating skills...\n');

const entries = fs.readdirSync(SKILLS_DIR, { withFileTypes: true });
const dirs = entries
  .filter(e => e.isDirectory())
  .map(e => e.name)
  .sort();

for (const dir of dirs) {
  validateSkill(dir);
}

console.log(`\nResults: ${skillCount} skills validated, ${errors} errors, ${warnings} warnings`);

if (errors > 0) {
  process.exit(1);
} else {
  console.log('All skills passed validation.');
}

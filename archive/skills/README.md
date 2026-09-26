# Archived skills

These were retired from the `ai-assistant-starter` plugin (unlinked from `plugins/ai-assistant-starter/skills/`) after a usage audit showed zero invocations. Kept here as reference material, not as active skills — each folder's `SKILL.md` was renamed to `REFERENCE.md` so it won't be picked up by skill discovery even if this directory is ever pointed at by a marketplace path.

To reinstate one: `git mv archive/skills/<name>/REFERENCE.md archive/skills/<name>/SKILL.md`, move the folder back to `skills/`, and re-add the symlink under `plugins/ai-assistant-starter/skills/<name>`.

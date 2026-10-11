# Skill Installation

[中文](INSTALL_SKILL_CN.md)

```bash
# Any agent (Claude Code, Cursor, Copilot, etc.)
npx skills add Agents365-ai/drawio-skill -g
```

Manual install: clone once to a persistent path, then link the skill subdirectory into the host skills root. Use `cp -R` instead of `ln -s` on hosts that do not follow symlinks.

```bash
# Clone once to a persistent path (use a location that does not exist yet,
# or reuse an existing clone of this repository)
mkdir -p ~/src
git clone https://github.com/Agents365-ai/drawio-skill.git ~/src/drawio-skill

# Link the skill subdirectory into the host skills root (Claude Code shown).
# The destination must not exist yet: plain ln -s nests inside an existing directory.
mkdir -p ~/.claude/skills
ln -s ~/src/drawio-skill/skills/drawio-skill ~/.claude/skills/drawio-skill

# Copy instead, for hosts that do not follow symlinks
# mkdir -p ~/.claude/skills
# cp -R ~/src/drawio-skill/skills/drawio-skill ~/.claude/skills/drawio-skill
```

The host entry must expose the skill as `<skills root>/drawio-skill/SKILL.md`. Do not clone the repository root into a skills directory. The nested root does not match the documented one-level layout, and recursive discovery varies by host. If `drawio-skill` is already installed, move the old entry aside before you create the new entry, or reuse the source clone at a stable location. If an earlier install cloned the repository root into the skills directory, reuse it as the clone, or move it aside.

Common paths: `~/.claude/skills/` (Claude Code), `.claude/skills/` (Claude Code project), `~/.config/opencode/skills/` (Opencode), `~/.openclaw/skills/` (OpenClaw), `~/.agents/skills/` (Codex), `~/.autohand/skills/` (Autohand Code global), and `<project>/.autohand/skills/` (Autohand Code project). Also indexed on [SkillsMP](https://skillsmp.com/skills/agents365-ai-drawio-skill-skills-drawio-skill-skill-md).

Autohand Code supports `autohand --skill-install` for cataloged skills, with `--project` for workspace-level installs. Until this skill is listed there, use the manual recipe above, linking `skills/drawio-skill` into `~/.autohand/skills/` (global) or `<project>/.autohand/skills/` (project).

## Updates

The recommended installer owns its own update command. SkillsMP is a listing only: it does not install or update skills.

```bash
# Global install made with the skills CLI
npx skills update drawio-skill -g
```

A link install follows the clone. Update the clone to update the skill:

```bash
git -C ~/src/drawio-skill pull
```

A copy install does not follow the clone. Update the clone, then copy `skills/drawio-skill/` again into an empty destination. Move the old copy aside first: copying into an existing `drawio-skill` directory nests a second copy inside it.

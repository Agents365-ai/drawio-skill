# Skill Installation

[中文](INSTALL_SKILL_CN.md)

```bash
# Any agent (Claude Code, Cursor, Copilot, etc.)
npx skills add Agents365-ai/365-skills -g

# Claude Code only
> /plugin marketplace add Agents365-ai/365-skills
> /plugin install drawio
```

Manual install — clone into your agent's skills directory:

```bash
git clone https://github.com/Agents365-ai/drawio-skill.git ~/.claude/skills/drawio-skill
git clone https://github.com/Agents365-ai/drawio-skill.git ~/.autohand/skills/drawio-skill
git clone https://github.com/Agents365-ai/drawio-skill.git .autohand/skills/drawio-skill
```

Common paths: `~/.claude/skills/` (Claude Code), `~/.config/opencode/skills/` (Opencode), `~/.openclaw/skills/` (OpenClaw), `~/.agents/skills/` (Codex), `~/.autohand/skills/` (Autohand Code global), and `<project>/.autohand/skills/` (Autohand Code project). Also indexed on [SkillsMP](https://skillsmp.com/skills/agents365-ai-drawio-skill-skills-drawio-skill-skill-md) and [ClawHub](https://clawhub.ai/agents365-ai/drawio-pro-skill).

Autohand Code supports `autohand --skill-install` for cataloged skills, with `--project` for workspace-level installs. Until this skill is listed there, use the direct clone path above.

## Updates

Updates flow through whatever channel you installed from:

```bash
# Claude Code plugin
/plugin update drawio

# OpenClaw
clawhub update drawio-pro-skill

# SkillsMP
skills update drawio-skill
```

For direct `git clone` installs, pull from your install directory:

```bash
cd <your-install-path>/drawio-skill && git pull
```

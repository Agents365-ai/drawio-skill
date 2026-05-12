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
```

Common paths: `~/.claude/skills/` (Claude Code), `~/.config/opencode/skills/` (Opencode), `~/.openclaw/skills/` (OpenClaw), `~/.agents/skills/` (Codex). Also indexed on [SkillsMP](https://skillsmp.com/skills/agents365-ai-drawio-skill-skill-md) and [ClawHub](https://clawhub.ai/agents365-ai/drawio-pro-skill).

## Updates

The skill auto-checks for updates once per 24 hours on first use in a conversation. When a new version is available, the agent prints a one-line notice in the reply. To apply:

```bash
cd <your-install-path>/drawio-skill && git pull
```

The check is read-only, self-throttled, and silent when up to date, offline, or not a git install — it won't block or slow the workflow.

Plugin-marketplace installs update automatically via the 365-skills umbrella. Package-manager installs handle updates themselves:

```bash
# Claude Code plugin
/plugin update drawio

# OpenClaw
clawhub update drawio-pro-skill

# SkillsMP
skills update drawio-skill
```

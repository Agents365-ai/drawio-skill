# 技能安装

[English](INSTALL_SKILL.md)

```bash
# 任意 Agent（Claude Code、Cursor、Copilot 等）
npx skills add Agents365-ai/365-skills -g

# 仅 Claude Code
> /plugin marketplace add Agents365-ai/365-skills
> /plugin install drawio
```

手动安装 —— 克隆到你的 Agent skills 目录：

```bash
git clone https://github.com/Agents365-ai/drawio-skill.git ~/.claude/skills/drawio-skill
git clone https://github.com/Agents365-ai/drawio-skill.git ~/.autohand/skills/drawio-skill
git clone https://github.com/Agents365-ai/drawio-skill.git .autohand/skills/drawio-skill
```

常用路径：`~/.claude/skills/`（Claude Code）、`~/.config/opencode/skills/`（Opencode）、`~/.openclaw/skills/`（OpenClaw）、`~/.agents/skills/`（Codex）、`~/.autohand/skills/`（Autohand Code 全局）和 `<project>/.autohand/skills/`（Autohand Code 项目级）。同时已索引于 [SkillsMP](https://skillsmp.com/skills/agents365-ai-drawio-skill-skills-drawio-skill-skill-md) 和 [ClawHub](https://clawhub.ai/agents365-ai/drawio-pro-skill)。

Autohand Code 支持通过 `autohand --skill-install` 安装已收录在 Autohand catalog 中的 skill，并可通过 `--project` 安装到当前项目。在该 skill 收录前，请使用上面的直接克隆方式。

## 更新

按你的安装渠道走对应的更新命令：

```bash
# Claude Code 插件
/plugin update drawio

# OpenClaw
clawhub update drawio-pro-skill

# SkillsMP
skills update drawio-skill
```

通过 `git clone` 手动安装的用户，在安装目录下拉取：

```bash
cd <你的安装路径>/drawio-skill && git pull
```

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
```

常用路径：`~/.claude/skills/`（Claude Code）、`~/.config/opencode/skills/`（Opencode）、`~/.openclaw/skills/`（OpenClaw）、`~/.agents/skills/`（Codex）。同时已索引于 [SkillsMP](https://skillsmp.com/skills/agents365-ai-drawio-skill-skill-md) 和 [ClawHub](https://clawhub.ai/agents365-ai/drawio-pro-skill)。

## 更新

Skill 会在每次对话首次使用时自动检查更新（24 小时节流）。有新版本时，Agent 会在回复中打印一行提示。应用更新：

```bash
cd <你的安装路径>/drawio-skill && git pull
```

检查为只读、自节流，在已是最新版、离线、或非 git 安装时静默退出，不会阻塞或拖慢工作流。

通过插件市场安装的用户通过 365-skills umbrella 自动更新。通过包管理器安装的用户直接用对应命令更新：

```bash
# Claude Code 插件
/plugin update drawio

# OpenClaw
clawhub update drawio-pro-skill

# SkillsMP
skills update drawio-skill
```

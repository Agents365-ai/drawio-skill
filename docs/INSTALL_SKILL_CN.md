# 技能安装

[English](INSTALL_SKILL.md)

```bash
# 任意 Agent（Claude Code、Cursor、Copilot 等）
npx skills add Agents365-ai/drawio-skill -g
```

手动安装：先克隆到一个固定路径，再把 skill 子目录链接进宿主 skills 根目录。宿主不支持符号链接时改用 `cp -R`。

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

宿主条目必须把 skill 呈现为 `<skills root>/drawio-skill/SKILL.md`。不要把仓库根目录克隆进 skills 目录。这种嵌套根目录不符合文档记录的一层布局，是否递归发现嵌套根目录因宿主而异。如果已经装有 `drawio-skill`，请先把旧条目移到别处再创建新条目，或者复用稳定位置的源克隆目录。早期安装若把仓库根目录克隆进了 skills 目录，可以把它复用为克隆目录，或者移走。

常用路径：`~/.claude/skills/`（Claude Code）、`.claude/skills/`（Claude Code 项目级）、`~/.config/opencode/skills/`（Opencode）、`~/.openclaw/skills/`（OpenClaw）、`~/.agents/skills/`（Codex）、`~/.autohand/skills/`（Autohand Code 全局）和 `<project>/.autohand/skills/`（Autohand Code 项目级）。同时已索引于 [SkillsMP](https://skillsmp.com/skills/agents365-ai-drawio-skill-skills-drawio-skill-skill-md)。

Autohand Code 支持通过 `autohand --skill-install` 安装已收录在 Autohand catalog 中的 skill，并可通过 `--project` 安装到当前项目。在该 skill 收录前，请按上面的手动安装方式，把 `skills/drawio-skill` 链接进 `~/.autohand/skills/`（全局）或 `<project>/.autohand/skills/`（项目级）。

## 更新

推荐的更新命令由 `npx skills` 安装器提供。SkillsMP 只是索引：它不安装也不更新 skill。

```bash
# Global install made with the skills CLI
npx skills update drawio-skill -g
```

链接安装跟随克隆目录，更新克隆即可更新 skill：

```bash
git -C ~/src/drawio-skill pull
```

复制安装不跟随克隆目录。先更新克隆，再把 `skills/drawio-skill/` 重新复制到一个空目标。请先移走旧副本：往已存在的 `drawio-skill` 目录里复制会嵌套出第二份副本。

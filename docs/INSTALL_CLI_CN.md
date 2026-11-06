# 前置依赖 —— draw.io 桌面版

[English](INSTALL_CLI.md)

需要安装 draw.io 桌面版用于图表导出：

## macOS

```bash
# 推荐方式 — Homebrew
brew install --cask drawio

# 验证安装
drawio --version
```

## Windows

从以下地址下载安装包：https://github.com/jgraph/drawio-desktop/releases

```powershell
# 验证安装
"C:\Program Files\draw.io\draw.io.exe" --version
```

Skill 会自动定位该可执行文件（`scripts/drawio_cli.py`：先试两个 PATH 名称，再试两个默认安装目录），默认安装无需修改 PATH。若装在其他位置，请把该目录加入 PATH。

## Linux

从以下地址下载 `.deb` 或 `.rpm` 包：https://github.com/jgraph/drawio-desktop/releases

```bash
# 无头导出（Linux 服务器无显示器时必须）
sudo apt install xvfb  # Debian/Ubuntu
xvfb-run -a drawio --version
```

| 平台 | 额外步骤 |
|------|----------|
| **macOS** | Homebrew 安装后无需额外操作 |
| **Windows** | 如不在 PATH 中，使用完整路径；Skill 也会自行探测两个默认安装目录 |
| **Linux** | 无头导出时命令前加 `xvfb-run -a` |

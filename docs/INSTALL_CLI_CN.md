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
| **Windows** | 如不在 PATH 中，使用完整路径 |
| **Linux** | 无头导出时命令前加 `xvfb-run -a` |

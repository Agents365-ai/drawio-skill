# Prerequisites — draw.io desktop

[中文](INSTALL_CLI_CN.md)

The draw.io desktop app must be installed for diagram export:

## macOS

```bash
# Recommended — Homebrew
brew install --cask drawio

# Verify
drawio --version
```

## Windows

Download and install from: https://github.com/jgraph/drawio-desktop/releases

```powershell
# Verify
"C:\Program Files\draw.io\draw.io.exe" --version
```

## Linux

Download `.deb` or `.rpm` from: https://github.com/jgraph/drawio-desktop/releases

```bash
# Headless export (required on Linux servers without display)
sudo apt install xvfb  # Debian/Ubuntu
xvfb-run -a drawio --version
```

| Platform | Extra step |
|----------|------------|
| **macOS** | No extra steps after Homebrew install |
| **Windows** | Use full path if not in PATH |
| **Linux** | Wrap commands with `xvfb-run -a` for headless export |

---
name: windows-wsl-management
description: "Manage WSL on Windows: inspect distros, probe running states, execute commands inside WSL, remove distros, uninstall the WSL Windows feature, clean Task Scheduler entries, and remove app artifacts in WSL filesystems."
version: 0.1.0
author: Hermes Agent
license: MIT
platforms: [windows]
metadata:
  hermes:
    tags: [windows, wsl, system-admin, cleanup, hermes]
---

# Windows WSL Management

Use this skill when the user asks to inspect, reconfigure, or remove WSL from a Windows host, especially when they also want to clean up Hermes artifacts inside the distro or Task Scheduler artifacts tied to WSL on the Windows side.

On Windows hosts, `terminal` runs bash through MSYS/git-bash. Use `wsl.exe` and `schtasks.exe` directly; don't try PowerShell builtins.

## 1. Inspect distros

```bash
wsl.exe --list --verbose
```

Look for `NAME` and `STATE` (`Stopped`, `Running`).

## 2. Run commands inside a specific distro

```bash
wsl.exe -d <DistroName> -e bash -lc '<command>'
```

This is the reliable way to reach a specific distro with a login shell.

Useful probes:
```bash
# OS release
wsl.exe -d Ubuntu -e bash -lc 'cat /etc/os-release'

# Hermes cron files
wsl.exe -d Ubuntu -e bash -lc 'ls -la /home/$USER/.hermes/cron'

# Hermes binary
wsl.exe -d Ubuntu -e bash -lc 'command -v hermes'

# Detect WSL-related scheduled tasks
schtasks.exe /query /fo LIST | grep -i 'wsl'
```

## 3. Remove a WSL distro

```bash
# Make sure it's not running
wsl.exe --terminate Ubuntu
# Remove filesystem and registration
wsl.exe --unregister Ubuntu
```

`--unregister` is destructive and irreversible.

## 4. Uninstall the WSL Windows feature

Removes the subsystem itself, not just one distro.

```bash
# Disable WSL optional feature
dism.exe /online /disable-feature /featurename:Microsoft-Windows-Subsystem-Linux /norestart

# Optionally disable Virtual Machine Platform, which WSL 2 depends on
dism.exe /online /disable-feature /featurename:VirtualMachinePlatform /norestart
```

Requires admin privileges and usually a restart.

## 5. Clean Task Scheduler entries related to WSL

```bash
# Find task names containing WSL or Ubuntu
schtasks.exe /query /fo LIST | grep -iE 'wsl|ubuntu'

# Delete by exact task name
schtasks.exe /delete /tn "<TaskName>" /f
```

Use exact names from the query output.

## 6. Remove Hermes artifacts inside a WSL distro

```bash
wsl.exe -d <DistroName> -e bash -lc '
  rm -rf ~/.hermes/cron/*
  # If the user wants full Hermes removal in WSL:
  rm -f ~/.local/bin/hermes
  rm -rf ~/.hermes
'
```

## Pitfalls

- `wsl.exe --unregister` fails if the distro is running. Always terminate first.
- Task Scheduler task names are case-sensitive in `/delete /tn`.
- DISM feature disable is silent on success; verify with a follow-up query if needed.
- Running WSL commands through git-bash is fine; don't switch the whole session to PowerShell builtins.

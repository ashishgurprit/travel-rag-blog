---
description: Sync project with Streamlined Development master
allowed-tools: ["Bash", "Read", "Write"]
---

# Sync with Master

Synchronize this project's lessons and commands with the Streamlined Development master.

## Instructions

1. **Check current status**:
   - Read `.claude/.master-version` for current version
   - Read `.claude/.master-path` for master location
   - Compare with master VERSION

2. **Show what's new**:
   - Display changelog entries since project version
   - List new lessons added
   - List updated commands

3. **Sync options**:
   - `pull` - Get latest from master
   - `push` - Contribute lessons to master
   - `status` - Just show version comparison

4. **Execute sync**:
   - For pull: Run `~/streamlined-development/scripts/sync-from-master.sh`
   - For push: Run `~/streamlined-development/scripts/contribute-lesson.sh`

## Usage

```
/project:sync           # Show status
/project:sync pull      # Get latest from master
/project:sync push      # Contribute lessons back
```

## Arguments

$ARGUMENTS

- No args or `status`: Show version comparison
- `pull`: Sync from master to this project
- `push`: Contribute this project's lessons to master

## Output

```
╔════════════════════════════════════════════════════════════╗
║                    SYNC STATUS                             ║
╠════════════════════════════════════════════════════════════╣
║ Project Version: 1.0.0                                     ║
║ Master Version:  1.2.0                                     ║
║ Status:          ⚠ Behind by 2 versions                   ║
╠════════════════════════════════════════════════════════════╣
║ New in master:                                             ║
║   • 3 new lessons (auth, database, testing)               ║
║   • Updated /project:pre-deploy command                    ║
║   • New skill: api-contracts/                              ║
╠════════════════════════════════════════════════════════════╣
║ Run `/project:sync pull` to update                         ║
╚════════════════════════════════════════════════════════════╝
```

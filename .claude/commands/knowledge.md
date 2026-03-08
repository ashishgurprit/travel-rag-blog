---
description: Search and reference the local GitHub knowledge base when building skills, lessons, or new apps
---

# /knowledge — Query the Knowledge Base

Search and reference the local GitHub knowledge base when building skills, lessons, or new apps.

## Usage

```bash
# Search across all tracked repos
python ~/Documents/Coding/knowledge-base/fetch.py search <query>

# Show full knowledge for a specific repo
python ~/Documents/Coding/knowledge-base/fetch.py show <repo-name>

# List all tracked repos
python ~/Documents/Coding/knowledge-base/fetch.py list

# Add a new repo
python ~/Documents/Coding/knowledge-base/fetch.py add <github-url>

# Update stale repos (>30 days old)
python ~/Documents/Coding/knowledge-base/fetch.py update
```

## When Building a Skill or App

1. Run `search` with the technology/domain (e.g. `search RAG`, `search langchain`, `search agents`)
2. Read the matching repo's README via `show <repo-name>`
3. Browse `~/Documents/Coding/knowledge-base/sources/<repo>/` for subdir READMEs
4. Reference patterns found when generating the skill's SKILL.md

## Knowledge Base Location

- Registry: `~/Documents/Coding/knowledge-base/repos.yaml`
- Sources:   `~/Documents/Coding/knowledge-base/sources/<repo-name>/`
- Mac path:  `~/development/coding/knowledge-base/` (same structure)

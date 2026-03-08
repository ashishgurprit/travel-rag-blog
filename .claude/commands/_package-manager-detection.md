---
description: Package manager detection helper for commands
type: internal-helper
---

# Package Manager Detection

All commands should detect the project's package manager and use it consistently.

## Detection Logic

```bash
# Detect package manager
if [ -f "pnpm-lock.yaml" ]; then
    PKG_MGR="pnpm"
elif [ -f "yarn.lock" ]; then
    PKG_MGR="yarn"
elif [ -f "package-lock.json" ]; then
    PKG_MGR="npm"
else
    PKG_MGR="npm"  # Default fallback
fi

# Use detected package manager
$PKG_MGR install
$PKG_MGR run dev
$PKG_MGR test
```

## Command Mapping

| Action | npm | yarn | pnpm |
|--------|-----|------|------|
| Install dependencies | `npm install` | `yarn` | `pnpm install` |
| Add package | `npm install <pkg>` | `yarn add <pkg>` | `pnpm add <pkg>` |
| Remove package | `npm uninstall <pkg>` | `yarn remove <pkg>` | `pnpm remove <pkg>` |
| Run script | `npm run <script>` | `yarn <script>` | `pnpm <script>` |
| Run tests | `npm test` | `yarn test` | `pnpm test` |
| Execute binary | `npx <cmd>` | `yarn dlx <cmd>` | `pnpm dlx <cmd>` |

## Usage in Commands

When writing command instructions, use this pattern:

### ❌ Wrong (Hardcoded)
```bash
npm test
npm run build
```

### ✅ Correct (Auto-detected)
```bash
# Detect package manager
if [ -f "pnpm-lock.yaml" ]; then
    pnpm test
elif [ -f "yarn.lock" ]; then
    yarn test
else
    npm test
fi
```

### ✅ Best (Helper variable)
```bash
# Detect once, use everywhere
PKG_MGR=$([ -f "pnpm-lock.yaml" ] && echo "pnpm" || [ -f "yarn.lock" ] && echo "yarn" || echo "npm")

$PKG_MGR test
$PKG_MGR run build
$PKG_MGR run lint
```

## In Documentation Examples

When showing examples in markdown, show the preferred package manager (pnpm) with npm as fallback:

```bash
# Install dependencies
pnpm install  # or: npm install

# Run tests
pnpm test  # or: npm test
```

Or show all options:

```bash
# Using pnpm (recommended)
pnpm test

# Using npm
npm test

# Using yarn
yarn test
```

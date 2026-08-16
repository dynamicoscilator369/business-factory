#!/usr/bin/env bash
# Argona-style /workspace layout for Grok Bot cloud computer.
set -euo pipefail
REPO="${1:-$(cd "$(dirname "$0")" && pwd)}"
WS="${WORKSPACE:-/workspace}"

mkdir -p "$WS"/{bin,config,skills,state,project}
ln -sfn "$REPO" "$WS/project/company-kernel" 2>/dev/null || cp -R "$REPO" "$WS/project/company-kernel"

cat > "$WS/config/env.sh" <<EOF
export PATH="$WS/bin:\$PATH"
export WORKSPACE="$WS"
export COMPANY_KERNEL="$WS/project/company-kernel"
EOF

echo "Bootstrap complete."
echo "  Project → $WS/project/company-kernel"
echo "  State   → $WS/state (symlink business .state here in production)"
echo "  Next: cp -R businesses/_template businesses/my-idea"

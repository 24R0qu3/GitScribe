#!/usr/bin/env bash
# install.sh — download and install gitscribe from the latest GitHub release.
#
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/24R0qu3/GitScribe/main/install.sh | bash
#
# Uninstall (semi — removes from Claude Code only):
#   curl -fsSL https://raw.githubusercontent.com/24R0qu3/GitScribe/main/install.sh | bash -s -- --uninstall
#
# Uninstall (full — also removes binary):
#   curl -fsSL https://raw.githubusercontent.com/24R0qu3/GitScribe/main/install.sh | bash -s -- --uninstall --full
set -euo pipefail

REPO="24R0qu3/GitScribe"
BIN_NAME="gitscribe"
INSTALL_DIR="${INSTALL_DIR:-$HOME/.local/bin}"
UNINSTALL=false
FULL=false

for arg in "$@"; do
  case "$arg" in
    --uninstall) UNINSTALL=true ;;
    --full)      FULL=true ;;
  esac
done

BIN="$INSTALL_DIR/$BIN_NAME"

# ── Uninstall ─────────────────────────────────────────────────────────────────
if $UNINSTALL; then
  if [ -f "$BIN" ]; then
    "$BIN" patch-claude --remove
    if $FULL; then
      rm -f "$BIN"
      echo "Removed $BIN"
    fi
  else
    echo "gitscribe not found at $BIN — nothing to uninstall."
  fi
  echo "Done."
  exit 0
fi

# ── Detect platform ───────────────────────────────────────────────────────────
OS="$(uname -s)"
case "$OS" in
  Linux)  PLATFORM="linux"  ;;
  Darwin) PLATFORM="macos"  ;;
  *)
    echo "Unsupported OS: $OS" >&2
    exit 1
    ;;
esac

# ── Resolve latest release tag ────────────────────────────────────────────────
echo "Fetching latest release..."
TAG="$(curl -fsSL "https://api.github.com/repos/$REPO/releases/latest" \
  | grep '"tag_name"' | head -1 \
  | sed 's/.*"tag_name": *"\([^"]*\)".*/\1/')"

[ -z "$TAG" ] && { echo "Could not determine latest release tag." >&2; exit 1; }

# ── Download binary ───────────────────────────────────────────────────────────
URL="https://github.com/$REPO/releases/download/$TAG/${BIN_NAME}-${TAG}-${PLATFORM}"
echo "Downloading $BIN_NAME $TAG ($PLATFORM)..."

mkdir -p "$INSTALL_DIR"
curl -fsSL "$URL" -o "$BIN"
chmod +x "$BIN"
echo "Installed to $BIN"

# ── PATH hint ─────────────────────────────────────────────────────────────────
if ! echo ":$PATH:" | grep -q ":$INSTALL_DIR:"; then
  echo ""
  echo "  $INSTALL_DIR is not in your PATH. Add it:"
  echo "    echo 'export PATH=\"$INSTALL_DIR:\$PATH\"' >> ~/.bashrc   # bash"
  echo "    echo 'export PATH=\"$INSTALL_DIR:\$PATH\"' >> ~/.zshrc    # zsh"
  echo "  Then restart your terminal."
  echo ""
fi

echo "Done. To register with Claude Code run: gitscribe patch-claude"

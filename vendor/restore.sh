#!/usr/bin/env bash
# Rebuild the exact ZMK workspace behind firmware/ using only this repository.
#
#   ./vendor/restore.sh [WORKSPACE_DIR]      (default: ~/zmk-charybdis)
#
# The big inputs (Zephyr, all west modules, ZMK, the PMW3610 driver, the arm
# toolchain) are stored as Release assets because they exceed what git allows in
# a tree. Nothing here needs the upstream repositories to still exist.
#
# Set ASSET_DIR=/path/to/archives to read the archives from disk instead of
# downloading them.
set -euo pipefail

OWNER="${OWNER:-}"
REPO_NAME="${REPO_NAME:-}"
TAG="${TAG:-v1.0.0}"
DEST="${1:-$HOME/zmk-charybdis}"

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Work out whose repository this is from the clone URL, so nothing here has to
# hardcode an account name. Override with OWNER=... REPO_NAME=... if needed.
if [ -z "$OWNER" ] || [ -z "$REPO_NAME" ]; then
  slug="$(git -C "$HERE" remote get-url origin 2>/dev/null || true)"
  slug="${slug%.git}"
  case "$slug" in
    *://*) slug="${slug#*://}"; slug="${slug#*/}" ;;  # https://host/owner/repo
    *:*)   slug="${slug##*:}" ;;                      # git@host:owner/repo
  esac
  OWNER="${OWNER:-${slug%%/*}}"
  REPO_NAME="${REPO_NAME:-${slug##*/}}"
fi
if [ -z "$OWNER" ] || [ -z "$REPO_NAME" ]; then
  echo "could not work out OWNER/REPO_NAME; run with OWNER=<user> REPO_NAME=<repo>" >&2
  exit 1
fi

BASE="https://github.com/$OWNER/$REPO_NAME/releases/download/$TAG"

mkdir -p "$DEST"
cd "$DEST"

for asset in $(awk '{print $2}' "$HERE/vendor/SHA256SUMS.txt"); do
  if [ -n "${ASSET_DIR:-}" ]; then
    echo "copy   $asset"
    cp -f "$ASSET_DIR/$asset" .
  elif [ -s "$asset" ]; then
    echo "cached $asset"
  else
    echo "fetch  $asset"
    curl -fL --retry 3 -o "$asset" "$BASE/$asset"
  fi
done

echo "=== verifying sha256 ==="
sha256sum -c "$HERE/vendor/SHA256SUMS.txt"

echo "=== extracting sources ==="
tar -xf zmk-workspace-src.tar.gz
tar -xf zephyr-sdk-0.16.5-arm-zephyr-eabi.tar.gz
mkdir -p hosttools
tar -xf hosttools-dtc.tar.gz -C hosttools

echo "=== workspace layout ==="
mkdir -p .west vendor
cat > .west/config <<'EOF'
[manifest]
path = vendor
file = manifest.lock.yml

[zephyr]
base = zephyr
EOF
cp -f "$HERE/vendor/manifest.lock.yml" vendor/
rm -rf config
cp -a "$HERE/config" config

echo "=== python tooling ==="
python3 -m venv "$DEST/.venv"
"$DEST/.venv/bin/pip" install --quiet --upgrade pip wheel
if ! "$DEST/.venv/bin/pip" install --quiet -r "$HERE/vendor/pip.lock.txt"; then
  echo "pinned versions unavailable, falling back to zephyr/scripts/requirements.txt"
  "$DEST/.venv/bin/pip" install --quiet -r "$DEST/zephyr/scripts/requirements.txt"
fi

echo
echo "workspace ready in $DEST"
echo "next: $HERE/vendor/build.sh $DEST"

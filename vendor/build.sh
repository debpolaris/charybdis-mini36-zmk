#!/usr/bin/env bash
# Build the three uf2 images from a workspace prepared by restore.sh.
#
#   ./vendor/build.sh [WORKSPACE_DIR]        (default: ~/zmk-charybdis)
#
# Prints sha256 of every image; compare against firmware/SHA256SUMS.txt to
# confirm the result is bit-identical to what is committed here.
set -euo pipefail

DEST="${1:-$HOME/zmk-charybdis}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

export PATH="$DEST/.venv/bin:$DEST/hosttools/sysroots/x86_64-pokysdk-linux/usr/bin:$PATH"
export ZEPHYR_TOOLCHAIN_VARIANT=zephyr
export ZEPHYR_SDK_INSTALL_DIR="$DEST/zephyr-sdk-0.16.5"
export ZMK_CONFIG="$DEST/config"

# Zephyr bakes `git describe --abbrev=12 --always` into the boot banner. The
# vendored sources carry no .git, so hand it the same value the locked commit
# would have produced; otherwise the image differs by that string alone.
BUILD_VERSION="$(awk -F'\t' '$1=="zephyr"{print $5}' "$HERE/vendor/projects.lock.tsv" | cut -c1-12)"
if [ -z "$BUILD_VERSION" ]; then
  echo "could not read the locked zephyr revision from vendor/projects.lock.tsv" >&2
  exit 1
fi
echo "BUILD_VERSION=$BUILD_VERSION"

cd "$DEST"

for pair in left:charybdis_left right:charybdis_right reset:settings_reset; do
  target="${pair%%:*}"
  shield="${pair##*:}"
  echo "=== $target ($shield) ==="
  west build -s zmk/app -d "build/$target" -p always -b nice_nano_v2 -- \
    -DZMK_CONFIG="$ZMK_CONFIG" \
    -DSHIELD="$shield" \
    -DUSER_CONFIG_OR_MODULE_PATH="$ZMK_CONFIG" \
    -DCMAKE_PREFIX_PATH="$DEST/zephyr" \
    -DBUILD_VERSION="$BUILD_VERSION"
  cp -f "build/$target/zephyr/zmk.uf2" "zmk.$target.uf2"
done

sha256sum zmk.left.uf2 zmk.right.uf2 zmk.reset.uf2

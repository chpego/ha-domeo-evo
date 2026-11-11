#!/usr/bin/env bash
# Copy the domeo-evo-modbus library into the integration.
#
# The library is not on PyPI yet, so the integration ships its own copy.
# Usage: scripts/vendor_domeo_evo_modbus.sh <path to a domeo-evo-modbus checkout>
#
# The checkout must be clean, so VENDORED.md names the exact commit.
set -euo pipefail

src="${1:?usage: $0 <path to a domeo-evo-modbus checkout>}"
repo="$(cd "$(dirname "$0")/.." && pwd)"
dest="$repo/custom_components/domeo_evo/domeo_evo_modbus"

if [ -n "$(git -C "$src" status --porcelain)" ]; then
    echo "error: $src has uncommitted changes; commit them first" >&2
    exit 1
fi
commit="$(git -C "$src" rev-parse HEAD)"

rm -rf "$dest"
mkdir -p "$dest"
for file in "$src"/src/domeo_evo_modbus/*.py; do
    case "$(basename "$file")" in
        testing.py) ;;  # test helpers go to tests/ instead
        *) cp "$file" "$dest/" ;;
    esac
done
cp "$src/LICENSE" "$dest/LICENSE"
cp "$src/src/domeo_evo_modbus/testing.py" "$repo/tests/register_images.py"

cat > "$dest/VENDORED.md" <<MD
Vendored from domeo-evo-modbus at commit $commit.

Re-vendor with: scripts/vendor_domeo_evo_modbus.sh <path to a domeo-evo-modbus checkout>
MD
echo "Vendored domeo-evo-modbus $commit"

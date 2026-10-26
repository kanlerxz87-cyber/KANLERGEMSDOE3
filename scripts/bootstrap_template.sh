#!/usr/bin/env bash
# Fetch the immutable shared template without creating a fork or checking out a branch.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PIN=07806249f4ed3efe70b4fbf866183c32392b7853
DEST="${GEMS_TEMPLATE_DIR:-$ROOT/.cache/shared-template-$PIN}"
verify_tools() {
  (cd "$DEST" && sha256sum --check --status "$ROOT/data/shared-tool-hashes.txt") || {
    echo "Shared template tool hashes do not match the pinned manifest." >&2; exit 1;
  }
}
if [[ -d "$DEST" ]]; then
  if [[ -f "$DEST/.template-commit" ]] && [[ "$(cat "$DEST/.template-commit")" == "$PIN" ]]; then
    verify_tools; printf '%s\n' "$DEST"; exit 0
  fi
  if [[ -d "$DEST/.git" ]] && [[ "$(git -C "$DEST" rev-parse HEAD)" == "$PIN" ]] && [[ -z "$(git -C "$DEST" status --porcelain --untracked-files=no)" ]]; then
    verify_tools; printf '%s\n' "$DEST"; exit 0
  fi
  echo "Existing template is not clean at pin $PIN: $DEST" >&2; exit 1
fi
mkdir -p "$(dirname "$DEST")"
TMP="$(mktemp -d "$(dirname "$DEST")/.gems-template.XXXXXX")"
trap 'rm -rf "$TMP"' EXIT
curl --fail --location --retry 2 --silent --show-error \
  "https://codeload.github.com/buffedlizard55-lab/GEMSDOE32/tar.gz/$PIN" -o "$TMP/template.tar.gz"
mkdir "$TMP/tree"
tar -xzf "$TMP/template.tar.gz" -C "$TMP/tree" --strip-components=1
printf '%s\n' "$PIN" > "$TMP/tree/.template-commit"
mv "$TMP/tree" "$DEST"
verify_tools
printf '%s\n' "$DEST"

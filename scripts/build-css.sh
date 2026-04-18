#!/usr/bin/env bash
# Build Tailwind CSS for the app using the v3 standalone binary.
# Downloads the binary on first run if missing.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

BIN="bin/tailwindcss"
VERSION="v3.4.17"

# Resolve platform suffix for Tailwind's release binaries
resolve_platform() {
  local os arch
  os="$(uname -s)"
  arch="$(uname -m)"
  case "$os-$arch" in
    Darwin-arm64)  echo "macos-arm64" ;;
    Darwin-x86_64) echo "macos-x64" ;;
    Linux-x86_64)  echo "linux-x64" ;;
    Linux-aarch64) echo "linux-arm64" ;;
    *) echo "unsupported-platform: $os-$arch" >&2; exit 1 ;;
  esac
}

if [ ! -x "$BIN" ]; then
  PLATFORM="$(resolve_platform)"
  URL="https://github.com/tailwindlabs/tailwindcss/releases/download/${VERSION}/tailwindcss-${PLATFORM}"
  echo "→ Downloading Tailwind $VERSION for $PLATFORM..."
  mkdir -p bin
  curl -fsSL -o "$BIN" "$URL"
  chmod +x "$BIN"
fi

INPUT="app/static/css/input.css"
OUTPUT="app/static/css/tailwind-output.css"
MODE="${1:-build}"   # build | watch

case "$MODE" in
  build)
    echo "→ Building $OUTPUT (minified)"
    "$BIN" -i "$INPUT" -o "$OUTPUT" --minify
    SIZE=$(wc -c < "$OUTPUT")
    echo "✓ Wrote $OUTPUT ($SIZE bytes)"
    ;;
  watch)
    echo "→ Watching $INPUT (Ctrl+C to stop)"
    exec "$BIN" -i "$INPUT" -o "$OUTPUT" --watch
    ;;
  *)
    echo "Usage: $0 [build|watch]" >&2
    exit 1
    ;;
esac

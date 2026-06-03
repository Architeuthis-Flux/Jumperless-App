#!/usr/bin/env bash
# Open a terminal and run the pipx bootstrap script (macOS / Linux).
set -euo pipefail

BOOTSTRAP="${1:?bootstrap script path}"
BOOTSTRAP="$(cd "$(dirname "$BOOTSTRAP")" && pwd)/$(basename "$BOOTSTRAP")"

find_py() {
  if command -v python3 >/dev/null 2>&1; then
    echo "python3"
  elif command -v python >/dev/null 2>&1; then
    echo "python"
  else
    echo "python3"
  fi
}

case "$(uname -s)" in
  Darwin*)
    py="$(find_py)"
    esc="${BOOTSTRAP//\'/\\\'}"
    osascript <<EOF
tell application "Terminal"
  activate
  set w to do script ""
  delay 0.3
  do script "${py} '${esc}'" in w
  set bounds of front window to {80, 80, 1100, 720}
end tell
EOF
    ;;
  Linux*)
    py="$(find_py)"
    inner="$py $(printf '%q' "$BOOTSTRAP")"
    if command -v gnome-terminal >/dev/null 2>&1; then
      exec gnome-terminal -- bash -lc "$inner; echo; read -r -p 'Press Enter to close…' _"
    elif command -v konsole >/dev/null 2>&1; then
      exec konsole -e bash -lc "$inner; echo; read -r -p 'Press Enter to close…' _"
    elif command -v xfce4-terminal >/dev/null 2>&1; then
      exec xfce4-terminal -e bash -lc "$inner; echo; read -r -p 'Press Enter to close…' _"
    elif command -v xterm >/dev/null 2>&1; then
      exec xterm -geometry 120x40 -e bash -lc "$inner; echo; read -r -p 'Press Enter to close…' _"
    else
      exec bash -lc "$inner"
    fi
    ;;
  *)
    py="$(find_py)"
    exec bash -lc "$py $(printf '%q' "$BOOTSTRAP")"
    ;;
esac

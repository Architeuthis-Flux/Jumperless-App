#!/usr/bin/env bash
# Print the path to a universal (x86_64 + arm64) python.org interpreter.
# Exits 0 and prints the path on stdout, or exits 1 with a message on stderr.
#
# Preference: stable 3.11 → stable 3.12 → stable 3.13 → any universal framework Python.
# Override with JUMPERLESS_PYTHON=/path/to/python3

set -euo pipefail

is_universal_python() {
  local py="$1"
  local info
  info="$(lipo -info "$py" 2>/dev/null || true)"
  [[ "$info" == *x86_64* && "$info" == *arm64* ]]
}

is_beta_python() {
  local py="$1"
  "$py" -c 'import sys; raise SystemExit("b" in sys.version.lower())' 2>/dev/null
}

python_version_tuple() {
  local py="$1"
  "$py" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")'
}

score_python() {
  # Lower score wins. Stable 3.11 beats stable 3.12, etc.; betas sort last.
  local py="$1"
  local major minor micro beta penalty
  IFS=. read -r major minor micro <<<"$(python_version_tuple "$py")"
  penalty=0
  if is_beta_python "$py"; then
    penalty=1000
  fi
  if (( major < 3 || (major == 3 && minor < 11) )); then
    penalty=$((penalty + 500))
  fi
  echo $((penalty + major * 10000 + minor * 100 + micro))
}

if [[ -n "${JUMPERLESS_PYTHON:-}" ]]; then
  if [[ ! -x "$JUMPERLESS_PYTHON" ]]; then
    echo "JUMPERLESS_PYTHON is not executable: $JUMPERLESS_PYTHON" >&2
    exit 1
  fi
  if ! is_universal_python "$JUMPERLESS_PYTHON"; then
    echo "JUMPERLESS_PYTHON is not universal (needs x86_64 + arm64): $JUMPERLESS_PYTHON" >&2
    lipo -info "$JUMPERLESS_PYTHON" >&2 || true
    exit 1
  fi
  echo "$JUMPERLESS_PYTHON"
  exit 0
fi

best_py=""
best_score=999999
framework_root="/Library/Frameworks/Python.framework/Versions"
if [[ -d "$framework_root" ]]; then
  for py in "$framework_root"/*/bin/python3; do
    [[ -x "$py" ]] || continue
    is_universal_python "$py" || continue
    score="$(score_python "$py")"
    if (( score < best_score )); then
      best_score=$score
      best_py="$py"
    fi
  done
fi

if [[ -n "$best_py" ]]; then
  echo "$best_py"
  exit 0
fi

echo "No universal python.org interpreter found under $framework_root" >&2
echo "Run: ./Scripts/setup_universal_python.sh" >&2
exit 1

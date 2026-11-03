#!/usr/bin/env bash
set -euo pipefail
umask 077

case "$(uname -m)" in
  x86_64)
    asset=agent-browser-linux-x64
    expected=d258593db4899577748a4b2a671a315f76f07a4553ba7fbbeaa95f0d16a4aaa8
    ;;
  aarch64)
    asset=agent-browser-linux-arm64
    expected=54eedbcaedcbd8b49f840098ea85dda653af0a036e28609b526ece068de6c0ab
    ;;
  *)
    printf '지원하지 않는 아키텍처입니다. 원문은 curl로 확인하세요.\n' >&2
    exit 1
    ;;
esac

mkdir -p /tmp/ab
target=/tmp/ab/agent-browser

# 스킬 저장소에 함께 넣은 실행 파일을 먼저 씁니다(네트워크 없이 설치, 같은 SHA-256 검증).
bundled="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)/../bin/$asset"
if [[ -f "$bundled" ]] && command -v sha256sum >/dev/null 2>&1; then
  actual=$(sha256sum "$bundled"); actual=${actual%% *}
  if [[ "$actual" == "$expected" ]] && cp "$bundled" "$target" && chmod +x "$target"; then
    printf '%s\n' "$target"
    exit 0
  fi
  rm -f "$target"
  printf '함께 넣은 실행 파일의 SHA-256이 맞지 않아 다운로드를 시도합니다.\n' >&2
fi

url="https://github.com/vercel-labs/agent-browser/releases/download/v0.39.0/$asset"
if curl --fail --location --silent --show-error --connect-timeout 10 --max-time 90 --output "$target" "$url"; then
  if ! command -v sha256sum >/dev/null 2>&1; then
    rm -f "$target"
    printf 'sha256sum이 없어 다운로드 파일을 검증할 수 없습니다.\n' >&2
    exit 1
  fi
  if ! actual=$(sha256sum "$target"); then
    rm -f "$target"
    printf 'SHA-256 계산에 실패했습니다.\n' >&2
    exit 1
  fi
  actual=${actual%% *}
  if [[ "$actual" != "$expected" ]]; then
    rm -f "$target"
    printf 'SHA-256 불일치: 다운로드 파일을 삭제했습니다.\n' >&2
    exit 1
  fi
  if ! chmod +x "$target"; then
    rm -f "$target"
    printf '실행 권한을 설정하지 못했습니다.\n' >&2
    exit 1
  fi
  printf '%s\n' "$target"
  exit 0
fi

rm -f "$target"
if command -v npm >/dev/null 2>&1 && (cd /tmp/ab && npm install agent-browser@0.39.0 >&2); then
  fallback=/tmp/ab/node_modules/.bin/agent-browser
  if [[ -x "$fallback" ]] && "$fallback" --version >/dev/null 2>&1; then
    printf '%s\n' "$fallback"
    exit 0
  fi
fi
printf '릴리스 다운로드와 로컬 npm 설치가 모두 불가합니다. 원문은 curl로만 확인하세요.\n' >&2
exit 1

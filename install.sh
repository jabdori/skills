#!/usr/bin/env bash
# 개인 스킬과 공용 자료(_shared)를 함께 설치합니다. 사용: bash install.sh [대상 폴더]
set -euo pipefail
src="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)/personal-skills"
dest="${1:-$HOME/.agents/skills}"
mkdir -p "$dest"
cp -R "$src"/. "$dest"/
missing=0
for need in _shared/personal-workflow.md _shared/templates/data-map.md _shared/scripts/presubmit.py exam-start/SKILL.md exam-start/rules.md; do
  [[ -e "$dest/$need" ]] || { echo "누락: $dest/$need" >&2; missing=1; }
done
[[ $missing == 0 ]] || exit 1
count=$(find "$dest" -mindepth 2 -maxdepth 2 -name SKILL.md | wc -l | tr -d ' ')
# 화면 확인 도구 agent-browser도 함께 설치합니다(리눅스에서만, 실패해도 스킬 설치는 유지).
browser=""
if [[ "$(uname -s)" == Linux ]]; then
  browser=$(bash "$dest/_shared/scripts/get-agent-browser.sh" 2>/dev/null) || browser=""
fi
echo "설치 완료: ${dest} (스킬 ${count}개, 공용 자료 포함). codex를 새로 시작하세요."
if [[ -n "$browser" ]]; then echo "화면 확인 도구: ${browser} (agent-browser)"; else echo "화면 확인 도구 agent-browser는 설치하지 못했습니다(리눅스가 아니거나 검증 실패)."; fi

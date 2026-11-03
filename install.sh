#!/usr/bin/env bash
# 개인 스킬과 공용 자료(_shared)를 함께 설치합니다. 사용: bash install.sh [대상 폴더]
set -euo pipefail
src="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)/personal-skills"
dest="${1:-$HOME/.agents/skills}"
mkdir -p "$dest"
cp -R "$src"/. "$dest"/
missing=0
for need in _shared/personal-workflow.md _shared/templates _shared/scripts/presubmit.py exam-start/SKILL.md exam-start/rules.md; do
  [[ -e "$dest/$need" ]] || { echo "누락: $dest/$need" >&2; missing=1; }
done
[[ $missing == 0 ]] || exit 1
count=$(find "$dest" -mindepth 2 -maxdepth 2 -name SKILL.md | wc -l | tr -d ' ')
echo "설치 완료: ${dest} (스킬 ${count}개, 공용 자료 포함). codex를 새로 시작하세요."

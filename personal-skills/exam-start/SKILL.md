---
name: exam-start
description: Cofa 응시를 시작할 때 한 번 사용합니다. 기존 AGENTS.md를 보존하며 작업 규칙과 확인된 프로젝트 정보, 담당자 질문안을 준비합니다.
---

# 응시 시작 준비

작업 폴더에서 한 번 수행합니다. 제품 코드는 수정하지 않습니다.

`AGENTS.md`를 고치기 전에 이 `SKILL.md`가 있는 폴더 기준의 [로컬 커밋 규칙](../_shared/personal-workflow.md#로컬-커밋)으로 시작 상태를 기록합니다: Git이 없으면 `git init`하고, `HEAD` 커밋이 없거나 기존 커밋 뒤 미커밋 변경이 있으면 `chore: 과제 시작 상태`와 한국어 본문으로 커밋하며, 변경 없는 기존 HEAD는 시작 기준으로 삼습니다. 커밋 전에는 저장소 루트에 실제로 있고 과제가 제공하지 않은 홈 설정 점 폴더(`.agents/`, `.codex/`, `.config/`, `.cache/` 등)만 그 저장소의 `.git/info/exclude`에 루트 고정 패턴으로 추가합니다.

1. 기존 `AGENTS.md`를 먼저 읽고 시스템 환경 정보와 사용자 추가 규칙을 짧게 알려 줍니다. 없으면 새 파일을 만듭니다. 기존 내용은 지우거나 일반 양식으로 교체하지 않습니다.
2. [작업 규칙 원본](rules.md)의 각 줄을 기존 지침과 의미로 대조해 겹치거나 충돌하는 줄은 건너뛰고, 나머지만 `AGENTS.md` 맨 아래에 덧붙입니다. 제목도 중복시키지 않으며 이미 덧붙인 규칙은 다시 넣지 않습니다. 충돌은 조용히 덮지 말고 알립니다.
3. `AGENTS.md`를 읽거나 만든 뒤 `## 이 프로젝트`에는 `docs/README.md` 링크만 짧게 두고 시스템 기본과 사용자 규칙은 보존합니다. 시작 커밋 SHA, 필수 산출물·수정 금지 파일, 확인된 실행·검사 명령과 포트는 [문서 지도](../_shared/personal-workflow.md#문서-지도)의 `docs/task/start-path.md`에 적으며 모르면 `못 찾음`으로 표시하고, 이 `SKILL.md` 상위의 `_shared` 절대 경로가 실제로 있는지도 확인해 같은 문서에 남깁니다.
4. [과제 지시문 정리표](../_shared/personal-workflow.md#과제-지시문-정리표)를 배경 한 단락 → 일상 비유 한 줄 → ASCII 흐름 그림 → 정리표 → 용어 풀이 순서로 보여 주고, [쉬운 말 기준](../_shared/personal-workflow.md#쉬운-말-기준)으로 `docs/task/overview.md`에 적습니다. 번호별 요구는 [인수 점검표](../_shared/templates/acceptance.md)로 `docs/requirements/acceptance.md`에 옮기고, 담당자 질문은 한 문장에 하나씩 영향 큰 5~7개부터 제시하며 제공 자료의 업무 요구는 [brief](../brief/SKILL.md)에 따라 기록합니다.
5. 정리표 다음에는 README·자료 사전을 읽고 [data_profile.py](../_shared/scripts/data_profile.py)를 제공 CSV 폴더에 실행해 실제 행으로 연결을 확인합니다. [데이터 지도 양식](../_shared/templates/data-map.md)의 순서대로 `docs/assets/data-relations.svg` 관계도와 한 건 따라가기부터 `docs/task/data-map.md`에 만들고, 사용자에게 **“관계도와 한 건 따라가기부터 보세요”**라고 안내합니다. 연결 후보나 뜻이 미확인이면 `추정(담당자 확인)`으로 표시하고, 그 한 건의 손계산 결과를 걷는 뼈대의 첫 테스트로 씁니다. 단계별 입력→처리→출력·계약 검사기·우선순위·시간은 `docs/task/start-path.md`에 두고, 만든 문서는 `docs/README.md`에 연결합니다.

`AGENTS.md`와 `docs/`의 정리 문서를 만든 뒤 [로컬 커밋 규칙](../_shared/personal-workflow.md#로컬-커밋)으로 `docs: 작업 규칙과 과제 정리표`와 한국어 본문을 사용해 로컬 커밋합니다.

시작 경로 끝에 한 줄로 알립니다: **AGENTS.md를 직접 읽고, DMs의 담당자 수를 확인한 뒤, 질문은 본인이 직접 보내 주세요.**

---
name: shared-resources
description: 개인 스킬(exam-start·brief·plan·build·verify·explain·learn 등)이 참조하는 공용 지침·템플릿·점검 스크립트 묶음입니다. 직접 호출하지 않습니다. 개인 스킬을 설치할 때 이 폴더를 `_shared`라는 이름 그대로 함께 설치해야 다른 스킬의 링크와 스크립트가 동작합니다.
---

# 공용 자료

다른 스킬이 `../_shared/` 상대 경로로 읽는 자료입니다. 이 스킬만 따로 호출하지 않습니다.

- `personal-workflow.md`: 공통 작업·문서 지침
- `templates/`: 과제 정리(task-overview)·데이터 지도(data-map)·요구 근거(requirements-evidence)·인수 점검(acceptance)·결정 기록(adr, adr-index)·코드 지도(code-map)·쉬운 설명 카드(concept-card)·조사 근거(research-evidence) 양식
- `scripts/`: 제출 전 점검(`presubmit.py`)과 도구 설치 스크립트

설치 폴더 이름이 `_shared`가 아니면 다른 스킬의 링크가 깨집니다. 빠져 있으면 저장소의 `install.sh`로 다시 설치합니다.

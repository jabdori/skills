# 개인 스킬셋 (Cofa 응시 환경용)

Codex에서 쓰는 **12개 스킬**과 [공통 지침](_shared/personal-workflow.md)입니다. 업무 담당자 에이전트에게 확인할 사실과 참가자의 판단을 구분하고, 그 근거가 구현·검증·제출 문서·사후 설명까지 이어지게 합니다. 별도 서버·관리 도구·외부 실행 의존성은 없습니다.

| 스킬 | 맡기는 요청 |
|---|---|
| [my-research](my-research/SKILL.md) | 근거 조사와 준비 판단 |
| [my-brief](my-brief/SKILL.md) | 목적·요구·업무 예외의 모호함 해소. 담당자에게 물을 것과 사용자가 정할 것을 구분 |
| [my-orient](my-orient/SKILL.md) | 과제 환경·기존 코드의 실제 현황 파악과 작업 재개 |
| [my-plan](my-plan/SKILL.md) | 접근·순서, 요구 근거가 붙은 명세와 작업 단위 |
| [my-build](my-build/SKILL.md) | 구현·검증, 독립 작업의 병렬 처리와 통합 |
| [my-verify](my-verify/SKILL.md) | 기술적 동작과 업무 요구 충족을 나눈 검토·판정 |
| [my-explain](my-explain/SKILL.md) | 결정 설명, 제출 문서, 인계, 사후 질의 대비 정리 |
| [my-debug](my-debug/SKILL.md) | 원인 불명 오류의 추적·복구 |
| [my-ux](my-ux/SKILL.md) | 사용자의 이해·조작·완료 문제 개선 |
| [my-init](my-init/SKILL.md) | 기존 프로젝트의 작업 명령·경계와 `AGENTS.md` 정비 |
| [my-wait](my-wait/SKILL.md) | 이해가 끊긴 지점에서 멈추고 배경·용어·예시로 재설명 |
| [my-retro](my-retro/SKILL.md) | 실제 시행착오를 다음 작업의 지침·검증에 반영 |

자연어로 요청하거나 `$my-build`처럼 역할을 지정합니다. 12개를 순서대로 실행하지 않으며 작은 수정은 해당 작업만 끝냅니다.

## 두는 위치

12개 `my-*` 폴더와 `_shared`를 **같은 스킬 폴더 바로 아래에 함께** 둡니다(`_shared` 상대 링크 유지). Codex는 작업 폴더의 `.agents/skills`와 사용자 폴더의 `~/.agents/skills`에서 스킬을 찾습니다. 작업 폴더를 제출물로 깨끗하게 두려면 `~/.agents/skills`를 씁니다.

```bash
mkdir -p ~/.agents/skills && cp -R personal-skills/my-* personal-skills/_shared ~/.agents/skills/
```

`codex`를 새로 시작한 뒤 "사용 가능한 my- 스킬 이름만 알려줘"로 인식을 확인합니다.

## 필요한 상황

| 상황 | 사용하는 양식·행동 |
|---|---|
| “담당자에게 뭘 물어봐야 해?” | [정보 출처와 질문 대상](_shared/personal-workflow.md#정보-출처와-질문-대상): 업무 사실은 담당자·자료, 구현 사실은 코드, 우선순위는 사용자 → 답변·결정·가정을 구분해 명세·검증·설명까지 연결 |
| “이 기능을 명세와 작업으로 정리해줘” | [명세·작업 양식](_shared/spec-and-tickets.md) |
| “독립 작업은 동시에 구현해줘” | [병렬 구현·통합](_shared/parallel-delivery.md). 토큰·시간이 평가되면 꼭 필요한 경우만 |
| “합쳐도 되는지 검토해줘” | [검토·PR 양식](_shared/review-and-pr.md) |
| “주문 완료와 결제 완료는 같은 뜻이야?” | [용어와 의미 지도](_shared/personal-workflow.md#용어와-의미-지도) |

검사 결과는 [공통 판정 기준](_shared/personal-workflow.md#실제-변경과-검사-근거)으로 확인합니다. Python 표준 `unittest`에서 수집 누락·전체 생략을 구분해야 할 때만 [검사 보조](my-verify/scripts/verify_unittest.py)를 씁니다.

지침은 행동 기준이며 자동 차단 장치는 아닙니다.

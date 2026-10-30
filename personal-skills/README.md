# 개인 스킬셋 (Cofa 응시 환경용)

Codex에서 쓰는 **14개 스킬**과 [공통 지침](_shared/personal-workflow.md)입니다. 업무 담당자 에이전트에게 확인할 사실과 참가자의 판단을 구분하고, 그 근거가 구현·검증·제출 문서·사후 설명까지 이어지게 합니다. 별도 서버·관리 도구·외부 실행 의존성은 없습니다.

| 스킬 | 맡기는 요청 |
|---|---|
| [research](research/SKILL.md) | 근거 조사와 준비 판단 |
| [brief](brief/SKILL.md) | 목적·요구·업무 예외의 모호함 해소. 담당자에게 물을 것과 사용자가 정할 것을 구분 |
| [orient](orient/SKILL.md) | 과제 환경·기존 코드의 실제 현황 파악과 작업 재개 |
| [plan](plan/SKILL.md) | 접근·순서, 요구 근거가 붙은 명세와 작업 단위 |
| [build](build/SKILL.md) | 구현·검증, 독립 작업의 병렬 처리와 통합 |
| [verify](verify/SKILL.md) | 기술적 동작과 업무 요구 충족을 나눈 검토·판정 |
| [explain](explain/SKILL.md) | 결정 설명, 제출 문서, 인계, 사후 질의 대비 정리 |
| [learn](learn/SKILL.md) | 제출 전·인계 전 실제 동작을 익히는 학습 문서와 예상 질문 |
| [debug](debug/SKILL.md) | 원인 불명 오류의 추적·복구 |
| [ux](ux/SKILL.md) | 사용자의 이해·조작·완료 문제 개선 |
| [init](init/SKILL.md) | 기존 프로젝트의 작업 명령·경계와 `AGENTS.md` 정비 |
| [exam-start](exam-start/SKILL.md) | Cofa 응시 시작 한 번: 시스템 지침 보존·규칙 추가·과제 파악. [rules.md](exam-start/rules.md)가 원본(clone이 막히면 이 내용을 직접 입력) |
| [wait](wait/SKILL.md) | 이해가 끊긴 지점에서 멈추고 배경·용어·예시로 재설명 |
| [retro](retro/SKILL.md) | 실제 시행착오를 다음 작업의 지침·검증에 반영 |

자연어로 요청하거나 `$build`처럼 역할을 지정합니다. 14개를 순서대로 실행하지 않으며 작은 수정은 해당 작업만 끝냅니다.

## 두는 위치

14개 스킬 폴더와 `_shared`를 **같은 스킬 폴더 바로 아래에 함께** 둡니다(`_shared` 상대 링크 유지). Codex는 작업 폴더의 `.agents/skills`와 사용자 폴더의 `~/.agents/skills`에서 스킬을 찾습니다. 작업 폴더를 제출물로 깨끗하게 두려면 `~/.agents/skills`를 씁니다.

```bash
mkdir -p ~/.agents/skills && cp -R personal-skills/* ~/.agents/skills/
```

`codex`를 새로 시작한 뒤 "사용 가능한 스킬에 brief·build·verify가 있는지 알려줘"로 인식을 확인합니다.

## 필요한 상황

| 상황 | 사용하는 양식·행동 |
|---|---|
| “업무 요구가 있는 과제를 진행해줘” | [요구 근거표](_shared/templates/요구근거.md)를 처음부터 기본으로 사용하고 출처·구현·검증·상태를 갱신. 과제 지정 제출 문서가 있으면 그 안에 둠 |
| “깊게 조사하거나 만든 화면을 확인해줘” | 심층 조사에만 [조사 근거표](_shared/templates/조사근거.md)를 쓰고, 필요한 원문·자기 화면 확인에는 [agent-browser 참고](_shared/agent-browser.md) |
| “이 기능을 명세와 작업으로 정리해줘” | [명세·작업 양식](_shared/spec-and-tickets.md) |
| “독립 작업은 동시에 구현해줘” | [병렬 구현·통합](_shared/parallel-delivery.md). 토큰·시간이 평가되면 꼭 필요한 경우만 |
| “합쳐도 되는지 검토해줘” | [검토·PR 양식](_shared/review-and-pr.md) |
| “제출 전 설명·생성물을 확인해줘” | 근거표에서 시작해 필요한 경우 [결정 문서](_shared/templates/DECISIONS.md)·[설명 카드](_shared/templates/설명카드.md)와 [읽기 전용 점검](_shared/scripts/presubmit.py) |
| “주문 완료와 결제 완료는 같은 뜻이야?” | [용어와 의미 지도](_shared/personal-workflow.md#용어와-의미-지도) |

검사 결과는 [공통 판정 기준](_shared/personal-workflow.md#실제-변경과-검사-근거)으로 확인합니다. Python 표준 `unittest`에서 수집 누락·전체 생략을 구분해야 할 때만 [검사 보조](verify/scripts/verify_unittest.py)를 씁니다.

지침은 행동 기준이며 자동 차단 장치는 아닙니다.

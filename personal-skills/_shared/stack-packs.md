# 시험 시작 때 설치하는 스택 팩

저장소 루트에서 실행합니다. 설치기와 `vendor`를 포함한 `_shared` 폴더가 함께 있어야 합니다.

```bash
bash _shared/scripts/install-stack-pack.sh go
export PATH="$HOME/.local/go/bin:$PATH"
export GOTOOLCHAIN=local

bash _shared/scripts/install-stack-pack.sh react
# 여러 팩도 한 번에 요청할 수 있습니다.
bash _shared/scripts/install-stack-pack.sh python node
```

| 팩 | 설치하거나 확인하는 것 | 언제 도움이 되나요? |
|---|---|---|
| common | find-skills | 준비한 스킬로 부족할 때 추가 스킬을 찾는 예비 도구입니다. |
| go | Go 1.27.3, use-modern-go, 지침 CLI 0.1.1, 공통 스킬 | Go 코드를 만들거나 고칠 때 프로젝트의 Go 버전에 맞는 언어·표준 라이브러리 사용법을 확인합니다. |
| react | React 성능·컴포넌트 조합·웹 화면 점검 스킬과 shadcn, 공통 스킬 | React 화면을 구현하고 데이터 요청·재렌더링·컴포넌트 구성·접근성을 검토할 때 사용합니다. |
| python | 공통 스킬, 기존 Python 3 버전 확인 | Python 작업을 시작할 때 실행 환경을 확인하고 필요하면 전용 스킬을 찾습니다. |
| node | 공통 스킬, 기존 Node.js 버전 확인 | Node 작업을 시작할 때 실행 환경을 확인하고 필요하면 전용 스킬을 찾습니다. |

Python·Node 전용 스킬은 이번 요청에서 지정되지 않아 임의로 추가하지 않았습니다. 이 두 런타임과 React 프로젝트의 npm 패키지는 설치하지 않습니다. 연습 이미지의 Python 3.11.2와 Node.js 22.23.2를 확인했습니다. 설치기 자체에도 Python 3가 필요합니다.

## 설치 위치와 기존 파일

- 모든 스킬은 공식 Codex 사용자 발견 경로인 `$HOME/.agents/skills/<스킬 이름>/SKILL.md`에 실제 파일로 설치합니다.
- Go 팩은 Linux amd64와 arm64를 지원합니다. 최초 설치 때 공식 go.dev에서 고정 버전 1.27.3을 내려받고, 고정 SHA-256으로 검증한 뒤 `$HOME/.local/go`에 설치합니다. sudo는 쓰지 않습니다. tarball은 저장소에 넣지 않습니다.
- 현재 셸의 PATH 적용은 위 명령으로 합니다. GOTOOLCHAIN=local은 프로젝트에서 다른 Go 도구 체인을 자동 다운로드하지 않게 합니다.
- Go 지침 CLI는 원본 스킬의 실행기가 찾는 `$XDG_CACHE_HOME/go-modern-guidelines/v0.1.1`에 둡니다. XDG_CACHE_HOME이 없으면 `$HOME/.cache`를 사용합니다.
- Codex 설정과 셸 시작 파일은 수정하지 않습니다. 스킬 설치와 PATH 적용 후 사용할 Codex 세션을 시작합니다.
- 같은 내용이면 재실행해도 그대로 사용합니다. 기존 스킬이나 Go 설치가 다른 내용이면 덮어쓰지 않습니다. Go 설치가 실패하면 아래 대체 스택 안내 한 줄만 출력하고 종료 코드 1을 반환합니다.
- 요청한 스킬·실행 파일을 준비하고 검사한 뒤 설치합니다. 다운로드·해시·기존 설치 충돌로 사전 준비가 실패하면 새 스킬을 일부만 설치하지 않습니다.

## 고정 원본과 라이선스

출처는 전체화면에서 외부 페이지가 열리지 않도록 이름으로만 적습니다. 전체 고정 커밋·파일별 해시·공식 Go 압축 파일 해시는 `stack-packs.lock.json`에 있습니다.

| 출처 이름 | 확인한 라이선스 | 배포 방식 |
|---|---|---|
| vercel-labs/skills — find-skills | 루트 LICENSE의 MIT | `vendor/find-skills`에 원본 스킬·LICENSE·ThirdPartyNoticeText.txt 동봉 |
| JetBrains/go-modern-guidelines — use-modern-go | 루트 LICENSE의 Apache-2.0 | `vendor/use-modern-go`에 스킬과 실행기·LICENSE 동봉 |
| shadcn-ui/ui — skills/shadcn | 루트 LICENSE.md의 MIT | `vendor/shadcn`에 하위 자료 전체와 LICENSE.md 동봉 |
| vercel-labs/agent-skills — react-best-practices, composition-patterns, web-design-guidelines | 저장소 LICENSE 파일 없음 | 저장소에 동봉하지 않고 설치 현장에서 고정 Git 커밋을 내려받음 |
| Go 공식 배포본 | BSD-3-Clause | 공식 사이트에서 현장 다운로드·해시 검증. `vendor/go-toolchain`에는 LICENSE만 보관 |
| JetBrains 지침 CLI의 golang.org/x/mod 의존성 | BSD-3-Clause | 지침 실행 파일의 라이선스·특허 고지를 runtime/licenses에 동봉 |

확인일은 2026-11-03입니다. find-skills는 `7a5e920bead4`, Go 스킬은 `155dc7ca10da`, shadcn은 `4aaea19d9cff`, Vercel 원격 스킬은 `1a2c79d4e6c4` 커밋입니다. 설치 중 최신 브랜치로 바꾸지 않습니다.

Vercel의 React·composition 스킬 머리말에는 MIT 표기가 있지만 저장소에는 LICENSE 파일이 없고 web-design-guidelines 머리말에도 라이선스 표기가 없습니다. 이번 팩은 요청한 보수적인 기준에 따라 세 스킬 모두 동봉하지 않습니다. 고정 커밋을 Git으로 확인한 뒤 필요한 스킬 폴더만 사용자 캐시에 보관합니다.

Go 지침 CLI는 원본 실행기의 VERSION에 맞춘 v0.1.1, 커밋 `937827b86eef`로 빌드했습니다. 공식 Go 1.27.3으로 CGO 없이 Linux 두 아키텍처용 실행 파일을 만들었으며 모듈 버전·체크섬·빌드 옵션을 고정 원본 목록에 남겼습니다. 스킬과 실행기 원문은 수정하지 않았습니다. 실행 파일에는 해당 CLI와 Go·x/mod의 라이선스·특허 고지가 함께 설치됩니다.

use-modern-go는 SKILL.md에서 `list`·`explain` 명령 실행을 요구합니다. 실행 파일이 없으면 원본 실행기가 첫 사용 때 `go install`로 다시 빌드합니다. 문서만으로 동작하는 스킬이 아니므로 두 Linux 아키텍처용 지침 CLI 약 9.3MiB는 유지했습니다. Go SDK tarball 두 개는 제거했습니다. 남은 vendor의 파일 합계는 9,944,088바이트(약 9.48MiB), 디스크 사용량은 약 9.6MiB입니다.

## 인터넷이 없을 때

```bash
bash _shared/scripts/install-stack-pack.sh go --offline
bash _shared/scripts/install-stack-pack.sh common --offline
```

공통·Python·Node 팩은 기존 런타임이 있으면 최초 설치도 오프라인으로 됩니다. Go는 이미 설치된 고정 SDK 또는 이전 다운로드 캐시가 있어야 오프라인 설치가 됩니다. SDK 최초 설치에는 인터넷이 필요합니다. 다운로드 캐시는 사용자 홈의 `.cache/stack-packs/downloads`에만 두며 저장소로 다시 복사하지 않습니다.

다운로드·해시 검증·설치 준비가 실패하면 다음 한 줄만 출력합니다. Node나 Python을 대신 자동 설치하거나 스택을 바꾸지는 않습니다.

```text
Go 설치 실패 — 이미 설치된 Node.js 22나 Python 3.11 스택을 고려
```

Go 지침 CLI는 동봉되어 있으므로 SDK 설치 뒤에는 지침 첫 호출을 위해 모듈을 다시 받지 않습니다.

React의 최초 설치는 인터넷이 필요합니다. 온라인 설치로 고정 원본을 받은 뒤에는 같은 사용자 캐시로 `react --offline` 재설치가 됩니다. 캐시가 없거나 변조됐으면 실패하고 기존 스킬은 유지합니다. 여러 팩을 함께 요청했는데 React 원본을 준비하지 못하면 다른 팩도 설치 단계로 넘어가지 않습니다.

스킬 파일의 오프라인 설치와 실제 활용은 구분합니다. find-skills의 검색, shadcn의 CLI·문서 조회, web-design-guidelines의 외부 기준 조회 등은 사용 중 인터넷이 필요할 수 있습니다. 이 팩은 프로젝트 패키지나 외부 웹 문서 전체를 미리 내려받지 않습니다.

## 연습 이미지에서 측정한 결과

`cofa-practice:local`, Linux arm64, UID 1001, Codex 0.163.0에서 확인합니다. 각 최초 설치는 새 일회용 컨테이너이며 시간에는 컨테이너 생성이 포함되지 않습니다. Go는 공식 다운로드 시간이 추가되어 네트워크 상태에 따라 달라집니다.

이전 동봉 tarball 방식의 온라인·오프라인 설치 시간은 현재 설치기에 적용하지 않습니다. 현재 측정표는 아래에 기록하며 원자료는 `stack-pack-results.json`에 있습니다.

| 팩 | 최초 온라인 | 최초 네트워크 차단 | 확인 결과 |
|---|---:|---:|---|
| common | 0.161초 | 0.082초 | 설치 성공 |
| go | 5.135초 | 0.093초 실패 안내 | 공식 다운로드·SHA-256·컴파일러·지침 CLI 확인 |
| react | 0.759초 | 0.089초 실패 안내 | 캐시 없는 오프라인 최초 설치 불가 |
| python | 0.090초 | 0.110초 | 설치 성공 |
| node | 0.115초 | 0.116초 | 설치 성공 |

Go의 이번 최초 온라인 설치는 다운로드를 포함해 5.135초였습니다. 3초 이내라는 수치는 이번 환경에서 재현하지 못했습니다.
go는 온라인 설치 후 네트워크를 분리하고 설치 폴더를 지운 재설치에서 사용자 캐시로 2.868초에 성공했습니다.
react는 온라인 설치 후 네트워크를 분리하고 설치 폴더를 지운 재설치에서 사용자 캐시로 0.101초에 성공했습니다.

단위 검사 16개가 통과했고, 일회용 컨테이너 14개 시나리오에서 설치 성공 또는 요청한 실패 안내·기존 파일 보존을 확인했습니다. 최초 온라인 측정의 앞선 반복 실행 중 Go 설치 실패 1회도 관측했으며 요청한 안내 한 줄만 출력했습니다. 실패 원인은 재현되지 않아 확정하지 않았습니다.

Go는 온라인에서도 설치 실패 시 안내 한 줄과 부분 설치 없음을 검사합니다. 따라서 설치 성공과 안내를 확인한 실패를 결과의 exit_code로 구별합니다. Go 오프라인 재설치는 온라인 설치 때 받은 사용자 캐시를 남기고 SDK·스킬 설치 폴더를 지운 뒤 확인합니다.

Codex 확인은 요청 범위에 맞춰 사용자 발견 경로의 SKILL.md, 이름·설명·파일 소유자와 설정 파일 미변경만 확인합니다. codex exec나 모델 요청은 사용하지 않습니다. Linux amd64는 공식 해시 고정과 CLI 교차 빌드까지 확인했으며 arm64 실행 결과로 대신하지 않습니다.

## 검사를 다시 실행하기

Linux 연습 컨테이너에 `_shared`를 `/pack`으로 읽기 전용 연결한 뒤 다음을 실행합니다.

```bash
python3 -B -m unittest discover -s /pack/scripts -p test_install_stack_pack.py -v
```

실제 컨테이너 측정은 저장소 루트의 호스트에서 실행합니다.

```bash
python3 -B _shared/scripts/test_stack_pack_container.py --image cofa-practice:local --output _shared/stack-pack-results.json
```

테스트는 일회용 컨테이너만 만들고 종료 시 삭제합니다. 실제 홈의 스킬·인증·Codex 설정은 연결하지 않습니다. 단위 검사 16개는 해시 불일치, 캐시 변조, 기존 파일 보존, 압축 경로, 네트워크 실패와 재설치를 확인합니다. macOS에서 단위 검사만 실행하면 Linux Go 설치 사례 여섯 개는 건너뜁니다.

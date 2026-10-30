# 원문·화면 확인 도구

[agent-browser](https://github.com/vercel-labs/agent-browser)는 Apache-2.0 네이티브 CLI이며 기본 실행은 headless입니다. 이미 설정된 검색·fetch MCP가 있으면 그것을 쓰고 새 도구를 설치하지 않습니다.

설치가 필요하면 [고정 버전 설치 스크립트](scripts/get-agent-browser.sh)를 `bash`로 실행합니다. v0.39.0 릴리스의 Linux 실행 파일을 `/tmp/ab`에 받아 SHA-256을 검증하고 경로를 출력하며, 다운로드 실패에만 npm이 있으면 같은 버전을 `/tmp/ab`에 설치·실행 확인합니다. 둘 다 안 되면 원문은 `curl`로만 확인합니다. 시험 환경은 x86_64 Debian 12·Node 22.23.2이고 npm 존재 여부는 확인 전입니다. [npm 배포본은 Node 24 이상](https://github.com/vercel-labs/agent-browser/blob/v0.39.0/package.json)을 요구하므로 대체 설치 성공을 가정하지 않습니다.

```bash
bash <스킬셋 경로>/_shared/scripts/get-agent-browser.sh
export PATH="/tmp/ab:/tmp/ab/node_modules/.bin:$PATH"
```

`agent-browser install`로 Chrome을 내려받지 않습니다. 기존 Chromium 자동 감지를 먼저 쓰고 실패할 때만 `--executable-path`로 이미 있는 브라우저를 지정합니다.

- **research:** `agent-browser read <url>`로 브라우저 없이 원문 본문을 읽습니다. 없거나 막히면 `curl`로 원문을 확인합니다.
- **verify·ux:** 자신이 만든 화면 과제의 서버만 `agent-browser open <url>` → `agent-browser snapshot -i` → 필요한 `agent-browser click @ref` → `agent-browser screenshot /tmp/own-app.png` 순서로 확인하고, 스크린샷 경로와 실제 확인한 흐름을 보고합니다.
- **금지:** Cofa 응시·감독 화면, 메신저, 제출 흐름과 데스크톱을 조작하지 않습니다(Computer Use 금지). `AI_GATEWAY_API_KEY`를 쓰는 AI 채팅 기능도 사용하지 않습니다. 검색어·외부 요청에는 과제 코드·데이터·담당자 답을 넣지 말고 일반 기술 질문으로 바꿉니다.

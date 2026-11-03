# 원문·화면 확인 도구

[agent-browser](https://github.com/vercel-labs/agent-browser)는 Apache-2.0 네이티브 CLI이며 기본 실행은 headless입니다. 원문 조사에는 이미 설정된 검색·fetch MCP를 쓸 수 있지만, 자기 화면의 클릭 확인에는 이 도구를 씁니다.

설치가 필요하면 [고정 버전 설치 스크립트](scripts/get-agent-browser.sh)를 `bash`로 실행합니다. 함께 넣은 v0.39.0 Linux 실행 파일을 SHA-256으로 확인해 `/tmp/ab`에 복사하고 경로를 출력합니다. 번들 파일이 없을 때만 릴리스 다운로드를, 다운로드 실패에만 로컬 npm 설치를 시도합니다. 둘 다 안 되면 실패를 알립니다. 시험 환경은 x86_64 Debian 12·Node 22.23.2이고 [npm 배포본은 Node 24 이상](https://github.com/vercel-labs/agent-browser/blob/v0.39.0/package.json)을 요구하므로 npm 대체 설치 성공을 가정하지 않습니다.

```bash
bash <스킬셋 경로>/_shared/scripts/get-agent-browser.sh
export PATH="/tmp/ab:/tmp/ab/node_modules/.bin:$PATH"
```

`agent-browser install`로 Chrome을 내려받지 않습니다. 기존 Chromium 자동 감지를 먼저 쓰고 실패할 때만 `--executable-path`로 이미 있는 브라우저를 지정합니다.

- **research:** `agent-browser read <url>`로 브라우저 없이 원문 본문을 읽습니다. 없거나 막히면 `curl`로 원문을 확인합니다.
- **build·verify·ux:** 화면 과제에서는 자기 서버만 `agent-browser open <url>` → `agent-browser snapshot -i` → 주요 흐름의 `agent-browser click @ref` → `agent-browser screenshot /tmp/own-app.png`로 확인합니다. 두 역할이면 각각 확인하고 스크린샷 경로·확인한 것·못 한 것을 보고합니다. 실행 파일이 없으면 위 설치 스크립트부터 쓰고, 화면 확인용 Playwright·Puppeteer·Selenium은 새로 설치하지 않습니다(과제가 자동 E2E 테스트를 요구하면 그 테스트는 예외이며 직접 화면 확인은 여전히 먼저 합니다).
- **금지:** Cofa 응시·감독 화면, 메신저, 제출 흐름과 데스크톱을 조작하지 않습니다(Computer Use 금지). `AI_GATEWAY_API_KEY`를 쓰는 AI 채팅 기능도 사용하지 않습니다. 검색어·외부 요청에는 과제 코드·데이터·담당자 답을 넣지 말고 일반 기술 질문으로 바꿉니다.

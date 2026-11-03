# skills

Codex용 작업 절차 스킬과 공용 자료(`_shared`)입니다. 업무 담당자에게 확인할 사실과 사용자의 판단을 구분하고, 그 근거가 구현·검증·결정 문서·설명까지 이어지게 합니다. 과제 답안이나 코드는 포함하지 않습니다.

자세한 구성은 [personal-skills/README.md](personal-skills/README.md)를, 실제 사용법은 [GUIDE.md](GUIDE.md)를, 시험 중 한 화면 요약은 [CHEATSHEET.md](CHEATSHEET.md)를 보세요.

## 설치

```bash
git clone --depth 1 https://github.com/jabdori/skills.git /tmp/s && bash /tmp/s/install.sh
```

`install.sh`는 스킬과 공용 자료 `_shared`(지침·템플릿·점검 스크립트)를 `~/.agents/skills`에 함께 복사하고 빠진 것이 없는지 확인합니다. 리눅스에서는 화면 확인 도구 agent-browser v0.39.0도 저장소에 함께 넣은 실행 파일(`_shared/bin/`, SHA-256 검증, Apache-2.0 — `LICENSE-agent-browser`)로 `/tmp/ab/agent-browser`에 설치합니다. 네트워크가 없어도 됩니다. Codex 설정은 바꾸지 않습니다.

Codex에게 "깃허브에서 jabdori/skills 설치해"라고 해도 됩니다. 이때는 내장 `skill-installer`가 `~/.codex/skills`에 설치하는데, **`_shared`(shared-resources)까지 함께 설치됐는지** 확인하세요. 빠지면 다른 스킬의 링크가 깨집니다.

`codex`를 새로 시작한 뒤 "사용 가능한 스킬에 exam-start·brief·build가 있는지 알려줘"로 인식을 확인합니다.

## License

MIT

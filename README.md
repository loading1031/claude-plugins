# claude-plugins

Claude Code 플러그인 마켓플레이스.

| 플러그인 | 내용 | 명령 |
|---|---|---|
| `planning` | 기획을 한 주제씩 닫는 진행 방식. 백로그 항목 하나 = 브랜치 하나 | `/planning:init`, `/planning:backlog`, `/planning:spec`, `/planning:commit`, `/planning:done`, `/planning:handoff` |
| `kopring` | Kotlin + Spring Boot 컨벤션. `.kt` 작업 시 규칙 자동 적용, 편집 전 검사 훅 | `/kopring:init`, 셸에서 `kopring-check` |

## 설치

```sh
claude plugin marketplace add loading1031/claude-plugins   # 로컬이면 경로
claude plugin install planning@loading1031-plugins --scope project
claude plugin install kopring@loading1031-plugins --scope project
```

프로젝트마다 한 번:

- `/planning:init` — CLAUDE.md에 기획 설정 절, backlog.md·log.md 생성
- `/kopring:init` — CLAUDE.md에 컨벤션 선언, pre-commit 훅 설치

## 출처

- `kopring`은 [kopring-conventions](https://github.com/loading1031/kopring-conventions)의 `.claude/rules`를 스킬로, 검사 스크립트와 훅·문서를 그대로 옮겼다(커밋 89d7201 기준).

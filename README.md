# claude-plugins

Claude Code 플러그인 마켓플레이스.

| 플러그인 | 내용 | 명령 |
|---|---|---|
| `planning` | 기획을 한 주제씩 닫는 진행 방식. 백로그 항목 하나 = 브랜치 하나 = 이슈 하나. git 명령 검사 훅(add -A, 커밋 접두어·Refs, 금지어) | `/planning:init`, `/planning:backlog`, `/planning:spec`, `/planning:commit`, `/planning:done`, `/planning:handoff` |
| `kopring` | Kotlin + Spring Boot 컨벤션. `.kt` 작업 시 규칙 자동 적용, 편집 전 검사 훅 | `/kopring:init`, 셸에서 `kopring-check` |
| `nextts` | Next.js(16+, App Router) + TypeScript 컨벤션. `.ts`/`.tsx` 작업 시 규칙 자동 적용, 편집 전 검사 훅(JS 파일·`NEXT_PUBLIC_` 비밀값·메모이제이션·Tailwind 클래스 조립과 색 임의값·접근성 등) | `/nextts:init`, 셸에서 `nextts-check` |
| `design` | 와이어프레임·화면 디자인을 Claude 아티팩트에 두고 코드와 맞추는 방식. 탭 구성(화면 > 컴포넌트 > 토큰), 화면 구현 전 읽기, 커밋에 rev·pub 기록. 프레임워크와 무관 | `/design:init` |

## 설치

```sh
claude plugin marketplace add loading1031/claude-plugins   # 로컬이면 경로
claude plugin install planning@loading1031-plugins --scope project
claude plugin install kopring@loading1031-plugins --scope project
claude plugin install nextts@loading1031-plugins --scope project
claude plugin install design@loading1031-plugins --scope project
```

플러그인에는 버전 번호가 없다. 커밋이 곧 버전이라, 프로젝트 `.claude/settings.json`에 자동 업데이트를 켜 두면 늘 최신을 쓴다:

```json
"extraKnownMarketplaces": {
  "loading1031-plugins": {
    "source": { "source": "github", "repo": "loading1031/claude-plugins" },
    "autoUpdate": true
  }
}
```

프로젝트마다 한 번:

- `/planning:init` — CLAUDE.md에 기획 설정 절, backlog.md·log.md 생성
- `/kopring:init` — CLAUDE.md에 컨벤션 선언, pre-commit 훅 설치
- `/nextts:init` — CLAUDE.md에 프론트엔드 컨벤션 선언, JS 설정 파일을 `.ts`로, pre-commit 훅 설치(검사 + `tsc --noEmit`)
- `/design:init` — 디자인 문서 연결(없으면 탭 구성대로 새로 만듦), CLAUDE.md에 디자인 절

## 출처

- `kopring`은 [kopring-conventions](https://github.com/loading1031/kopring-conventions)의 `.claude/rules`를 스킬로, 검사 스크립트와 훅·문서를 그대로 옮겼다(커밋 89d7201 기준).

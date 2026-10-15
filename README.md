# claude-plugins

Claude Code 플러그인 마켓플레이스.

| 플러그인 | 내용 | 명령 |
|---|---|---|
| `planning` | 기획을 한 주제씩 닫는 진행 방식. GitHub 이슈 또는 파일 백로그에서 작업 선택·세션 재개. git 명령 검사 훅(add -A, 커밋 접두어·Refs, 금지어, 개발 브랜치 선언 시 dev에서 분기·dev로 PR) | `/planning:init`, `/planning:backlog`, `/planning:spec`, `/planning:commit`, `/planning:done`, `/planning:handoff` |
| `kopring` | Kotlin + Spring Boot 컨벤션. `.kt` 작업 시 규칙 자동 적용, 편집 전 검사 훅 | `/kopring:init`, 셸에서 `kopring-check` |
| `nextts` | Next.js(16+, App Router) + TypeScript 컨벤션. `.ts`/`.tsx` 작업 시 규칙 자동 적용, 편집 전 검사 훅(JS 파일·`NEXT_PUBLIC_` 비밀값·메모이제이션·Tailwind 클래스 조립과 색 임의값·접근성 등) | `/nextts:init`, 셸에서 `nextts-check` |
| `django` | 기본 Django 서버·템플릿 + Tailwind CSS 4·DaisyUI 5. HTMX·async 선택 적용. Claude/Codex 공용 스킬 | `/django:init`, `/django:guide`, `/django:server`, `/django:templates`, `/django:htmx` |
| `design` | 와이어프레임·화면 디자인을 Claude 아티팩트에 두고 코드와 맞추는 방식. 탭 구성(화면 > 컴포넌트 > 토큰), 화면 구현 전 읽기, 커밋에 rev·pub 기록. 프레임워크와 무관 | `/design:init` |

## 설치

```sh
claude plugin marketplace add loading1031/claude-plugins   # 로컬이면 경로
claude plugin install planning@loading1031-plugins --scope project
claude plugin install kopring@loading1031-plugins --scope project
claude plugin install nextts@loading1031-plugins --scope project
claude plugin install design@loading1031-plugins --scope project
claude plugin install django@loading1031-plugins --scope project
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

- `/planning:init` — 프로젝트에 GitHub 이슈 또는 파일 백로그 설정
- `/kopring:init` — CLAUDE.md에 컨벤션 선언, pre-commit 훅 설치
- `/nextts:init` — CLAUDE.md에 프론트엔드 컨벤션 선언, JS 설정 파일을 `.ts`로, pre-commit 훅 설치(검사 + `tsc --noEmit`)
- `/django:init` — Django 프로젝트 설정과 컨벤션 연결. 의존성·migration·훅을 자동 설치하지 않음
- `/design:init` — 디자인 문서 연결(없으면 탭 구성대로 새로 만듦), CLAUDE.md에 디자인 절

## 출처

- `kopring`은 [kopring-conventions](https://github.com/loading1031/kopring-conventions)의 `.claude/rules`를 스킬로, 검사 스크립트와 훅·문서를 그대로 옮겼다(커밋 89d7201 기준).

## Django 패키지

`plugins/django`는 Django 서버·Django 템플릿·Tailwind CSS 4·DaisyUI 5를 기본으로 하는 지침 플러그인이다. 일반 sync view와 폼/ORM이 기본이며 HTMX·async는 필요한 기능에서만 쓴다. React, API 프런트 분리, 특정 DB·배포 서비스, TipTap, pattern library는 기본 의존성이 아니다.

Claude Code는 위 마켓플레이스 설치를 사용한다. Codex용 portable manifest는 `plugins/django/plugin.json`에 있고 같은 `skills/`와 `docs/`를 사용한다. Codex에서 수동 설치할 때 이 플러그인 폴더 전체를 대상으로 해야 한다(스킬만 복사하면 참조 문서가 빠진다). 설치 후 해당 클라이언트에서 `guide`/`init`이 로드되는지 확인한다. 이 저장소에 패키지를 추가한 것만으로 두 클라이언트에 설치·활성화됐다고 취급하지 않는다. 별도 lifecycle hook이나 MCP 서버는 없다.

기존 2nd-if 규칙에서 공통 기술 원칙을 추출하면서 전체 async 강제, Django 버전 고정 가정, 특정 서버 경로·DB·운영 환경, 오래된 DaisyUI 문법을 제거했다. 소설·분기·리더·TipTap 정책은 제품 프로젝트에 남긴다. design 플러그인은 화면 기준, django는 실제 템플릿/UI 코드 규칙을 담당한다.

### GitHub 이슈를 백로그로 사용

기획 설정에 `백로그: issue`, `작업 추적: OWNER/REPO`, `작업지시서: issue`를 둔다. 기존 `작업지시서: issue` + `작업 추적` 설정도 인식한다. `백로그: file`이면 기존 파일 방식을 유지한다.

`/planning:backlog`는 열린 이슈에서 진행 중 작업과 다음 후보를 보여 주고, `/planning:backlog pick 17`은 해당 이슈의 본문·댓글과 관련 문서를 읽어 현재 세션에서 재개한다. 새 세션에서도 같은 저장소 설정을 읽으므로 이관한 todo 목록을 다시 설명할 필요가 없다. 세션을 자동 생성하는 기능은 아니다. 명령 표기는 클라이언트가 제공하는 스킬 호출 방식을 따른다.

이슈 모드는 backlog.md·work-orders.md·log.md를 중복 생성하지 않는다. 기획만 끝난 구현 이슈를 닫지 않으며, 전체 완료 기준을 충족한 뒤에만 종료한다.

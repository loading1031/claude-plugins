# 컨벤션

Next.js(16 이상, App Router) + TypeScript 프로젝트의 컨벤션이다. 특정 앱 설계(차트 라이브러리, 실시간 처리 방식, 백엔드 종류)는 다루지 않는다. 그런 것은 각 프로젝트의 `CLAUDE.md`나 `.claude/rules`에 둔다. 와이어프레임과 화면 디자인의 작업 방식은 `design` 플러그인이 다룬다.

## 무엇을 규칙으로 두나

스킬 본문은 해당 파일을 작업할 때마다 컨텍스트에 들어간다. 그래서 Claude가 자주 어기거나 기본값과 다르게 정한 것만 둔다. 훅 검사는 위반할 때만 메시지를 내므로, 스킬에 쓰지 않은 규칙도 훅으로는 막는다(예: `secret/no-public-secret`).

### 두지 않는 것

| 항목 | 이유 |
|---|---|
| App Router, 서버 컴포넌트가 기본 | Next 기본값 |
| `useState`·`useEffect`·`useRef`는 클라이언트 컴포넌트에서만 | React가 빌드 때 막고, Next TypeScript 플러그인도 편집기에서 알려 준다 |
| 토큰은 httpOnly 쿠키에, 브라우저 저장소에 두지 않음 | Claude가 이미 지킨다 |
| Canvas·DOM 라이브러리는 `useEffect`에서 만들고 정리 함수에서 해제 | React 기본 패턴 |
| 패키지 매니저 | 프로젝트의 도구 선택. pre-commit 타입 검사 명령은 lockfile로 고른다 |
| Tailwind·shadcn/ui 사용 여부 | 프로젝트의 도구 선택. 대신 `tailwindcss`·`components.json`이 있으면 해당 규칙이 저절로 켜진다 |

## 규칙의 부류

| 표시 | 뜻 | 바꾸려면 |
|---|---|---|
| **범용** | 이 플러그인을 쓰는 모든 프로젝트에 적용 | 플러그인을 고친다 |
| **팀** | 합리적인 기본값. 조건(React Compiler, `tailwindcss`, `components.json`, `server/` 폴더)이 맞을 때만 켜지거나 선언으로 끈다 | 조건·선언을 바꾼다 |
| **프로젝트** | 프로젝트 `CLAUDE.md` "프론트엔드 컨벤션" 절에 선언한 값으로 동작 | 선언을 고친다(`/nextts:init`) |

## 강제 수단

같은 규칙을 두 번 검사하지 않는다. ESLint 설정은 이 플러그인이 건드리지 않는다.

| 수단 | 시점 | 하는 일 |
|---|---|---|
| **Claude 훅** | Claude Code가 파일을 쓰거나 고치기 직전 | 아래 색인의 규칙. 새로 생기는 위반만 차단 |
| **pre-commit 훅** | 커밋할 때 | 같은 검사 스크립트로 커밋되는 파일 전체 검사, 그리고 `tsc --noEmit` |
| **Claude 스킬** | `.ts`/`.tsx`·`.css`·설정 파일 작업 중 | 훅으로 잡을 수 없는 규칙(`"use client"` 위치, `server-only`, 화면 상태, 모바일 우선) |

검사 대상은 Next 프로젝트 안의 파일뿐이다. 파일에서 위로 올라가며 `next`를 의존성에 둔 `package.json`을 찾아 그 폴더를 프로젝트 루트로 본다. 모노레포(`frontend/` 등)도 선언 없이 동작한다.

## 문서

| 문서 | 내용 |
|---|---|
| [컴포넌트](components.md) | `"use client"` 위치, `server-only`, 메모이제이션과 React Compiler |
| [TypeScript와 도구](typescript.md) | JS 파일 금지, 설정 파일을 `.ts`로, `allowJs`, Turbopack, 타입 검사 |
| [구조와 환경변수](architecture.md) | `server/` 폴더, private·public 환경변수 관리(`server/env.ts`, `lib/public-env.ts`) |
| [비밀값과 백엔드](backend-and-secrets.md) | `NEXT_PUBLIC_`, 백엔드는 서버에서만 호출(BFF), 쓰지 않는 라이브러리 |
| [Tailwind와 화면](tailwind-and-ui.md) | v4 설정, 클래스 조립 금지, 색·다크 모드는 토큰, UI 컴포넌트 재사용, 화면 상태, 접근성, 모바일 우선 |

## 검사 규칙 색인

검사 스크립트가 출력하는 `rule id` 전체 목록이다. 모두 Claude 훅과 pre-commit 훅 둘 다 적용된다.

| rule id | 부류 | 내용 | 문서 |
|---|---|---|---|
| `ts/no-js-file` | 범용 | `.js`·`.jsx`·`.mjs`·`.cjs` 파일 금지(`public/` 제외). 훅은 새 파일만 막는다 | [TypeScript와 도구](typescript.md) |
| `ts/no-allow-js` | 범용 | `tsconfig.json`의 `"allowJs": true` 금지 | [TypeScript와 도구](typescript.md) |
| `secret/no-public-secret` | 범용 | `NEXT_PUBLIC_`이 붙은 비밀 이름(`SECRET`, `PRIVATE`, `PASSWORD`, `SERVICE_ROLE`, `SERVICE_KEY`, `DATABASE_URL` 등) 금지. `.ts`·`.tsx`·`.env*` | [비밀값과 백엔드](backend-and-secrets.md) |
| `memo/no-manual-memo` | 팀 | `useMemo`·`useCallback`·`memo`를 `react`에서 가져오거나 `React.`으로 쓰지 않음. `next.config.*`에 `reactCompiler`가 켜진 프로젝트에서만 | [컴포넌트](components.md) |
| `bundler/no-webpack` | 팀 | `package.json`의 `next dev`·`next build`에 `--webpack` 금지. 선언 "번들러: webpack 허용"이면 끔 | [TypeScript와 도구](typescript.md) |
| `project/backend-server-only` | 프로젝트 | "백엔드 호출: 서버만"일 때 백엔드 주소 환경변수에 `NEXT_PUBLIC_`을 붙이거나 클라이언트 컴포넌트에서 읽지 않음 | [비밀값과 백엔드](backend-and-secrets.md) |
| `arch/server-only-marker` | 팀 | `server/`가 있으면 그 안의 파일(`.d.ts` 제외)에 `import "server-only"` 필수 | [구조와 환경변수](architecture.md) |
| `arch/env-via-module` | 팀 | `server/`가 있으면 `process.env`는 `server/env.ts`·`lib/public-env.ts`(`NEXT_PUBLIC_`만)·설정 파일에서만 | [구조와 환경변수](architecture.md) |
| `tailwind/no-config-file` | 팀 | Tailwind v4에서 `tailwind.config.*` 새 파일, CSS의 `@tailwind` 지시어 금지 | [Tailwind와 화면](tailwind-and-ui.md) |
| `tailwind/no-dynamic-class` | 팀 | `` `bg-${x}-500` ``, `"text-" + x`처럼 클래스 이름 조립 금지 | [Tailwind와 화면](tailwind-and-ui.md) |
| `tailwind/no-arbitrary-color` | 팀 | 색 임의값(`text-[#f00]`), `style`의 색 리터럴 금지. 크기·간격 임의값은 허용 | [Tailwind와 화면](tailwind-and-ui.md) |
| `tailwind/dark-via-token` | 팀 | `dark:` 뒤의 팔레트 색 금지 → 색 토큰 | [Tailwind와 화면](tailwind-and-ui.md) |
| `ui/use-ui-component` | 팀 | `components.json`이 있으면 UI 폴더 밖에서 `<button>`·`<input>`·`<select>`·`<textarea>` 금지 | [Tailwind와 화면](tailwind-and-ui.md) |
| `a11y/no-click-on-div` | 범용 | `role` 없는 `<div onClick>`·`<span onClick>` 금지 | [Tailwind와 화면](tailwind-and-ui.md) |
| `a11y/image` | 범용 | `<img>` 금지(→ `next/image`), `alt` 없는 `<Image>` 금지 | [Tailwind와 화면](tailwind-and-ui.md) |
| `project/forbidden-lib` | 프로젝트 | "쓰지 않는 라이브러리"의 패키지를 import하거나 `package.json`에 추가하지 않음 | [비밀값과 백엔드](backend-and-secrets.md) |

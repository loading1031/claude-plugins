---
name: init
description: 프로젝트에 nextts 컨벤션을 적용한다 — CLAUDE.md에 프론트엔드 선언, JS 설정 파일 옮기기, pre-commit 훅 설치
disable-model-invocation: true
---

# /nextts:init — 프로젝트에 컨벤션 적용

Claude 훅과 코드 규칙은 플러그인을 켜면 바로 동작한다. Next 프로젝트 위치(`next`를 의존성에 둔 `package.json`), React Compiler 사용 여부(`next.config.*`), Tailwind 버전(`tailwindcss`), UI 컴포넌트 폴더(`components.json`), 구조 검사(`server/` 폴더)는 검사기가 알아서 찾는다. 생성된 API 타입(openapi-typescript 표시가 있는 파일)은 항상 수정을 막는다. 이 명령은 플러그인이 대신할 수 없는 것만 한다.

## 절차

### 1. 확인
- Next 프로젝트 루트를 찾는다(저장소 루트 또는 `frontend/` 같은 하위 폴더). 없으면 Next 프로젝트를 먼저 만들라고 안내하고 끝낸다.
- 백엔드를 서버에서만 부르는지(BFF), 그렇다면 백엔드 주소 환경변수 이름, 쓰지 않을 라이브러리를 묻는다. 이미 CLAUDE.md에 적혀 있으면("결정된 사항" 등) 거기서 옮기고 묻지 않는다.

### 2. CLAUDE.md
프로젝트 루트 `CLAUDE.md`에 아래 절이 없으면 추가하고, 있으면 값만 맞춘다. 다른 내용은 건드리지 않는다. kopring의 "## 컨벤션" 절과는 별개다.

```markdown
## 프론트엔드 컨벤션
- nextts 플러그인을 따른다 (규칙은 .ts/.tsx 작업 시 자동 적용, 검사 훅 동작)
- 백엔드 호출: <서버만 | 제한 없음>   <!-- 훅 project/backend-server-only -->
- 백엔드 주소 환경변수: <없으면 "없음". 예: BACKEND_URL>
- 번들러: Turbopack   <!-- "webpack 허용"이면 훅 bundler/no-webpack 끔 -->
- 쓰지 않는 라이브러리: <없으면 "없음". 예: axios, moment>   <!-- 훅 project/forbidden-lib -->
```

### 3. JavaScript 파일 옮기기
- Next 프로젝트 안의 `.js`·`.jsx`·`.mjs`·`.cjs`(`public/`, `node_modules/`, `.next/` 제외)를 찾아 보여 주고, `.ts`로 옮길지 묻는다. Tailwind v4 프로젝트에 `tailwind.config.*`가 있으면 `@theme`으로 옮길지 묻는다. create-next-app이 만든 `postcss.config.mjs`, `eslint.config.mjs`가 보통 여기에 해당한다.
- `eslint.config.ts`로 옮기면 개발 의존성 `jiti`(2.2.0 이상)를 lockfile의 패키지 매니저로 추가한다.
- `tsconfig.json`의 `allowJs`를 `false`로 바꾼다.
- 근거: `${CLAUDE_SKILL_DIR}/../../docs/conventions/typescript.md`

### 4. server/와 환경변수
근거: `${CLAUDE_SKILL_DIR}/../../docs/conventions/architecture.md`. `server/` 폴더가 있으면 구조 검사가 켜진다.
- Next 루트(또는 `src/`)에 `server/`가 없으면 만들지 묻는다. 만들면 `server/env.ts`(`import "server-only"`, 필요한 private 변수를 `required()`로 읽음)와 `lib/public-env.ts`(`NEXT_PUBLIC_` 변수를 이름 그대로 읽음)를 만든다. 변수 이름은 사용자에게 묻거나 `.env.example`·기존 코드의 `process.env`에서 모은다.
- `.env.example`이 없으면 만든다: 변수 이름 전부, 값은 비우고 private/public을 주석으로 표시. `.gitignore`가 `.env*`를 무시하면 `!.env.example` 줄을 더한다.
- 이미 `server/`가 있으면 `nextts-check`로 `arch/*` 위반을 보여 주고, `process.env`를 env 모듈로 옮길지 묻는다.

### 5. API 클라이언트 (서버가 `openapi/openapi.json`을 만드는 경우)
근거: `${CLAUDE_SKILL_DIR}/../../docs/conventions/api-client.md`. 저장소 루트에 `openapi/openapi.json`이 없으면 서버 쪽(kopring `/kopring:init` 3단계)을 먼저 하라고 안내하고 건너뛴다.
1. 의존성: `openapi-fetch`(dependencies), `openapi-typescript`(devDependencies)를 lockfile의 패키지 매니저로 추가한다.
2. `package.json`에 `"api:generate": "openapi-typescript <Next 루트에서 본 상대 경로>/openapi/openapi.json -o server/api/schema.d.ts"`를 넣고 실행한다.
3. `${CLAUDE_PLUGIN_ROOT}/templates/api-client/client.ts` → `server/api/client.ts`. `__BACKEND_URL_KEY__`는 `server/env.ts`의 백엔드 주소 키로 바꾼다. 인증 헤더 미들웨어는 사용자와 채운다.
4. `api-spec-sync.yml` → `.github/workflows/`. `__DEV_BRANCH__`는 기획 설정의 "개발 브랜치"(없으면 기본 브랜치), `__FRONT_DIR__`는 저장소 루트에서 본 Next 루트(예: `frontend`), `__NODE_VERSION__`은 프로젝트 Node 버전.
5. GitHub App 설정을 확인한다: `gh variable list`에 `APP_CLIENT_ID`, `gh secret list`에 `APP_PRIVATE_KEY`가 있는지. 없으면 문서의 "자동 갱신" 절대로 안내한다(앱 만들기 → 권한 Contents·Pull requests 쓰기 → 저장소에 설치 → Client ID·private key 등록).

### 6. pre-commit 훅
1. `${CLAUDE_PLUGIN_ROOT}/scripts/check_next_conventions.py`를 저장소의 `scripts/conventions/check_next_conventions.py`로 복사한다. 이미 있고 내용이 다르면 차이를 보여 주고 덮어쓸지 묻는다.
2. `.githooks/pre-commit`이 없으면 `#!/usr/bin/env sh` 다음에 아래 블록을 넣어 만들고 실행 권한을 준다. 있으면 이 블록이 들어 있는지 확인하고, 없으면 **shebang 바로 다음**에 넣는다. 예전 nextts 블록이 있고 내용이 다르면(검사 파일 목록 등) 이 블록으로 바꾼다. 다른 검사(kopring 등)가 파일이 없을 때 `exit 0`하거나 `exec`로 끝나므로 그보다 앞에 있어야 한다.
   ```sh
   # 커밋되는 프론트엔드 파일의 Next.js 컨벤션 검사와 타입 검사 (nextts 플러그인)
   next_files=$(git diff --cached --name-only --diff-filter=ACM -- '*.ts' '*.tsx' '*.mts' '*.cts' '*.js' '*.jsx' '*.mjs' '*.cjs' '*.css' '*package.json' '*tsconfig.json' '*.env*')
   if [ -n "$next_files" ]; then
     next_check="$(git rev-parse --show-toplevel)/scripts/conventions/check_next_conventions.py"
     # shellcheck disable=SC2086
     python3 "$next_check" --files $next_files || exit 1
     # shellcheck disable=SC2086
     python3 "$next_check" --typecheck $next_files || exit 1
   fi
   ```
3. git 저장소면 `git config core.hooksPath .githooks`를 실행한다. 이미 다른 hooksPath가 설정돼 있으면 바꾸지 말고 사용자에게 알린다.
4. 플러그인을 업데이트한 뒤에는 이 명령을 다시 실행해 복사본을 맞추라고 안내한다. 복사본이 플러그인 검사기와 다르면 Claude 훅이 편집 때마다 경고한다.

### 7. 확인
- `python3 --version`이 3.10 이상인지 확인한다.
- 결과를 요약한다: CLAUDE.md에 쓴 값, 옮긴 JS 파일, 만든 `server/`·env 파일, 복사한 파일, hooksPath 설정 여부.

## 참고
- 규칙 전체와 rule id 색인: `${CLAUDE_SKILL_DIR}/../../docs/conventions/README.md`
- 저장소의 프론트엔드 파일 전체를 한 번에 검사: Bash에서 `nextts-check`

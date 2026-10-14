# 구조와 환경변수

Next는 화면과 얇은 BFF만 맡는다. 도메인 규칙과 in/out 구분은 백엔드(Spring 등)가 한다. 그래서 헥사고날처럼 계층을 나누지 않고, 비밀을 다루는 서버 전용 코드만 `server/` 폴더 하나에 모은다.

Next 루트 또는 `src/` 아래에 `server/` 폴더가 있으면 이 문서의 검사가 켜진다. 없는 프로젝트에서는 꺼진다.

## 폴더

```
app/          라우팅·화면 조립·서버 액션. server/를 불러 데이터를 받아 그린다
components/   ui/(공용) + 화면별 UI
server/       import "server-only". 백엔드 클라이언트, 세션, env.ts
lib/          유틸, public-env.ts
```

- 서버 액션(`"use server"`)은 얇게 두고 인증·백엔드 호출은 `server/`에 위임한다.
- 기능끼리 import 금지 같은 계층 규칙은 두지 않는다. Next 쪽 코드가 얇아 득보다 비용이 크다.

출처: Next는 구조에 대해 "unopinionated"([Project structure](https://nextjs.org/docs/app/getting-started/project-structure)). 데이터 접근은 서버에서만 도는 계층에 모으고, 서버 액션은 그 계층에 위임한다([Data Security](https://nextjs.org/docs/app/guides/data-security) "Data Access Layer", "Using a Data Access Layer for mutations").

## `server/`의 파일은 `server-only` (팀, `arch/server-only-marker`)

`server/`의 모든 파일은 맨 위에 `import "server-only"`를 둔다. 클라이언트 컴포넌트가 이 파일을 import하면 빌드 오류가 난다. 생성된 타입 파일(`.d.ts`)은 실행 코드가 없어 제외한다.

## 환경변수 (팀, `arch/env-via-module`)

### 두 종류

| 종류 | 이름 | 예 | 어디까지 가나 |
|---|---|---|---|
| private(서버 전용) | 접두어 없음 | `SPRING_API_URL`, `SPRING_SERVICE_KEY`, `SESSION_SECRET` | Next 서버 안. 클라이언트 컴포넌트에서 읽으면 빈 값 |
| public(브라우저 공개) | `NEXT_PUBLIC_` | `NEXT_PUBLIC_GA_ID` | 빌드 때 브라우저 번들에 값이 박힌다 |

### 읽는 곳은 종류별로 파일 하나

kopring이 `@Value`를 금지하고 `@ConfigurationProperties` 한 곳에 모으는 것과 같다.

```ts
// server/env.ts — private 전부
import "server-only";

function required(name: string): string {
  const value = process.env[name];
  if (!value) throw new Error(`환경변수 ${name}가 없다`);
  return value;
}

export const env = {
  springApiUrl: required("SPRING_API_URL"),
  springServiceKey: required("SPRING_SERVICE_KEY"),
  sessionSecret: required("SESSION_SECRET"),
};
```

```ts
// lib/public-env.ts — public 전부. 브라우저에서도 import 가능
export const publicEnv = {
  gaId: process.env.NEXT_PUBLIC_GA_ID,
};
```

- 다른 코드는 `process.env`를 읽지 않고 `env.springApiUrl`, `publicEnv.gaId`를 import한다.
- `lib/public-env.ts`는 `process.env.NEXT_PUBLIC_X`처럼 이름을 그대로 쓴다. Next는 빌드 때 이 글자 그대로의 참조만 값으로 바꾼다. `process.env[name]`이나 `const e = process.env; e.NEXT_PUBLIC_X`처럼 읽으면 브라우저에서 빈 값이 된다(검사기도 이 형태를 막는다).
- 예외: 빌드·서버 시작 때 서버에서만 실행되는 설정 파일(`next.config.ts`, `instrumentation.ts`, `proxy.ts`, `*.config.ts`)은 `process.env`를 직접 읽어도 된다.

### 왜 한 곳에서만 읽나

1. **비밀이 새지 않는다.** 아무 파일에서 `process.env.SPRING_SERVICE_KEY`를 읽게 두면, 그 파일이 클라이언트 컴포넌트에 import될 때 오류 없이 빈 값이 되어 조용히 고장 난다. 그걸 고치려고 `NEXT_PUBLIC_`을 붙이면 비밀이 브라우저로 나간다. `server/env.ts`에 모으면 처음부터 빌드 오류가 된다.
2. **설정을 한 곳에서 확인한다.** 필요한 변수가 없으면 서버가 시작할 때 바로 실패한다.
3. **Next 권장.** "Secret keys should be stored in environment variables, but only the Data Access Layer should access `process.env`", 감사 때 "environment variables are not imported outside the Data Access Layer"를 확인하라고 한다([Data Security](https://nextjs.org/docs/app/guides/data-security)).

### 값을 두는 파일

| 파일 | git | 내용 |
|---|---|---|
| `.env.example` | 커밋 | 변수 이름 전부와 설명(private/public 표시). 값은 비운다. create-next-app의 `.gitignore`는 `.env*`를 모두 무시하므로 `!.env.example` 줄을 더한다 |
| `.env.local` | 커밋 안 함 | 실제 값(비밀 포함) |

- `.env*` 파일은 `src/`를 써도 프로젝트 루트에 둔다.
- Next는 변수를 이 순서로 찾고 처음 찾은 값을 쓴다: 셸 환경변수(`process.env`) → `.env.$(NODE_ENV).local` → `.env.local`(테스트 때는 안 읽음) → `.env.$(NODE_ENV)` → `.env`. 비밀은 `.env.local`이나 셸 환경변수에만 둔다.
- `NEXT_PUBLIC_` 값은 `next build` 때 굳는다. 빌드한 뒤 환경변수를 바꿔도 브라우저 쪽 값은 바뀌지 않는다.

출처: [Environment Variables](https://nextjs.org/docs/app/guides/environment-variables) "Environment Variable Load Order", "Bundling Environment Variables for the Browser"(동적 조회 `process.env[varName]`, `const env = process.env`는 값으로 바뀌지 않음), create-next-app 템플릿 `gitignore`

## 백엔드 주소 검사와의 관계

`server/`가 있으면 "클라이언트 컴포넌트에서 백엔드 주소 환경변수를 읽음"(`project/backend-server-only`)은 `arch/env-via-module`이 더 넓게 막으므로 끈다. 백엔드 주소에 `NEXT_PUBLIC_`을 붙이는 검사는 그대로 둔다.

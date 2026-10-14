# 비밀값과 백엔드

## `NEXT_PUBLIC_` 비밀값 금지 (범용, `secret/no-public-secret`)

`NEXT_PUBLIC_`이 붙은 환경변수는 빌드 때 클라이언트 번들에 문자열로 박힌다. 비밀값은 접두어 없이 두고 서버 코드에서만 읽는다(그 모듈에는 `import "server-only"`).

검사는 이름으로 한다: `NEXT_PUBLIC_` 뒤에 `SECRET`, `PRIVATE`, `PASSWORD`, `PASSWD`, `SERVICE_ROLE`, `SERVICE_KEY`, `DATABASE_URL`, `DB_URL`이 들어가면 막는다. `KEY`, `TOKEN`은 넣지 않았다. `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY`, `NEXT_PUBLIC_MAPBOX_TOKEN`처럼 원래 공개용인 값이 많아서다.

Claude도 이 규칙은 알지만, 클라이언트 컴포넌트에서 값이 비어 있을 때 접두어를 붙여 "고치는" 실수를 한다. 그래서 스킬에는 쓰지 않고 훅으로만 막는다.

## 백엔드는 서버에서만 호출 (프로젝트, `project/backend-server-only`)

Next 서버를 BFF(Backend For Frontend)로 두는 프로젝트의 선언이다. 클라이언트에서 외부 API를 바로 부르는 Next 앱도 흔해서 범용 규칙이 아니다.

```markdown
- 백엔드 호출: 서버만
- 백엔드 주소 환경변수: BACKEND_URL
```

- 백엔드는 서버 컴포넌트, 라우트 핸들러, 서버 액션에서만 부른다. 브라우저는 Next하고만 통신한다.
- 클라이언트 컴포넌트가 데이터를 바꿔야 하면 서버 액션이나 라우트 핸들러를 거친다. 실시간 데이터도 라우트 핸들러가 중계한다.
- 검사: 백엔드 주소 환경변수에 `NEXT_PUBLIC_`을 붙이거나(`NEXT_PUBLIC_BACKEND_URL`), `"use client"` 파일에서 그 이름을 읽으면 막는다.

## 쓰지 않는 라이브러리 (프로젝트, `project/forbidden-lib`)

```markdown
- 쓰지 않는 라이브러리: axios, moment
```

그 패키지(와 하위 경로 `axios/…`)를 import·require하거나 `package.json` 의존성에 추가하면 막는다. 선언을 바꾸려면 사용자에게 먼저 묻는다.

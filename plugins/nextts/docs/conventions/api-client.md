# API 클라이언트

백엔드 API의 타입은 저장소 루트의 `openapi/openapi.json`(서버가 PR마다 갱신, kopring `docs/conventions/api-spec.md`)에서 만든다. 손으로 타입을 쓰지 않는다.

## 구성

```
server/api/
├ schema.d.ts   openapi-typescript가 만든 타입. 직접 고치지 않는다 (api/generated-readonly)
└ client.ts     import "server-only". openapi-fetch의 createClient, 인증 헤더 미들웨어
```

```ts
// 서버 컴포넌트·서버 액션·라우트 핸들러
import { api } from "@/server/api/client";
const { data, error } = await api.GET("/api/v1/stocks/{code}", { params: { path: { code } } });

// 어디서나(클라이언트 컴포넌트 props 포함): 타입만
import type { components } from "@/server/api/schema";
type Order = components["schemas"]["Order"];
```

- `package.json`: `"api:generate": "openapi-typescript <저장소 루트>/openapi/openapi.json --properties-required-by-default -o server/api/schema.d.ts"`
- `--properties-required-by-default`: springdoc(Kotlin)은 non-null 필드를 `required`로 표시하지 않고 nullable만 `["string","null"]`로 표시한다. 이 옵션이 없으면 모든 필드가 선택값(`code?: string`)이 된다. 있으면 `code: string`, `limitPrice: string | null`
- 호출은 `server/`를 거친다. `openapi-fetch`를 `server/` 밖에서 값으로 import하면 막는다(`api/client-in-server`, `server/` 폴더가 있을 때). `import type`은 실행 코드가 없어 번들에 들어가지 않으므로 허용한다.

## 왜 openapi-typescript + openapi-fetch인가

2026-10-14 같은 스펙으로 두 생성기를 돌리고 사용 코드의 타입 검사까지 확인했다.

| | openapi-typescript 7.13 + openapi-fetch 0.17 (선택) | typescript-axios (openapi-generator 7.10) |
|---|---|---|
| 생성물 | `schema.d.ts` 1개(147줄), 타입만 | 13개 파일(1,019줄) |
| 런타임 | openapi-fetch 약 0.2MB | axios 약 2MB + 생성 코드 |
| 생성할 때 필요 | Node | Java |
| 호출 | `api.POST("/api/v1/orders", { body })`. 경로 문자열도 타입 검사 | `orders.placeOrder({ placeOrderRequest })` |
| Next | fetch 기반 | Next fetch 캐시를 못 쓴다 |

## 숫자

- BigDecimal(금액·가격·비율·환율)은 스펙에서 `type: string, format: decimal` → TS `string`. 표시만 하고 계산하지 않는다
- 정수(수량·건수)는 `number`
- 차트 라이브러리에 넘길 때만 `Number()`로 바꾼다(그리기용이라 끝자리 오차가 드러나지 않는다)
- 입력 중 계산(주문 예상 금액 등)은 서버 액션으로 서버에 맡긴다

## 자동 갱신

스펙이 개발 브랜치에 머지되면 GitHub Action(`api-spec-sync.yml`)이 `pnpm api:generate`를 돌려 `chore: API 스펙 갱신` PR을 연다. 타입이 바뀌어 화면 코드가 깨지면 그 PR의 타입 검사가 실패하고, 그 PR에서 고친다.

- 토큰은 GitHub App: 기본 `GITHUB_TOKEN`으로 만든 PR에서는 다른 워크플로(CI)가 돌지 않는다([create-pull-request concepts](https://github.com/peter-evans/create-pull-request/blob/main/docs/concepts-guidelines.md)). `actions/create-github-app-token@v3`이 실행마다 1시간짜리 설치 토큰을 만든다
- 저장소 설정: Variables `APP_CLIENT_ID`(앱의 Client ID), Secrets `APP_PRIVATE_KEY`(앱의 private key `.pem` 전체). 앱 권한은 Contents·Pull requests Read and write, 그 저장소에 설치. Client secret(OAuth용)은 쓰지 않는다
- 프론트 쪽 drift 검사는 두지 않는다. 스펙 머지와 재생성 PR 사이의 차이는 정상이다

템플릿: `${CLAUDE_PLUGIN_ROOT}/templates/api-client/` (`/nextts:init`이 복사한다).

## 실제로 돌려 본 결과 (2026-10-15)

stock 저장소의 테스트 브랜치에서 이 템플릿을 그대로 돌렸다(브랜치·PR은 확인 후 정리).

| 확인 | 결과 |
|---|---|
| 스펙이 바뀌지 않은 push | 동기화 Action 성공, GitHub App 토큰 발급 성공, PR 안 만듦 |
| 서버가 응답 필드를 추가하고 스펙을 갱신한 push | Action이 `loading1031-bot`(GitHub App) 이름으로 `chore: API 스펙 갱신` PR을 열었다. 바뀐 파일은 `schema.d.ts` 하나(`currency: string` 추가) |
| 그 PR에서 CI가 도나 | 돈다. 타입 검사·drift 검사가 `pull_request`로 실행돼 통과(`GITHUB_TOKEN`이었다면 돌지 않는다) |
| 생성 타입 | `price: string`, `quantity: number`, `limitPrice: string \| null`. 사용 코드 타입 검사 통과 |

---
name: external-api
description: 외부 API 어댑터 규칙(@HttpExchange, 타임아웃, 도메인 예외 변환, 멱등 재시도). 외부 HTTP 연동을 쓸 때 사용
paths: "**/*.kt"
user-invocable: false
---

# 외부 API

근거: ${CLAUDE_SKILL_DIR}/../../docs/architecture/external-api.md

- 외부 API는 out 포트(`IssueWaybillPort`) 뒤에 두고 `adapter/out/external/<업체>`(계층형: `infrastructure`)에서 구현한다. 포트는 도메인 타입으로 주고받는다.
- HTTP 호출은 HTTP Interface(`@HttpExchange`)로 선언한다. 새 코드에서 `RestTemplate`을 쓰지 않는다.
- 외부 API의 요청·응답 DTO는 어댑터 패키지 밖으로 내보내지 않는다.
- 외부 오류(`RestClientResponseException` 등)는 어댑터에서 도메인 예외로 바꾼다.
- 연결·응답 타임아웃을 항상 명시하고 `*Properties`로 설정한다.
- 재시도는 멱등한 호출에만 한다. 결제·주문 생성 같은 호출은 멱등 키를 보내거나 재시도하지 않는다.
- 인증 키는 환경 변수로 주입하고 로그에 남기지 않는다.
- 업체를 바꿔 쓸 수 있으면 업체별 어댑터를 만들고 선택은 `config`에서 한다.
- 동시 호출은 `coroutineScope { async(CoroutineName("...")) { } }`로 묶는다.
- 어댑터 테스트에는 타임아웃, 5xx, 잘못된 응답 형식을 넣는다.

훅이 `arch/tech-client-outside-adapter`, `di/selection-in-config-only` 위반을 차단한다.

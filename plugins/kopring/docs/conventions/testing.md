# 테스트

Zed에는 빈 연결 오류를 편집 중에 보여 주는 기능도, Kotlin 디버거도 없다. 테스트가 그 둘을 대신한다.

## 1. 빈 연결 오류를 실행 전에 알 수 없다

| 컨벤션 | 부류 | 강제 |
|---|---|---|
| `@SpringBootTest` **컨텍스트 로딩 테스트**를 하나 둔다. 빈 연결 오류와 이름 규칙 메서드 오류를 실행 전에 잡는 유일한 장치다 | 범용 | 테스트 |
| 빈 구성, Repository 메서드, 설정 클래스를 바꾸면 커밋 전에 `./gradlew test`를 돌린다 | 범용 | 리뷰 |

## 2. 디버거가 없다

| 컨벤션 | 부류 | 강제 |
|---|---|---|
| 핵심 규칙은 `domain`의 순수 클래스에 두고 **Spring 없이 단위 테스트**한다. 디버거가 필요한 상황 자체를 줄인다 | 범용 | 리뷰 |
| 코루틴 코드는 `runTest`의 가상 시간으로 결정적으로 테스트한다 | 범용 | detekt `CoroutineLaunchedInTestWithoutRunTest` |
| 외부 시스템(DB, Redis, Kafka)이 얽힌 흐름은 Testcontainers 통합 테스트로 검증한다 | 범용 | 리뷰 |
| 외부 API는 WireMock 또는 `MockRestServiceServer`로 대체한다 | 범용 | 리뷰 |
| 비동기 흐름(이벤트, 메시지)은 로그의 `correlationId`로 추적할 수 있게 만든다 | 범용 | 리뷰 ([이벤트 드리븐](../architecture/event-driven.md)) |

## 3. 테스트 코드 예외

- 테스트 코드(`src/test`)에서는 `@Autowired`, `@Value`, `runBlocking`을 써도 된다. 검사 스크립트도 이 규칙들을 테스트 경로에 적용하지 않는다.
- 헥사고날 구조에서는 out 포트를 가짜 구현으로 바꿔서 application 서비스를 Spring 없이 테스트할 수 있다.

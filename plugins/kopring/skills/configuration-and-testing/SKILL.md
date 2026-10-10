---
name: configuration-and-testing
description: @ConfigurationProperties 설정값 규칙과 테스트 규칙(컨텍스트 로딩, Testcontainers). 설정이나 테스트를 쓸 때 사용
paths: "**/*.kt, **/application*.yml, **/application*.yaml, **/application*.properties"
user-invocable: false
---

# 설정값과 테스트

근거: ${CLAUDE_SKILL_DIR}/../../docs/conventions/configuration.md, ${CLAUDE_SKILL_DIR}/../../docs/conventions/testing.md

## 설정값

- `@Value`를 쓰지 않는다. 설정은 `@ConfigurationProperties` 클래스로 묶는다.
- 설정 클래스는 `config` 패키지에 `*Properties`라는 이름으로 두고, 접두사는 `<앱>.<영역>`으로 한다.
- `application.yml`에 키를 추가하면 대응하는 `*Properties` 필드도 같이 추가한다.
- 애플리케이션 클래스에 `@ConfigurationPropertiesScan`을 붙여 `*Properties`가 자동 등록되게 한다.
- 비밀값은 `application.yml`에 쓰지 않고 환경 변수로 주입한다.

```kotlin
@ConfigurationProperties("wms.allocation")
data class AllocationProperties(
    val maxQuantityPerPick: Int,
    val policy: String = "FIFO",
)
```

## 테스트

- `@SpringBootTest` 컨텍스트 로딩 테스트를 유지한다. 빈 연결 오류와 이름 규칙 메서드 오류를 실행 전에 잡는 유일한 장치다.
- 빈 구성, Repository 메서드, 설정 클래스를 바꾸면 `./gradlew test`로 컨텍스트 로딩 테스트까지 통과하는지 확인한다.
- `domain`의 규칙은 Spring 없이 단위 테스트한다. 헥사고날이면 out 포트를 가짜 구현으로 바꿔 서비스도 Spring 없이 테스트한다.
- 외부 시스템(DB, Redis, Kafka)이 얽힌 흐름은 Testcontainers, 외부 API는 WireMock 또는 `MockRestServiceServer`로 테스트한다.
- 테스트 코드에서는 `@Autowired`, `@Value`, `runBlocking`을 써도 된다. 코루틴 테스트는 `runTest`를 쓴다.

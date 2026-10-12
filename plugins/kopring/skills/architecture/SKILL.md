---
name: architecture
description: 패키지 구조와 계층(계층형/out 포트 헥사고날), 의존 방향, 포트·어댑터 이름 규칙. Kotlin + Spring 코드를 쓰거나 패키지를 만들 때 사용
paths: "**/*.kt, **/*.kts"
user-invocable: false
---

# 패키지 구조와 계층

근거: ${CLAUDE_SKILL_DIR}/../../docs/architecture/choosing.md

- 이 컨벤션은 **계층형**과 **out 포트 헥사고날** 두 구조를 지원한다. 프로젝트의 `CLAUDE.md`에 어느 쪽인지 적혀 있어야 한다. 없으면 코드를 쓰기 전에 사용자에게 묻는다.
- 계층형: `domain`, `application`, `infrastructure`, `api`, `config`
- out 포트 헥사고날: `domain`(+`domain/event`), `application/port/out`, `application/service`, `adapter/in/{web,messaging}`, `adapter/out/{persistence,cache,timeseries,external,messaging}`, `config`
- in 포트(UseCase 인터페이스)는 만들지 않는다. 컨트롤러와 리스너는 서비스를 직접 호출한다.
- 의존 방향
  - 계층형: `api → application → infrastructure → domain`, `application → domain`
  - 헥사고날: `adapter.in → application.service → application.port.out ← adapter.out`, 모두 `→ domain`
- `domain`: 순수 동기 Kotlin. `org.springframework.*`, `kotlinx.coroutines.*`, 바깥 계층을 import하지 않는다. JPA 애너테이션은 허용한다.
- `application`: 유스케이스와 트랜잭션 경계. 동기 코드. 헥사고날에서는 `adapter`를 import하지 않고 `port/out` 인터페이스에만 의존한다.
- Redis·Kafka·HTTP·JDBC(`JdbcTemplate`, `JdbcClient` 등) 등 외부 기술 클라이언트는 `infrastructure`(계층형) 또는 `adapter/out`(헥사고날)과 `config`에서만 쓴다.
- 이름: 포트 `<동사><대상>Port`(`LoadStockPort`), 어댑터 `<대상><기술>Adapter`(`StockPersistenceAdapter`), 읽기 전용 서비스 `<대상>QueryService`.
- 새 기술(캐시, 시계열 DB, 외부 API, 브로커)을 추가할 때는 docs/architecture/의 해당 케이스 문서를 먼저 읽는다.

훅이 `arch/domain-no-outer`, `arch/application-no-adapter`, `arch/tech-client-outside-adapter`, `domain/no-spring`, `domain/no-coroutines` 위반을 차단한다.

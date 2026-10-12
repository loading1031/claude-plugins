# 아키텍처 선택

이 컨벤션은 두 가지 패키지 구조를 지원한다. 어느 쪽을 쓸지는 **"서비스 코드가 서로 다른 기술이나 모델을 직접 알게 되느냐"**로 정한다. 저장소나 외부 시스템의 개수 자체는 기준이 아니다.

## 1. 지원하는 구조

### 1.1 계층형

```
<base>
├── domain          순수 동기 Kotlin(Spring·코루틴 없음). 비즈니스 규칙, JPA 엔티티
├── application     @Service. 유스케이스, 트랜잭션 경계(동기)
├── infrastructure  Spring Data Repository, JDSL 쿼리, 외부 기술 클라이언트
├── api             @RestController, 요청·응답 DTO, WebSocket·SSE
└── config          기능별 @Configuration, *Properties, 구현체 선택, Dispatcher·Scope
```

- 의존 방향: `api → application → infrastructure → domain`, `application → domain`
- 서비스가 `JpaRepository` 같은 구현 기술에 **직접** 의존한다.
- 전통적인 `controller/service/repository` 구조와 사실상 같고, 이름과 `domain` 순수성 규칙만 다르다.

### 1.2 out 포트 헥사고날 (권장 기본값)

```
<base>
├── domain
│   └── event/              도메인 이벤트 (순수 data class)
├── application
│   ├── port/out/           LoadStockPort, SaveStockPort, PublishStockEventPort
│   └── service/            @Service, 트랜잭션 경계. 컨트롤러·리스너가 직접 호출
├── adapter
│   ├── in/web/             @RestController
│   ├── in/messaging/       @KafkaListener, 외부 진입용 @EventListener
│   ├── out/persistence/    JpaRepository + JDSL, 포트 구현
│   ├── out/cache/          Redis
│   ├── out/timeseries/     시계열 DB
│   ├── out/external/       외부 API 클라이언트
│   └── out/messaging/      KafkaTemplate, Outbox
└── config
```

- 의존 방향: `adapter.in → application.service → application.port.out ← adapter.out`, 모두 `→ domain`
- 서비스는 **포트 인터페이스만** 안다. JPA, Redis, Kafka의 존재를 모른다.
- **in 포트(UseCase 인터페이스)는 두지 않는다.** 들어오는 쪽(웹, 메시지)은 추상화할 일이 거의 없고, 구현체 하나짜리 인터페이스만 늘어난다. Zed에서는 인터페이스가 하나 늘 때마다 "정의로 이동" 후 "구현으로 이동"을 한 번 더 해야 한다.

### 1.3 완전 헥사고날 (지원하지 않음)

in 포트까지 두는 구조다. 이 컨벤션에서는 쓰지 않는다. 이유는 1.2의 마지막 항목과 같다. 여러 진입점이 같은 유스케이스를 쓰더라도 서비스 클래스를 직접 호출하면 충분하다.

## 2. 고르는 기준

| 상황 | Spring 설정으로 숨길 수 있나 | 헥사고날의 이점 | 문서 |
|---|---|---|---|
| RDB 하나만 씀 | — | 작음 | — |
| `@Cacheable` 캐싱 | 숨길 수 있음 (CacheManager) | 작음 | [캐시](cache.md) |
| 직접 다루는 캐시 로직 (TTL 분기, 무효화, 분산 락) | 없음 | 중간 | [캐시](cache.md) |
| RDB + 시계열 DB 등 다른 기술의 저장소 | 없음 | **큼** | [다중 저장소](multi-datastore.md) |
| 읽기 Replica 라우팅 | 숨길 수 있음 (Routing DataSource) | 작음 | [읽기·쓰기 분리](read-write-split.md) |
| CQRS (읽기 모델이 다름) | 없음 | **큼** | [읽기·쓰기 분리](read-write-split.md) |
| 외부 API (결제, 택배사, 증권사) | 없음 | **큼** | [외부 API](external-api.md) |
| 프로세스 내부 이벤트 | 숨길 수 있음 (ApplicationEventPublisher) | 작음 | [이벤트 드리븐](event-driven.md) |
| 메시지 브로커 (Kafka, RabbitMQ) | 없음 | **큼** | [이벤트 드리븐](event-driven.md) |

판단 규칙:

- 표에서 "이점 큼"인 상황이 **하나라도 있거나 생길 예정이면** out 포트 헥사고날을 쓴다.
- 그 외에는 계층형으로 시작해도 된다. 나중에 "이점 큼" 상황이 생기면 해당 기술부터 포트 뒤로 옮긴다.
- 어느 구조를 쓰는지는 프로젝트의 `CLAUDE.md`에 적는다. Claude는 적혀 있지 않으면 사용자에게 묻는다.

## 3. 이름 규칙 (헥사고날)

| 대상 | 규칙 | 예 |
|---|---|---|
| out 포트 | `<동사><대상>Port`. 메서드는 그 동작만 | `LoadStockPort`, `SaveOrderPort`, `PublishStockEventPort` |
| out 어댑터 | `<대상><기술>Adapter`. 같은 기술이면 여러 포트를 한 어댑터가 구현해도 된다 | `StockPersistenceAdapter : LoadStockPort, SaveStockPort` |
| 서비스 | `<대상>Service`, 읽기 전용이면 `<대상>QueryService` | `AllocationService`, `StockQueryService` |

포트의 파라미터와 반환 타입은 `domain` 타입이나 application이 정의한 DTO다. JPA 엔티티를 쓰는 경우(엔티티가 `domain`에 있을 때)는 허용한다.

## 4. 기능 우선 패키지 (선택)

기능이 많아지면 기능을 먼저 나누고 그 안에 위 구조를 둔다. 계층형·헥사고날 어느 쪽과도 같이 쓸 수 있다.

```
<base>
├── stock/      domain/ application/ adapter/
├── inbound/    domain/ application/ adapter/
├── outbound/   domain/ application/ adapter/
└── config/     공통 Config (Dispatcher, 캐시, 메시징)
```

검사 스크립트의 경로 규칙은 경로에 `/domain/`, `/application/`, `/adapter/out/` 등이 들어 있는지만 보므로 기능 우선 구조에서도 그대로 동작한다.

## 5. 강제

| 규칙 | 부류 | 강제 |
|---|---|---|
| `domain`은 바깥 계층을 import하지 않는다 | 범용 | 훅 (`arch/domain-no-outer`), ArchUnit |
| `application`은 `adapter`를 import하지 않는다 (헥사고날) | 범용 | 훅 (`arch/application-no-adapter`), ArchUnit |
| Redis·Kafka·HTTP·JDBC(`JdbcTemplate`, `JdbcClient` 등) 클라이언트는 `infrastructure`, `adapter/out`, `config`에서만 쓴다 | 범용 | 훅 (`arch/tech-client-outside-adapter`) |
| 전체 의존 방향 | 범용 | ArchUnit (템플릿 예정) |

## 6. Zed에서의 비용

헥사고날은 구현체가 하나뿐인 인터페이스(포트)를 만든다. 서비스에서 `loadStockPort.load()`를 "정의로 이동"하면 인터페이스로 가고, 실제 코드를 보려면 "구현으로 이동"을 한 번 더 해야 한다. Kotlin LSP에서 둘 다 동작하므로 큰 문제는 아니지만, in 포트를 두지 않는 이유 중 하나다.

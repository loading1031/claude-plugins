# 이벤트 드리븐

EDA는 Zed 환경에서 영향이 가장 큰 케이스다. 보내는 쪽과 받는 쪽이 서로를 모르게 하는 것이 EDA의 목적이라 코드 탐색으로 흐름을 따라가기 어렵고, 비동기로 실행되어 디버거로 따라가기도 어렵다.

## 1. 종류

| 종류 | 예 | 이 문서에서 |
|---|---|---|
| **프로세스 내부 이벤트** | `ApplicationEventPublisher` + `@EventListener` | 다룸 (2·4장) |
| **메시지 브로커** | Kafka, RabbitMQ | 다룸 (2·5장) |
| **이벤트 소싱** | 이벤트 저장소가 원본 데이터 | 다루지 않음. 보통 전용 프레임워크(Axon 등)를 쓰고 컨벤션 범위가 커서 별도 문서 대상 |

## 2. 구조

| 종류 | 헥사고날 이점 | 이유 |
|---|---|---|
| 내부 이벤트 | 작음 | Spring이 이미 추상화한다. 서비스는 `publishEvent(StockAllocated(...))`만 안다 |
| 메시지 브로커 | **큼** | Kafka는 DB처럼 외부 기술이다. 직렬화, 토픽, 재시도가 서비스에 번지지 않게 한다 |

```
domain/event/                StockAllocated, OrderShipped   순수 data class, Spring 의존 없음
application/port/out/        PublishStockEventPort          브로커 발행 포트
application/service/         AllocationService              이벤트를 만들고 발행
adapter/in/messaging/        StockEventKafkaListener        브로커에서 받아 서비스 호출
                             AllocationEventHandler         내부 이벤트 리스너
adapter/out/messaging/       KafkaStockEventPublisher       PublishStockEventPort 구현, Outbox
                             Topics                         토픽 이름 상수
```

계층형 구조에서는 리스너를 `api`(외부 진입), 발행 어댑터를 `infrastructure`에 둔다.

- 보내는 쪽은 out 포트, 받는 쪽은 in 어댑터다. 받는 쪽은 웹 컨트롤러와 같은 위치이고, 컨트롤러처럼 **변환과 서비스 호출만** 한다.
- 도메인 이벤트는 `ApplicationEvent`를 상속하지 않는다(Spring 4.2부터 불필요). 그래서 `domain`에 둘 수 있다.

## 3. 흐름 추적: 이벤트 클래스를 허브로

IntelliJ Ultimate는 `publishEvent(...)` 옆에 리스너로 가는 아이콘을, 리스너 옆에 발행 지점으로 가는 아이콘을 보여 준다. Zed에서는 `publishEvent`에서 "정의로 이동"을 해도 Spring 인터페이스로 갈 뿐, 누가 받는지 알 수 없다.

그래서 **이벤트 클래스의 사용처 찾기 한 번으로 발행 지점과 리스너가 전부 나오게** 만든다.

| 컨벤션 | 부류 | 강제 |
|---|---|---|
| 이벤트 하나당 클래스 하나. 이름은 과거형(`StockAllocated`, `OrderShipped`) | 범용 | 리뷰 |
| `GenericEvent(type: String, payload: Map<String, Any>)` 같은 범용 이벤트를 쓰지 않는다 | 범용 | 리뷰 |
| 리스너는 **구체 이벤트 클래스 하나**를 파라미터로 받는다. `Any`, `ApplicationEvent`, 상위 타입, `@EventListener(classes = [...])` 금지 | Zed | 훅 (`event/listener-concrete-type`) |
| Kafka 토픽·RabbitMQ 큐 이름은 `Topics` 상수로만 쓴다. `@KafkaListener(topics = ["..."])`, `kafkaTemplate.send("...")` 금지 | 범용 | 훅 (`event/topic-constant`) |
| 브로커 메시지 클래스는 이벤트 클래스와 1:1로 대응시키고, 이름을 `<이벤트>Message`로 한다 | 팀 | 리뷰 |
| 이벤트 클래스는 `domain/event`, 토픽 상수는 메시징 어댑터 패키지에만 둔다 | 팀 | ArchUnit |

```kotlin
// domain/event
data class StockAllocated(val eventId: UUID, val sku: String, val quantity: Int, val occurredAt: Instant)

// application/service — 발행
publisher.publishEvent(StockAllocated(UUID.randomUUID(), sku, qty, Instant.now(clock)))  // clock: 주입받은 Clock

// adapter/in/messaging — 수신. 파라미터 타입이 StockAllocated라서 사용처 찾기에 잡힌다
@Component
class AllocationEventHandler(private val pickingService: PickingService) {
    @TransactionalEventListener(phase = TransactionPhase.AFTER_COMMIT)
    fun on(event: StockAllocated) = pickingService.createTask(event.sku, event.quantity)
}
```

## 4. 프로세스 내부 이벤트

| 컨벤션 | 부류 | 강제 |
|---|---|---|
| `@EventListener`는 발행자와 **같은 트랜잭션에서 동기로** 실행된다. 리스너가 실패하면 원래 작업도 롤백된다. 이걸 원할 때만 쓴다 | 범용 | 리뷰 |
| 부수 효과(알림, 외부 호출, 다른 모듈 갱신)는 `@TransactionalEventListener(phase = AFTER_COMMIT)`로 처리한다 | 범용 | 리뷰 |
| `AFTER_COMMIT` 리스너 안에서 DB에 쓰려면 `@Transactional(propagation = REQUIRES_NEW)`가 필요하다. 없으면 쓰기가 반영되지 않는다 | 범용 | 리뷰 |
| `AFTER_COMMIT` 리스너는 앱이 그 사이에 죽으면 실행되지 않는다. 유실되면 안 되는 이벤트는 Outbox(Spring Modulith의 이벤트 발행 기록 등)를 쓴다 | 범용 | 리뷰 |
| `@Async` 리스너는 MDC·보안 컨텍스트를 잃는다. `TaskDecorator`로 넘긴다 | 범용 | 리뷰 |

## 5. 메시지 브로커

| 컨벤션 | 부류 | 강제 |
|---|---|---|
| **DB 저장과 메시지 발행은 하나의 트랜잭션으로 묶이지 않는다.** 이벤트를 같은 DB 트랜잭션으로 outbox 테이블에 저장하고, 별도 발행기가 브로커로 보낸다(Outbox 패턴) | 범용 | 리뷰 |
| **소비자는 멱등하게** 만든다. 같은 메시지가 두 번 올 수 있다. 이벤트 ID로 처리 여부를 기록한다 | 범용 | 리뷰 |
| 순서가 중요한 이벤트는 같은 파티션 키(예: SKU, 계좌번호)로 보낸다 | 범용 | 리뷰 |
| 재시도는 횟수를 제한하고, 끝내 실패한 메시지는 DLQ(Dead Letter Topic)로 보낸다 | 범용 | 리뷰 |
| 모든 메시지에 `eventId`, `occurredAt`, `correlationId`를 넣는다. 헤더 또는 본문 | 범용 | 리뷰 |
| 스키마 변경은 필드 추가만 한다. 삭제·이름 변경·의미 변경은 새 버전 이벤트(`StockAllocatedV2`)로 만든다 | 범용 | 리뷰 |
| 직렬화는 JSON(Kotlin 모듈)이나 스키마 레지스트리(Avro, Protobuf)로 하고, Java 직렬화를 쓰지 않는다 | 범용 | 리뷰 |
| `KafkaTemplate`, `RabbitTemplate`은 메시징 어댑터와 `config`에서만 쓴다 | 범용 | 훅 (`arch/tech-client-outside-adapter`) |

## 6. 디버깅 대신 추적

비동기 흐름은 IntelliJ 디버거로도 따라가기 어렵다. Zed에는 디버거 자체가 없으므로 다음이 주 수단이다.

| 컨벤션 | 부류 | 강제 |
|---|---|---|
| `correlationId`를 요청 진입 시 만들고, 이벤트·메시지 헤더·MDC로 끝까지 넘긴다. 로그 검색 한 번으로 흐름 전체가 나와야 한다 | 범용 | 리뷰 |
| Micrometer Tracing(OpenTelemetry)으로 HTTP → 이벤트 → Kafka → 소비자를 하나의 트레이스로 잇는다 | 범용 | 리뷰 |
| 발행·수신 시 이벤트 이름, `eventId`, `correlationId`를 INFO 로그로 남긴다 | 범용 | 리뷰 |
| 흐름 전체는 Testcontainers(Kafka) 통합 테스트로 검증한다 | 범용 | 리뷰 |
| 리스너 로직은 서비스로 위임하고, 서비스는 이벤트 없이 단위 테스트한다 | 범용 | 리뷰 |

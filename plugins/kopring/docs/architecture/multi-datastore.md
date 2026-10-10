# 다중 저장소 (RDB + 시계열 DB 등)

데이터 성격에 따라 저장소를 나누는 경우다. 예: 주문·잔고는 PostgreSQL, 시세 틱·분봉은 시계열 DB. **out 포트 헥사고날을 쓴다.** 포트가 없으면 서비스 하나가 JPA와 시계열 DB 클라이언트를 둘 다 직접 다루게 된다.

## 1. 구조

```kotlin
// application/port/out — 데이터 종류별 포트
interface SaveOrderPort { fun save(order: Order): Order }
interface LoadCandlesPort { fun load(symbol: String, range: TimeRange, interval: Interval): List<Candle> }
interface SaveTicksPort { fun saveAll(ticks: List<Tick>) }

// adapter/out/persistence — JPA·JDSL은 여기에만
// adapter/out/timeseries — 시계열 DB 클라이언트는 여기에만
```

| 컨벤션 | 부류 | 강제 |
|---|---|---|
| 포트는 **데이터 종류** 단위로 만든다. 저장소 기술 단위(`TimeseriesPort`)로 만들지 않는다 | 범용 | 리뷰 |
| 저장소 클라이언트는 해당 어댑터 패키지에서만 쓴다 | 범용 | 훅 (`arch/tech-client-outside-adapter`) |
| Kotlin JDSL은 RDB 어댑터에서만 쓴다 | 범용 | 리뷰 |
| 시간은 저장소와 무관하게 `Instant`(UTC)로 다룬다. 시간대 변환은 표시 계층에서만 | 범용 | 리뷰 |

## 2. 트랜잭션: 두 저장소는 하나로 묶이지 않는다

`@Transactional`은 JPA 트랜잭션 매니저가 관리하는 RDB만 묶는다. 시계열 DB 쓰기는 RDB 롤백과 무관하게 남거나, 반대로 RDB만 커밋되고 시계열 DB 쓰기가 실패할 수 있다.

| 컨벤션 | 부류 | 강제 |
|---|---|---|
| 한 유스케이스에서 두 저장소에 쓰지 않는 것을 기본으로 한다 | 범용 | 리뷰 |
| 꼭 필요하면 **주 저장소(RDB)에 먼저 쓰고**, 부 저장소 쓰기는 이벤트로 넘긴다. 이벤트는 커밋 후에 처리한다(`@TransactionalEventListener(AFTER_COMMIT)` 또는 Outbox) | 범용 | 리뷰 ([이벤트 드리븐](event-driven.md)) |
| 부 저장소 쓰기는 재시도해도 결과가 같게(멱등) 만든다. 예: 시계열 포인트는 (심볼, 시각)을 키로 덮어쓴다 | 범용 | 리뷰 |
| 분산 트랜잭션(XA, 2PC)은 쓰지 않는다 | 팀 | 리뷰 |

## 3. 같은 기술의 데이터소스가 여러 개인 경우 (RDB 두 개)

JPA 데이터소스가 둘 이상이면 Repository가 어느 DB를 쓰는지가 `@EnableJpaRepositories`의 패키지 스캔 설정으로 정해진다. 이건 **코드 탐색으로 보이지 않는다.**

| 컨벤션 | 부류 | 강제 |
|---|---|---|
| 데이터소스마다 패키지를 나눈다 (`adapter/out/persistence/order`, `adapter/out/persistence/market`) | 범용 | 리뷰 |
| 데이터소스마다 Config를 하나씩 둔다 (`OrderDataSourceConfig`, `MarketDataSourceConfig`). 패키지 스캔 경로, EntityManagerFactory, 트랜잭션 매니저를 그 Config에서 모두 정한다 | 범용 | 리뷰 |
| 트랜잭션 매니저 이름 문자열을 서비스에 쓰지 않는다. 합성 애너테이션을 만든다 | Zed | 리뷰 |

```kotlin
@Target(AnnotationTarget.CLASS, AnnotationTarget.FUNCTION)
@Retention(AnnotationRetention.RUNTIME)
@Transactional(transactionManager = "marketTransactionManager")
annotation class MarketTransactional

@Service
@MarketTransactional
class CandleAggregationService(...)
```

`MarketTransactional`의 사용처 찾기로 해당 DB에 쓰는 서비스가 전부 나온다. 문자열 `"marketTransactionManager"`는 IntelliJ에서는 추적되지만 Zed에서는 추적되지 않는다.

## 4. 테스트

- 어댑터마다 Testcontainers로 실제 저장소를 띄워 통합 테스트한다.
- application 서비스는 포트를 가짜 구현으로 바꿔서 Spring 없이 테스트한다.

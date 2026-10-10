# 읽기·쓰기 분리

"읽기 DB와 쓰기 DB를 나눈다"는 말은 두 가지를 뜻할 수 있고, 아키텍처 영향이 전혀 다르다.

| | Replica 라우팅 | CQRS |
|---|---|---|
| 무엇을 나누나 | 같은 스키마의 **복제본**으로 읽기 부하를 분산 | 읽기와 쓰기의 **모델 자체**를 분리 |
| 서비스가 차이를 아나 | 모름 (설정에서 처리) | 앎 (다른 포트, 다른 모델) |
| 헥사고날 이점 | 작음 | **큼** |

## 1. Replica 라우팅

`@Transactional(readOnly = true)`면 Replica로, 아니면 Primary로 보낸다. 라우팅은 `config`에서 처리하고 서비스는 모른다. **포트를 두지 않는다.**

```kotlin
// config/DataSourceRoutingConfig.kt
class ReadWriteRoutingDataSource : AbstractRoutingDataSource() {
    override fun determineCurrentLookupKey() =
        if (TransactionSynchronizationManager.isCurrentTransactionReadOnly()) "replica" else "primary"
}

@Bean @Primary
fun dataSource(routing: ReadWriteRoutingDataSource): DataSource = LazyConnectionDataSourceProxy(routing)
```

| 컨벤션 | 부류 | 강제 |
|---|---|---|
| 라우팅 DataSource는 반드시 `LazyConnectionDataSourceProxy`로 감싼다. 감싸지 않으면 readOnly 여부가 정해지기 전에 커넥션을 먼저 얻어서 **모든 쿼리가 Primary로 간다** | 범용 | 리뷰 |
| 읽기 전용 서비스는 클래스에 `@Transactional(readOnly = true)`를 붙이고, 쓰기 메서드만 `@Transactional`로 덮어쓴다 | 범용 | 리뷰 |
| 읽기 전용 서비스는 `*QueryService`로 이름 짓는다. 이름만 보고 어느 DB로 가는지 알 수 있다 | 팀 | 리뷰 |
| **방금 쓴 데이터를 바로 읽어야 하는 경우**(복제 지연)는 쓰기 트랜잭션 안에서 읽거나 Primary를 명시한다 | 범용 | 리뷰 |
| 라우팅 관련 클래스는 `config`에만 둔다 | 범용 | 리뷰 |

Zed 관점: 어떤 메서드가 Replica로 가는지는 `readOnly` 속성으로만 정해진다. `*QueryService` 이름 규칙과 클래스 단위 `readOnly`가 그것을 코드에서 바로 보이게 한다.

## 2. CQRS

쓰기는 정규화된 RDB 엔티티로, 읽기는 비정규화된 조회 전용 테이블이나 다른 저장소(Elasticsearch 등)로 한다. **out 포트 헥사고날을 쓴다.**

```kotlin
// application/port/out
interface SaveOrderPort { fun save(order: Order): Order }                       // 쓰기 모델 (엔티티)
interface OrderSummaryQueryPort { fun search(cond: OrderSearchCondition): Page<OrderSummary> }  // 읽기 모델 (DTO)

// application/service
class OrderCommandService(private val saveOrderPort: SaveOrderPort, ...)
class OrderQueryService(private val orderSummaryQueryPort: OrderSummaryQueryPort)
```

| 컨벤션 | 부류 | 강제 |
|---|---|---|
| 쓰기와 읽기 서비스를 나눈다: `*CommandService`, `*QueryService` | 팀 | 리뷰 |
| 읽기 포트는 엔티티가 아니라 조회 전용 DTO를 반환한다 | 범용 | 리뷰 |
| 읽기 모델은 쓰기 모델의 이벤트로 갱신한다. 갱신은 커밋 후에 한다 | 범용 | 리뷰 ([이벤트 드리븐](event-driven.md)) |
| 읽기 모델은 늦게 반영될 수 있다(최종 일관성). 화면·API 문서에 그 사실을 적는다 | 범용 | 리뷰 |
| 읽기 모델 갱신 처리는 멱등하게 만든다. 같은 이벤트가 두 번 와도 결과가 같아야 한다 | 범용 | 리뷰 |

## 3. 고르는 기준

- 읽기 부하가 문제일 뿐이면 Replica 라우팅. 코드 변경이 거의 없다.
- 조회 화면이 여러 테이블을 조인하는 복잡한 검색이고 쓰기 모델과 모양이 크게 다르면 CQRS.
- 처음부터 CQRS로 시작하지 않는다. Replica 라우팅이나 조회 전용 JDSL 쿼리로 버티다가 필요해지면 해당 조회부터 분리한다.

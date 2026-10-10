# 캐시 (Redis)

캐시는 쓰는 방식에 따라 두 경우로 나뉜다. Spring 캐시 추상화로 충분하면 포트가 필요 없고, 캐시 로직을 직접 다루면 포트 뒤로 숨긴다.

## 1. Spring 캐시 추상화 (`@Cacheable`)

서비스는 캐시가 Redis인지 로컬 메모리인지 모른다. `CacheManager` 설정이 Spring의 포트·어댑터 역할을 한다. **구조와 무관하게 포트를 두지 않는다.**

```kotlin
// config/CacheNames.kt — 캐시 이름은 여기에만
object CacheNames {
    const val STOCK_SNAPSHOT = "stock-snapshot"
}

// application
@Service
class StockQueryService(private val loadStockPort: LoadStockPort) {
    @Cacheable(cacheNames = [CacheNames.STOCK_SNAPSHOT], key = "#sku", sync = true)
    fun snapshot(sku: String): StockSnapshot = StockSnapshot.from(loadStockPort.load(sku))
}
```

| 컨벤션 | 부류 | 강제 |
|---|---|---|
| 캐시 이름은 `config/CacheNames`의 상수로만 쓴다. 문자열 직접 사용 금지. 상수의 사용처 찾기로 캐시를 쓰는 곳이 전부 나온다 | 팀 | 훅 (`cache/name-constant`) |
| 캐시별 TTL은 `config`의 CacheManager 설정에서 정한다. TTL 없는 캐시를 만들지 않는다 | 범용 | 리뷰 |
| `key`를 명시한다. 기본 키 생성(모든 인자 조합)에 기대지 않는다 | 범용 | 리뷰 |
| **JPA 엔티티를 캐시하지 않는다.** 지연 로딩 프록시와 직렬화가 충돌한다. 캐시 전용 DTO(`*Snapshot`)를 만든다 | 범용 | 리뷰 |
| 직렬화는 JSON(Kotlin 모듈 등록)으로 한다. JDK 직렬화를 쓰지 않는다 | 범용 | 리뷰 |
| 동시에 같은 키가 비어 있으면 DB로 몰리는 문제(캐시 스탬피드)를 막으려면 `sync = true` | 범용 | 리뷰 |
| 같은 클래스 안에서 `@Cacheable` 메서드를 호출하지 않는다(프록시를 거치지 않음) | 범용 | 리뷰 |
| 쓰기 트랜잭션 안에서 무효화하면 롤백 시 캐시만 지워지거나, 커밋 전에 다시 채워질 수 있다. CacheManager를 `transactionAware`로 설정하거나 `@TransactionalEventListener(AFTER_COMMIT)`에서 무효화한다 | 범용 | 리뷰 |

## 2. 캐시 로직을 직접 다루는 경우

상황별 TTL, 부분 갱신, 카운터, 분산 락처럼 `RedisTemplate`을 직접 써야 하는 경우다. 서비스에 Redis 코드가 섞이지 않게 포트 뒤로 숨긴다.

```kotlin
// application/port/out
interface StockCachePort {
    fun get(sku: String): StockSnapshot?
    fun put(sku: String, snapshot: StockSnapshot, ttl: Duration)
    fun evict(sku: String)
}

interface LockPort {
    fun <T> withLock(key: String, waitTime: Duration, block: () -> T): T
}

// adapter/out/cache
@Component
class StockRedisAdapter(private val redis: StringRedisTemplate, ...) : StockCachePort { ... }

@Component
class RedissonLockAdapter(private val redisson: RedissonClient) : LockPort { ... }
```

| 컨벤션 | 부류 | 강제 |
|---|---|---|
| `RedisTemplate`, `RedissonClient`는 `adapter/out/cache`(계층형: `infrastructure`)와 `config`에서만 쓴다 | 범용 | 훅 (`arch/tech-client-outside-adapter`) |
| 분산 락은 `LockPort` 하나로 감싼다. 락 대기 시간과 보유 시간을 항상 명시한다 | 범용 | 리뷰 |
| 락 안에서 트랜잭션을 시작한다(락 → 트랜잭션 → 커밋 → 락 해제). 반대 순서면 커밋 전에 락이 풀린다 | 범용 | 리뷰 |
| Redis 키는 `<앱>:<대상>:<id>` 형식이고, 키 생성 함수는 어댑터 안에 하나만 둔다 | 팀 | 리뷰 |

## 3. Zed 관점

- IntelliJ도 캐시 이름 문자열을 따라가 주지 않는다. 캐시 이름 상수화는 IDE와 무관하게 유효하다.
- 캐시가 끼면 "왜 값이 안 바뀌지?"를 디버거로 보기 어렵다. 로컬에서는 캐시 적중·누락을 DEBUG 로그로 남기고(`logging.level.org.springframework.cache=TRACE`), 테스트에서는 캐시를 끄거나 Testcontainers Redis로 검증한다.

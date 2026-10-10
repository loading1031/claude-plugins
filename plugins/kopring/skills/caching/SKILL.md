---
name: caching
description: @Cacheable과 Redis 캐시 규칙(캐시 이름 상수, 엔티티 캐시 금지, 커밋 후 무효화, 분산 락 순서). 캐시를 다룰 때 사용
paths: "**/*.kt"
user-invocable: false
---

# 캐시

근거: ${CLAUDE_SKILL_DIR}/../../docs/architecture/cache.md

- 단순 조회 캐시는 `@Cacheable`로 한다. 이 경우 포트를 만들지 않는다.
- 캐시 이름은 `config/CacheNames`의 상수로만 쓴다: `@Cacheable(cacheNames = [CacheNames.STOCK_SNAPSHOT], key = "#sku")`
- `key`를 명시하고, 캐시별 TTL은 `config`의 CacheManager 설정에서 정한다.
- JPA 엔티티를 캐시하지 않는다. 캐시 전용 DTO(`*Snapshot`)를 반환하는 메서드에 붙인다.
- 같은 클래스 안에서 `@Cacheable` 메서드를 호출하지 않는다.
- 쓰기 후 무효화는 커밋 후에 일어나게 한다(transactionAware CacheManager 또는 `@TransactionalEventListener(AFTER_COMMIT)`).
- 상황별 TTL, 카운터, 분산 락처럼 `RedisTemplate`이 필요하면 `StockCachePort`/`LockPort` 같은 out 포트를 만들고 `adapter/out/cache`(계층형: `infrastructure`)에서 구현한다.
- 분산 락은 락 → 트랜잭션 → 커밋 → 락 해제 순서로 건다.

훅이 `cache/name-constant`, `arch/tech-client-outside-adapter` 위반을 차단한다.

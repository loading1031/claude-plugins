---
name: persistence
description: JPA 영속성과 Kotlin JDSL 쿼리 규칙(@Query 금지, 이름 규칙 메서드 조건 2개까지). Repository나 쿼리를 쓸 때 사용
paths: "**/*.kt"
user-invocable: false
---

# 영속성과 쿼리: Kotlin JDSL

근거: ${CLAUDE_SKILL_DIR}/../../docs/conventions/persistence.md. Zed + Kotlin LSP는 이름 규칙 메서드와 문자열 JPQL을 검사하지 못하므로, 쿼리는 컴파일러가 검사하는 Kotlin JDSL로 쓴다.

- 쓸 수 있는 순서:
  1. `JpaRepository` 기본 메서드 (`save`, `findById`, `findAll`, `delete` …)
  2. 조건 2개 이하의 이름 규칙 메서드 (`findBySku`, `findByLocationCodeAndSku`)
  3. 그 외 전부 Kotlin JDSL
- `@Query`, `@NativeQuery`, `EntityManager.createQuery/createNativeQuery`를 쓰지 않는다.
- Repository는 영속성 어댑터(계층형: `infrastructure`, 헥사고날: `adapter/out/persistence`)에 두고 `JpaRepository<T, ID>, KotlinJdslJpqlExecutor`를 함께 상속한다. 헥사고날이면 같은 패키지의 어댑터가 out 포트를 구현하고, 서비스는 포트만 쓴다.
- 동적 조건은 `and(...)` 안에 `값?.let { 조건 }`을 넣어 null이면 생략되게 한다.
- 필드는 문자열이 아니라 프로퍼티 참조(`Stock::sku`)로 쓴다.
- `@Entity`를 `data class`로 만들지 않는다.
- 네이티브 SQL이 꼭 필요해 보이면 직접 쓰지 말고 사용자에게 사유와 함께 먼저 물어본다.

```kotlin
interface StockRepository : JpaRepository<Stock, Long>, KotlinJdslJpqlExecutor

fun StockRepository.findAvailable(locationCode: String, sku: String?) = findAll {
    select(entity(Stock::class))
        .from(entity(Stock::class), join(Stock::location))
        .where(
            and(
                path(Location::code).eq(locationCode),
                sku?.let { path(Stock::sku).eq(it) },
                path(Stock::quantity).gt(0),
            )
        )
}
```

훅이 `jdsl/no-string-query`, `jdsl/no-create-query`, `jdsl/derived-query-max-2`, `jpa/no-data-class-entity` 위반을 차단한다.

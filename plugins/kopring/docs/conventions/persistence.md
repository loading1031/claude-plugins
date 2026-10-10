# 영속성과 쿼리

Zed + Kotlin LSP는 Spring Data 이름 규칙 메서드와 문자열 JPQL을 검사하지 못한다. 쿼리는 컴파일러가 검사하는 **Kotlin JDSL**로 쓴다. 선택 근거는 [환경 문서 4.1](../environment/zed.md#41-쿼리-kotlin-jdsl-채택).

## 1. 이름 규칙 메서드를 편집 중에 검사할 수 없다

`findByLocationCodeAndSku` 같은 메서드는 Spring이 앱 시작 시 이름을 해석해 구현한다. Kotlin LSP는 이름의 의미를 모르기 때문에 오타나 없는 필드를 알려 주지 못한다.

| 컨벤션 | 부류 | 강제 |
|---|---|---|
| 이름 규칙 메서드는 **조건 2개까지만** 쓴다 | 팀 | 훅 (`jdsl/derived-query-max-2`) |
| 조건이 3개 이상이거나, 동적 조건·조인·정렬 조합이 필요하면 Kotlin JDSL로 쓴다 | 팀 | 위와 같음 |
| 이름 규칙 메서드 오류는 컨텍스트 로딩 테스트로 잡는다 | 범용 | 테스트 ([테스트](testing.md)) |

## 2. 문자열 JPQL을 검사할 수 없다

| 컨벤션 | 부류 | 강제 |
|---|---|---|
| `@Query`, `@NativeQuery`를 쓰지 않는다 | Zed | 훅 (`jdsl/no-string-query`) |
| `EntityManager.createQuery/createNativeQuery`에 문자열 쿼리를 쓰지 않는다 | Zed | 훅 (`jdsl/no-create-query`) |
| 쿼리는 Kotlin JDSL로 쓴다. Repository는 `KotlinJdslJpqlExecutor`를 상속한다 | 팀 | 리뷰 |
| 네이티브 SQL이 꼭 필요하면(통계·벌크 처리 등) 별도 `*QueryDao` 클래스에 모으고 PR에 사유를 적는다. 훅이 막으므로 사람이 직접 작성한다 | 팀 | 리뷰 |

`@Query` 금지는 막힌 사람이 문자열 조립 같은 더 나쁜 우회를 하게 만들 위험이 있다. 그래서 네이티브 SQL용 예외 경로를 둔다.

## 3. 쓰는 순서

1. `JpaRepository` 기본 메서드 (`save`, `findById`, `findAll`, `delete` …)
2. 조건 2개 이하의 이름 규칙 메서드 (`findBySku`, `findByLocationCodeAndSku`)
3. 그 외 전부 Kotlin JDSL

## 4. 위치

| 구조 | Repository 위치 |
|---|---|
| 계층형 | `infrastructure` |
| 헥사고날 | `adapter/out/persistence`. application은 `port/out`의 인터페이스에만 의존한다 |

`JpaRepository`는 Spring 타입이라 `domain`에 두지 않는다(`domain/no-spring`). 구조 선택은 [아키텍처 선택](../architecture/choosing.md).

## 5. 예시

```kotlin
interface StockRepository : JpaRepository<Stock, Long>, KotlinJdslJpqlExecutor

fun StockRepository.findAvailable(locationCode: String, sku: String?) = findAll {
    select(entity(Stock::class))
        .from(entity(Stock::class), join(Stock::location))
        .where(
            and(
                path(Location::code).eq(locationCode),
                sku?.let { path(Stock::sku).eq(it) },   // null이면 조건 생략
                path(Stock::quantity).gt(0),
            )
        )
}
```

- 필드는 문자열이 아니라 프로퍼티 참조(`Stock::sku`)로 쓴다.
- 동적 조건은 `and(...)` 안에 `값?.let { 조건 }`을 넣어 null이면 생략되게 한다.

엔티티 작성 규칙(`data class` 금지, `plugin.jpa`)은 [Kotlin + Spring 기본](kotlin-spring.md).

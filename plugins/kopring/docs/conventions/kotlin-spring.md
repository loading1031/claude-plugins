# Kotlin + Spring 기본

Kotlin 클래스는 기본이 `final`이고, `data class`는 `equals`/`hashCode`/`toString`을 자동으로 만든다. 둘 다 Spring 프록시와 JPA 지연 로딩과 충돌한다.

| 컨벤션 | 부류 | 강제 |
|---|---|---|
| `kotlin("plugin.spring")`을 적용한다. `@Transactional`, `@Cacheable` 등 프록시가 동작하려면 클래스가 열려 있어야 한다 | 범용 | 빌드 설정 |
| `kotlin("plugin.jpa")`를 적용한다. JPA 엔티티에 인자 없는 생성자를 만들어 준다 | 범용 | 빌드 설정 |
| `@Entity`를 `data class`로 만들지 않는다. 자동 생성된 `equals`/`hashCode`/`toString`이 지연 로딩 연관을 건드린다 | 범용 | 훅 (`jpa/no-data-class-entity`) |
| 상태를 가진 객체를 Kotlin `object`로 만들지 않는다. 진짜 전역 싱글톤이 되어 테스트와 동시성 문제가 생긴다 | 범용 | 리뷰 |
| JSON 직렬화에 `jackson-module-kotlin`을 쓴다. 없으면 기본값·nullable 처리가 깨진다 | 범용 | 빌드 설정 |
| 같은 클래스 안에서 `@Transactional`, `@Cacheable` 메서드를 직접 호출하지 않는다(self-invocation). 프록시를 거치지 않아 동작하지 않는다 | 범용 | 리뷰 |

```kotlin
// build.gradle.kts
plugins {
    kotlin("plugin.spring")
    kotlin("plugin.jpa")
}
```

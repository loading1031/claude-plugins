---
name: dependency-injection
description: 생성자 주입, @Bean 등록과 구현체 선택은 config에서만, Config 이름·크기 규칙. 빈을 정의하거나 주입할 때 사용
paths: "**/*.kt"
user-invocable: false
---

# 의존성 주입

근거: ${CLAUDE_SKILL_DIR}/../../docs/conventions/dependency-injection.md. Zed에는 "이 자리에 어떤 빈이 주입되나"를 보여 주는 기능이 없으므로, 주입 관계가 코드에 그대로 드러나게 쓴다.

- 생성자 주입만 쓴다. 생성자가 하나면 `@Autowired`를 붙이지 않는다.
- `@Autowired`, `@Inject`, `lateinit var` 필드 주입을 쓰지 않는다. 테스트 코드(`src/test`)는 예외.
- 구현체가 여러 개인 인터페이스는 `@Component`로 자동 등록하지 않는다. `config`의 `@Configuration`에서 `@Bean`으로 명시 등록한다.
- `@Primary`, `@Qualifier`, `@Profile`, `@ConditionalOn*`은 `config` 패키지에서만 쓴다.
- 도메인 객체를 빈으로 쓰려면 `config`의 `@Bean` 메서드로 등록한다. 의존 빈은 메서드 인자로 받는다(다른 `@Bean` 메서드를 직접 호출하지 않는다).
- `@Configuration`은 기능 하나당 하나로 만들고 이름은 `<기능>Config`로 한다(`AllocationConfig`, `LabelPrinterConfig`). `AppConfig`, `CommonConfig`처럼 기능이 드러나지 않는 이름은 쓰지 않는다.
- Config 하나에 `@Bean`은 6개까지. 넘치면 기존 Config에 밀어 넣지 말고 기능별로 나눈다. "구현체 선택은 config에서만" 규칙 때문에 모든 빈이 한 파일에 몰리는 것을 막는 규칙이다.

```kotlin
@Configuration
class AllocationConfig {
    @Bean
    fun allocationPolicy(props: AllocationProperties): AllocationPolicy = when (props.policy) {
        "FIFO" -> FifoPolicy()
        else -> LifoPolicy()
    }

    @Bean
    fun stockAllocator(policy: AllocationPolicy) = StockAllocator(policy)
}
```

훅이 `di/no-autowired`, `di/selection-in-config-only`, `domain/no-spring`, `config/generic-name`, `config/too-many-beans` 위반을 차단한다. 차단되면 규칙을 우회하지 말고 위 방식으로 고친다.

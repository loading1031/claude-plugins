# 의존성 주입

IntelliJ Ultimate는 주입 지점 옆에 실제 주입될 빈을 보여 주지만, Kotlin LSP는 타입 정의와 구현체 목록까지만 보여 준다. 주입 관계가 **코드에 그대로 드러나게** 쓴다.

## 1. "이 자리에 어떤 빈이 주입되는지"를 실행 전에 볼 수 없다

| 컨벤션 | 부류 | 강제 |
|---|---|---|
| **생성자 주입만** 쓴다. 생성자가 하나면 `@Autowired`를 붙이지 않는다. `@Autowired`, `@Inject`, `lateinit var` 주입 금지 (테스트 제외) | 범용 | 훅 (`di/no-autowired`) |
| 구현체 선택(`@Primary`, `@Qualifier`, `@Profile`, `@ConditionalOn*`)은 **`config` 패키지의 `@Configuration`에서만** 한다 | Zed | 훅 (`di/selection-in-config-only`) |
| 구현체가 여러 개인 인터페이스는 `@Component`로 자동 등록하지 않고 `@Bean`으로 명시 등록한다 | Zed | 리뷰 |
| `@Bean` 메서드의 의존 빈은 메서드 인자로 받는다. 다른 `@Bean` 메서드를 직접 호출하지 않는다 | 범용 | 리뷰 |
| 실제로 주입된 구현은 디버거로 확인한다 | — | — |

## 2. 거대한 Config를 막는다

1번의 두 "Zed" 규칙만 기계적으로 지키면 모든 `@Bean`이 한 파일에 몰리는 **거대한 Config** 안티패턴이 생긴다. 다음은 그것을 막는 짝 규칙이다.

| 컨벤션 | 부류 | 강제 |
|---|---|---|
| `@Configuration`은 **기능 하나당 하나**, 이름은 `<기능>Config` (`LabelPrinterConfig`, `AllocationConfig`) | 범용 | 훅 (`config/generic-name`) |
| Config 하나에 `@Bean`은 **6개까지**. 넘으면 기능별로 나눈다 | 팀 | 훅 (`config/too-many-beans`) |

```
config/
├── AllocationConfig.kt     할당 정책 선택
├── LabelPrinterConfig.kt   프린터 선택 (local이면 콘솔)
├── CarrierConfig.kt        택배사 클라이언트
└── CoroutineConfig.kt      Dispatcher, CoroutineScope
```

```kotlin
@Configuration
class LabelPrinterConfig {
    @Bean @Profile("local")
    fun consoleLabelPrinter(): LabelPrinter = ConsoleLabelPrinter()

    @Bean @Profile("!local")
    fun zebraLabelPrinter(props: LabelPrinterProperties): LabelPrinter = ZebraLabelPrinter(props.host)
}
```

"프린터는 어떻게 고르지?"의 답이 `LabelPrinterConfig.kt` 한 파일에 있어서, 사용처 찾기만으로 추적할 수 있다.

비교: IntelliJ에서 흔한 방식은 구현 클래스에 직접 `@Component @Profile("local")`을 붙이는 것이다. 짧지만, 어떤 구현이 들어가는지 알려면 구현 클래스를 전부 열어 봐야 한다. IntelliJ는 주입 지점 아이콘으로 바로 보여 주지만 Zed는 그렇지 않다.

## 3. 컴포넌트 스캔으로 등록된 빈은 생성 지점이 코드에 없다

| 컨벤션 | 부류 | 강제 |
|---|---|---|
| `domain` 패키지는 **Spring에 의존하지 않는다**(`org.springframework.*` import 금지). 도메인 객체를 빈으로 쓰려면 `config`의 `@Bean`으로 등록한다 | 범용 | 훅 (`domain/no-spring`), ArchUnit |
| `@Service`, `@Repository`, `@RestController`는 application·어댑터 계층에서 자유롭게 쓴다. 구현체가 하나뿐이라 헷갈릴 일이 없다 | 범용 | ArchUnit |
| JPA 애너테이션(`jakarta.persistence`)은 `domain` 엔티티에 허용한다. 도메인 모델과 JPA 엔티티를 분리할 필요가 생기면 다시 검토한다 | 팀 | — |

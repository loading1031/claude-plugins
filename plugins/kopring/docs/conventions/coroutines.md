# 코루틴

코루틴 디버깅의 어려움은 두 종류다. **코루틴 자체의 특성**에서 오는 것은 컨벤션으로 원인을 없앨 수 있고, **Zed에 디버거가 없어서** 생기는 것은 영향 범위를 줄이는 수밖에 없다.

## 1. 가장 중요한 규칙: 코루틴은 경계에만

| 컨벤션 | 부류 | 강제 |
|---|---|---|
| `domain`은 **동기 코드**로 쓴다. `suspend`와 `kotlinx.coroutines`를 쓰지 않는다 | 팀 | 훅 (`domain/no-coroutines`) |
| 코루틴은 웹 진입(WebSocket, SSE)과 외부 호출 어댑터에서만 쓴다 | 팀 | 리뷰 |
| `@Transactional` 계층(application 서비스)은 동기 코드로 쓴다 | 범용 | 훅 (`coroutine/no-suspend-transactional`) |

디버깅이 가장 많이 필요한 비즈니스 규칙이 코루틴 문제에서 벗어나고, Spring 없이 단위 테스트로 검증된다. JPA 기반 앱이라서 맞는 규칙이다. 완전한 리액티브(WebFlux + R2DBC) 앱이라면 다시 검토한다.

## 2. 어려운 점별 컨벤션

| 어려운 점 | 원인 | 컨벤션 | 부류 | 강제 |
|---|---|---|---|---|
| 스택 트레이스가 끊김 | `suspend` 이후 다른 스레드에서 재개되어 호출한 쪽이 스택에서 사라짐 | 로컬·테스트 실행에 `-Dkotlinx.coroutines.debug`를 켠다. 예외 스택 트레이스가 복원되고 스레드 이름에 `@코루틴이름#N`이 붙는다 | 범용 | 빌드 설정 |
| 로그로 어느 코루틴인지 구분 불가 | 여러 코루틴이 같은 스레드 풀을 번갈아 씀 | `launch`/`async`에는 `CoroutineName`을 붙인다. 로그 MDC는 `MDCContext()`로 넘긴다 | 범용 | 훅 (`coroutine/name-required`) |
| 어떤 코루틴이 어디서 멈췄는지 모름 | 스레드 덤프에 suspend된 코루틴이 안 보임 | `local` 프로필에서 `DebugProbes.install()`, 필요할 때 `DebugProbes.dumpCoroutines()` | 범용 | 설정 코드 |
| 예외가 사라짐 | `GlobalScope`로 띄운 코루틴은 수명과 예외를 아무도 관리하지 않음 | `GlobalScope` 금지. `config`에서 만든 `CoroutineScope`를 주입받는다 | 범용 | 훅 (`coroutine/no-global-scope`), detekt `GlobalCoroutineUsage` |
| 취소가 삼켜짐 | `runCatching` 안의 suspend 호출이 `CancellationException`까지 잡음 | suspend 호출을 `runCatching`으로 감싸지 않는다. `catch (e: Exception)`에서는 `CancellationException`을 다시 던진다 | 범용 | detekt `SuspendFunSwallowedCancellation` |
| 스레드가 막힘 | 메인 코드의 `runBlocking`이 요청 스레드를 붙잡음 | 메인 코드에서 `runBlocking` 금지 (테스트는 `runTest` 권장) | 범용 | 훅 (`coroutine/no-run-blocking`) |
| 트랜잭션·MDC·보안 컨텍스트 유실 | JPA 트랜잭션 등은 ThreadLocal 기반인데 코루틴은 재개될 때 스레드가 바뀜 | `@Transactional` 계층에 `suspend fun`을 쓰지 않는다. DB 호출은 호출 측에서 `withContext(ioDispatcher)`로 감싼다 | 범용 | 훅 (`coroutine/no-suspend-transactional`) |
| 타이밍에 따라 재현되다 말다 함 | 실제 스레드와 시간에 의존 | `Dispatchers.IO/Default`를 직접 쓰지 않고 주입받는다. 테스트는 `runTest`의 가상 시간으로 결정적으로 실행한다 | 범용 | 훅 (`coroutine/inject-dispatcher`), detekt `InjectDispatcher`, `CoroutineLaunchedInTestWithoutRunTest` |
| 변수가 "optimized out"으로 안 보임 | suspend 이후 안 쓰는 변수를 컴파일러가 버림 | 디버깅할 때만 Kotlin 컴파일러 옵션 `-Xdebug`를 켠다(`-PcoroutineDebug`). **운영 빌드 금지**(메모리 누수 위험) | 범용 | 빌드 설정 |
| 브레이크포인트로 멈춰서 볼 수 없음 | Zed 화면에 Kotlin 디버거가 연결되어 있지 않음 | IntelliJ로 attach한다. 코루틴 패널을 보려면 디버그 에이전트를 붙인다(아래). Kotlin LSP의 DAP 디버거는 코루틴 안의 브레이크포인트도 잡는 것을 확인했다([환경 3.3](../environment/zed.md#33-검증-kotlin-lsp의-dap-디버거는-동작한다-2026-10-09)). **IntelliJ attach 시 코루틴 패널은 아직 검증하지 않음** | Zed | — |

각 행이 실제로 성립하는지는 `examples/debugging`의 테스트로 확인한다. 같은 상황을 "컨벤션 없이"(`./gradlew testWithoutConvention`)와 "컨벤션 적용"(`./gradlew test`)으로 나눠 재현한다.

그 밖의 규칙(detekt 기본 규칙과 같음): `Thread.sleep` 대신 `delay`, suspend 함수가 `Flow`를 반환하지 않게 한다.

## 3. 예시

```kotlin
// config/CoroutineConfig.kt — Dispatcher와 Scope를 만드는 유일한 곳
@Configuration
class CoroutineConfig {
    // Dispatchers.IO는 공용 객체라 닫을 수 없다. destroyMethod를 비우지 않으면 Spring이 종료 시 close()를 추론해 호출하다 예외가 난다
    @Bean(destroyMethod = "")
    fun ioDispatcher(): CoroutineDispatcher = Dispatchers.IO

    @Bean
    fun applicationScope(): CoroutineScope = ApplicationScope()
}

// cancel()은 CoroutineScope의 확장 함수라 @Bean(destroyMethod = "cancel")로 지정할 수 없다
class ApplicationScope :
    CoroutineScope by CoroutineScope(SupervisorJob() + Dispatchers.Default + CoroutineName("app")),
    DisposableBean {
    override fun destroy() = cancel()
}

// 웹 진입 계층: 이름 붙은 코루틴, 주입받은 Dispatcher
class StockStreamPublisher(
    private val scope: CoroutineScope,
    private val io: CoroutineDispatcher,
    private val stockQueryService: StockQueryService,   // 동기 @Transactional 서비스
) {
    fun start(sku: String) = scope.launch(CoroutineName("stock-stream-$sku") + MDCContext()) {
        val snapshot = withContext(io) { stockQueryService.snapshot(sku) }  // DB는 동기, 호출 측에서 io로
        // ...
    }
}
```

## 4. 디버깅 설정

```kotlin
// build.gradle.kts
tasks.named<org.springframework.boot.gradle.tasks.run.BootRun>("bootRun") {
    jvmArgs("-Dkotlinx.coroutines.debug")
    providers.gradleProperty("ideaAgent").orNull?.let { jvmArgs("-javaagent:$it") }  // IntelliJ attach용
}
tasks.test {
    jvmArgs("-Dkotlinx.coroutines.debug")
}
kotlin {
    compilerOptions {
        if (project.hasProperty("coroutineDebug")) freeCompilerArgs.add("-Xdebug")  // 로컬 디버깅 전용
    }
}
```

IntelliJ로 attach할 때 디버그 에이전트를 붙여 실행한다.

```sh
./gradlew bootRun --debug-jvm \
  -PideaAgent="/Applications/IntelliJ IDEA.app/Contents/plugins/java/lib/rt/debugger-agent.jar"
```

이 상태로 IntelliJ의 "Remote JVM Debug"(포트 5005)로 붙는다. 코루틴 패널이 실제로 뜨는지는 예시 프로젝트에서 검증한 뒤 이 문서를 고친다.

## 참고

- [kotlinx-coroutines-debug](https://github.com/Kotlin/kotlinx.coroutines/blob/master/kotlinx-coroutines-debug/README.md)
- [detekt – Coroutines rule set](https://detekt.dev/docs/rules/coroutines/)
- [IntelliJ IDEA – Attach to process](https://www.jetbrains.com/help/idea/attach-to-process.html)

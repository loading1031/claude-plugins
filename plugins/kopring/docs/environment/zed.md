# Zed로 Kotlin + Spring 개발하기

- 작성일: 2026-10-09
- 상태: 채택

이 문서는 Kotlin + Spring Boot를 **Zed 에디터**로 개발할 때 어떤 도구를 쓰는지, 그 때문에 어떤 기능을 쓸 수 없는지, 그 공백을 어떤 기술 선택과 컨벤션으로 메우는지를 기록한다.

## 1. 기술 스택

| 구분 | 선택 |
|---|---|
| 언어 | Kotlin |
| 프레임워크 | Spring Boot |
| 빌드 | Gradle (Kotlin DSL, Gradle Wrapper) |
| 영속성 | Spring Data JPA + **Kotlin JDSL** |
| JDK | 21 이상 |
| 에디터 | Zed |

## 2. 에디터: Zed와 확장

| 확장 | 제공하는 것 | 사용 여부 |
|---|---|---|
| **Kotlin** (`zed-extensions/kotlin`) | Kotlin 문법 강조, 자동완성, 정의로 이동, 사용처 찾기, 이름 바꾸기, 진단. 언어 서버는 JetBrains 공식 **Kotlin LSP**(무료)를 기본으로 사용 | 사용 |
| **Java** | Eclipse JDT LS 기반 Java 지원, `.gradle.kts` 강조·진단, `.properties` 지원 | 사용 (빌드 스크립트·설정 파일용) |
| Spring Tools (`zed-spring-tools`) | Broadcom Spring Tools 기반 `application.yml`/`.properties` 자동완성, Spring 관련 Java 진단 | **사용 안 함** (아래 참고) |

Spring Tools를 쓰지 않는 이유:

- Zed 공식 레지스트리에 아직 등록되지 않았다(2026-07 등록 PR이 열려 있으나 병합 전). Dev Extension으로 직접 설치해야 하고, 작성자도 안정 버전이 아니라고 밝히고 있다.
- Broadcom Spring Tools는 공식적으로 **Java 소스만 지원**한다. `.kt` 파일 안의 Spring 기능(빈 탐색, 매핑 목록, 진단)은 동작하지 않는다.
- Java 언어 서비스는 `.java` 파일이 열려 있어야 시작되는데, 순수 Kotlin 프로젝트에는 `.java` 파일이 없다.

## 3. Zed 환경에서 쓸 수 없는 기능

IntelliJ IDEA Ultimate와 비교했을 때 Zed + Kotlin LSP에 없는 기능이다.

### 3.1 디버깅

| 기능 | 상태 |
|---|---|
| Zed 안에서 Kotlin 브레이크포인트 디버깅 | **공식 확장에서는 불가.** Zed Kotlin 확장에 디버그 어댑터가 없다. Kotlin LSP에 내장된 DAP 디버거는 정상 동작하고(3.3), 시제품 확장으로 Zed 안에서 attach·중단점·변수 확인까지 된다(3.4). 정식 지원은 업스트림에서 진행 중이다. |
| 코루틴 디버깅 (가상 스택, 코루틴 목록) | 불가 |
| Spring 디버거 (활성 프로필, 실제 적용된 설정값, 빈 정보 표시) | 불가. IntelliJ Ultimate 전용 |

### 3.2 Spring 관련 정적 분석·탐색

| 기능 | 영향 |
|---|---|
| Spring Data 이름 규칙 메서드(`findByLocationCodeAndSku`) 검사·자동완성 | 메서드 이름 오타나 없는 필드를 편집 중에 알 수 없다. 앱 시작 시 `PropertyReferenceException`으로 실패한다. |
| `@Query` 안의 JPQL 문자열 검사 | 문자열로만 취급된다. 오류는 앱 시작 시 드러난다. |
| 빈 연결 오류 사전 검사 ("주입할 빈 없음", "후보 2개") | 실행해야 알 수 있다. |
| 주입 지점 ↔ 빈 정의 이동 아이콘, Beans 창, 의존성 그래프 | 없다. 타입 정의로 이동, 구현으로 이동, 사용처 찾기로 대체한다. |
| 이벤트 발행 ↔ 리스너 이동 아이콘 | 없다. 누가 이벤트를 받는지 코드 탐색으로 알 수 없다. |
| Endpoints 창 (전체 HTTP 매핑 목록) | 없다. `Mapping` 텍스트 검색으로 대체한다. |
| `@Value("${...}")` ↔ `application.yml` 이동 | 없다. |

일반 Kotlin 코드 탐색(정의로 이동, 구현으로 이동, 사용처 찾기, 이름 바꾸기)과 `JpaRepository` 기본 메서드(`save`, `findById` 등)의 자동완성·탐색은 정상 동작한다.

### 3.3 검증: Kotlin LSP의 DAP 디버거는 동작한다 (2026-10-09)

"Zed에서 `bootRun`을 디버그 대기로 띄우고 붙었는데 브레이크포인트가 안 잡힌다"는 사례가 있다. 같은 조건에서 무료 Kotlin LSP(`kotlin-server` 263.6379.0)의 DAP 디버거로 직접 붙어 확인했다. 예시 프로젝트는 `examples/debugging`, 검증 스크립트는 `scripts/dap/verify_kotlin_dap.py`다.

| 시나리오 | 결과 |
|---|---|
| 일반 요청 (`StockAllocator.kt:8`) | 멈춤. 요청 스레드, 호출 스택 3단계, 지역 변수(`requested=10, available=7, allocated=7`) 확인 |
| 코루틴 요청, `withContext(io)`로 스레드가 바뀐 뒤 (`AllocationController.kt:30`) | 멈춤. 스레드 이름 `DefaultDispatcher-worker-1 @allocate-B2#1`(코루틴 디버그 모드 + `CoroutineName` 컨벤션 덕분), 지역 변수 확인 |
| 그 코루틴 안에서 호출된 도메인 코드 | 멈춤. 변수 확인 |

순서: 앱을 `./gradlew bootRun --debug-jvm`으로 띄움 → `kotlin-server --stdio`에 프로젝트를 열고 임포트 완료 대기(약 25초) → LSP `workspace/executeCommand` `start_debug_server` → 받은 포트에 DAP로 연결 → `attach`(`hostName`, `port: 5005`) → `setBreakpoints` → `configurationDone`.

결론:

- 디버거 엔진에는 문제가 없다. 막혀 있는 건 **Zed 화면과의 연결**뿐이다.
- 인용된 실패 사례는 Java 확장(Eclipse JDT 기반 디버거)으로 붙었기 때문으로 추정한다. JDT 디버거는 `.kt` 소스를 이해하지 못해 브레이크포인트 위치를 클래스에 대응시키지 못한다. 그 사례의 정확한 설정은 확인하지 못했다.
- Zed 디버거 확장 API는 `debug-adapter-binary.connection`으로 **이미 떠 있는 DAP 서버에 TCP로 붙을 수 있다.** 따라서 "kotlin-server에서 `start_debug_server`로 포트를 받아 그 포트를 돌려주는" Zed 확장을 만들면 Zed 화면에서도 디버깅할 수 있다. 시제품으로 확인한 결과는 3.4에 있다.

### 3.4 검증: Zed 안에서 디버깅하기 (시제품, 2026-10-10)

Kotlin 확장을 고친 시제품(공개하지 않음)으로 Zed 1.23.2에서 attach, 중단점, Variables 패널, 중단점 사이 Continue가 동작하는 것을 확인했다. 정식 지원은 [zed-extensions/kotlin#121](https://github.com/zed-extensions/kotlin/issues/121)에서 논의한다.

Zed와 연결하려면 세 군데가 어긋난다.

| 어긋남 | 시제품의 처리 | 근본 해결 |
|---|---|---|
| Zed 확장 API는 언어 서버에 `workspace/executeCommand`를 보낼 수 없어 `start_debug_server`를 부를 수 없다 | Java 확장처럼 언어 서버 앞에 프록시를 두고 HTTP로 요청을 중계 | Zed 확장 API가 LSP 요청을 지원 ([zed#20042](https://github.com/zed-industries/zed/issues/20042)) |
| 서버는 DAP adapterID로 `intellij_jvm`만 받는다(`Kotlin`, `jvm`, `java`는 거부). Zed는 어댑터 이름을 adapterID로 보낸다 | 어댑터 이름을 `intellij_jvm`으로 지음 | 해결됨 |
| 서버는 `pathFormat`과 상관없이 스택 프레임의 `source.path`를 `file://` URI로 보낸다. VS Code는 받아 주지만 Zed는 파일과 연결하지 못해 Variables가 빈다 | 프록시가 일반 경로로 바꿈 | 서버 수정([Kotlin/kotlin-lsp#285](https://github.com/Kotlin/kotlin-lsp/issues/285)) 또는 Zed의 URI 허용([zed 토론 #65408](https://github.com/zed-industries/zed/discussions/65408)) |

알려진 제약:

- 서버는 JDWP 연결이 끝나기 전에 attach 성공을 돌려준다. attach 직후 몇 초 안에 실행된 코드는 중단점을 놓칠 수 있다.
- Zed는 DAP `invalidated` 이벤트를 처리하지 않는다. `this` 같은 객체 값이 `Collecting data…`로 남을 수 있다.
- Zed는 `continue` 응답이 다음 `stopped`보다 늦게 처리되면 멈춘 프로그램을 실행 중으로 표시할 수 있다([zed#65410](https://github.com/zed-industries/zed/issues/65410)).
- 코드 옆 인라인 값은 Kotlin용 `debugger.scm` 쿼리가 있어야 한다. 시제품에 추가했지만 Zed 화면에서는 확인하지 않았다.

## 4. 보완책

### 4.1 쿼리: Kotlin JDSL 채택

3.2의 "Spring Data 메서드 검사 불가"와 "JPQL 문자열 검사 불가"를 보완하기 위해, 조건이 있는 쿼리는 **Kotlin JDSL**로 작성한다.

- 필드를 문자열이 아니라 Kotlin 프로퍼티 참조(`Stock::sku`)로 쓰기 때문에 오타가 **컴파일 에러**가 된다. 별도 Spring 도구 없이 Kotlin LSP만으로 자동완성, 이름 바꾸기, 사용처 찾기가 된다.
- 코드 생성(KSP/kapt)이 없다. 엔티티를 바꾼 뒤 다시 빌드하기 전까지 LSP가 생성 클래스를 못 찾는 문제가 생기지 않아 Zed 환경과 잘 맞는다.
- Spring Data와는 `KotlinJdslJpqlExecutor`로 연동한다.

비교 후 채택하지 않은 것: **QueryDSL**(OpenFeign 포크 + KSP). 자료와 사례는 더 많지만 Q클래스 코드 생성이 필요하다. 빌드 설정이 늘고, 생성 전에는 LSP에서 빨간 줄이 생긴다.

### 4.2 컨벤션과 강제 수단

3장의 각 공백을 어떤 컨벤션으로 메우는지, 그 컨벤션을 무엇으로 강제하는지는 [컨벤션 목록](../conventions/README.md)에 정리했다.

| 3장의 공백 | 컨벤션 | 문서 |
|---|---|---|
| 이름 규칙 메서드·JPQL 검사 불가 | Kotlin JDSL, `@Query` 금지, 이름 규칙 메서드는 조건 2개까지 | [영속성](../conventions/persistence.md) |
| 주입될 빈을 미리 볼 수 없음 | 생성자 주입, 구현체 선택은 기능별 `@Configuration`에서만 | [의존성 주입](../conventions/dependency-injection.md) |
| 컴포넌트 스캔 빈의 생성 지점 없음 | `domain`은 Spring 비의존, `@Bean`으로 명시 등록 | [의존성 주입](../conventions/dependency-injection.md) |
| 빈 연결 오류 사전 검사 불가 | `@SpringBootTest` 컨텍스트 로딩 테스트 | [테스트](../conventions/testing.md) |
| `@Value` ↔ yml 이동 불가 | `@ConfigurationProperties`만 사용 | [설정값](../conventions/configuration.md) |
| 이벤트 발행 ↔ 리스너 추적 불가 | 이벤트 클래스를 허브로, 리스너는 구체 타입만 | [이벤트 드리븐](../architecture/event-driven.md) |
| Endpoints 창 없음 | 컨트롤러 위치·이름 규칙, 클래스 단위 경로 접두사 | [웹 API](../conventions/web-api.md) |
| Kotlin·코루틴 디버거 없음 | 코루틴은 경계에만, `domain`은 동기 코드. 코루틴 디버그 모드, `CoroutineName`, Dispatcher 주입 | [코루틴](../conventions/coroutines.md) |

### 4.3 디버깅

Zed 안에서 Kotlin 디버깅이 되기 전까지는 다음 방법으로 디버깅한다.

1. 앱을 디버그 포트를 열고 실행한다: `./gradlew bootRun --debug-jvm` (JDWP, 기본 포트 5005)
2. IntelliJ IDEA에서 **Run → Attach to Process** 또는 "Remote JVM Debug" 실행 구성으로 붙는다.
3. 편집은 Zed에서, 브레이크포인트와 변수 확인은 IntelliJ에서 한다.

JVM 디버깅은 표준 프로토콜(JDWP)을 쓰므로 Spring 앱도 일반 JVM 프로그램과 똑같이 디버깅된다. Spring 전용 디버거는 필요 없다.

디버거가 필요한 상황 자체를 줄이는 것이 우선이다. 핵심 규칙은 순수 동기 코드로 두고 단위 테스트한다([테스트](../conventions/testing.md), [코루틴](../conventions/coroutines.md)).

## 5. 검토했으나 채택하지 않은 디버깅 연동 방안

| 방안 | 내용 | 채택하지 않은 이유 |
|---|---|---|
| IntelliJ MCP 서버의 디버거 도구 | IntelliJ 2026.1.3+ 내장 MCP 서버가 `xdebug_*` 도구로 디버거를 외부에 노출. Zed 에이전트나 Claude Code가 조작 | AI 에이전트가 대신 조작하는 방식이라 Zed 디버거 화면과 연동되지 않는다. 필요할 때 보조로만 쓴다. |
| JetBrains `intellij-server` (Java and Kotlin by IntelliJ IDEA) | IntelliJ 엔진을 헤드리스로 실행해 LSP와 DAP, Spring 기능까지 제공 | 현재 EAP 약관상 평가 목적만 허용되고 프로덕션 사용이 금지된다. 정식 출시 후에는 IntelliJ Ultimate 구독이 필요하다. |
| 무료 Kotlin LSP(`kotlin-server`)의 DAP를 Zed에 직접 연결 | `intellij-server`와 같은 빌드, 같은 디버거 엔진, 무료 라이선스. `start_debug_server` 명령으로 DAP 포트를 받아 TCP로 연결하는 구조 | **채택.** 디버거 엔진 동작(3.3)과 시제품 확장의 Zed 연동(3.4)을 확인했다. 정식 지원은 업스트림 이슈로 진행 중이다. |
| IntelliJ에 DAP 서버 플러그인 직접 개발 | XDebugger API(공개)와 `lsp4j.debug`로 DAP 서버 구현 | 작업량이 크고 IntelliJ를 계속 띄워 둬야 한다. |
| `intellij-server` 플러그인을 IntelliJ에 이식 | — | 빌드 버전과 의존 모듈이 달라 동작하지 않고, EAP 약관(리버스 엔지니어링 금지)에 위배된다. |
| `fwcd/kotlin-debug-adapter` | 오픈소스 독립 Kotlin DAP | 유지보수가 느리고 코루틴 지원이 약하다. |

## 6. 재검토 시점

- Zed Kotlin 확장이 Kotlin LSP의 디버거(DAP)를 지원할 때 → 4.3을 Zed 내장 디버깅으로 교체하고, 부류가 "Zed"인 디버깅 관련 규칙을 다시 검토한다.
- 무료 Kotlin LSP DAP를 Zed에 연결하는 확장(3.3, 5장 후속 과제)이 완성되었을 때 → 같은 교체를 한다.
- `intellij-server`가 정식 출시되었을 때 → Ultimate 구독으로 Spring 정적 분석(3.2)까지 보완할지, 부류가 "Zed"인 규칙을 풀지 검토한다.

## 참고

- [Zed Kotlin 문서](https://zed.dev/docs/languages/kotlin)
- [Zed Debugger 문서](https://zed.dev/docs/debugger)
- [Kotlin LSP 릴리스](https://github.com/Kotlin/kotlin-lsp/releases)
- [IntelliJ IDEA – Agentic debugging](https://www.jetbrains.com/help/idea/agentic-debugging.html)
- [IntelliJ IDEA Goes LSP (JetBrains Blog)](https://blog.jetbrains.com/idea/2026/08/intellij-idea-goes-lsp/)
- [Spring Tool Suite and Kotlin](https://docs.spring.io/sts/nan/v373/SpringToolSuiteAndKotlin.html)
- [Zed Spring Tools 등록 PR #6875](https://github.com/zed-industries/extensions/pull/6875)
- [Kotlin JDSL](https://github.com/line/kotlin-jdsl)
- [OpenFeign QueryDSL](https://github.com/OpenFeign/querydsl)

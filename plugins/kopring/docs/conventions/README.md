# 컨벤션

Zed + Kotlin LSP 환경에는 IntelliJ Ultimate의 Spring 전용 분석·탐색 기능도, Kotlin 디버거도 없다([환경](../environment/zed.md)). 이 디렉터리는 그 공백을 **어떤 컨벤션으로 메우고, 무엇으로 강제하는지**를 주제별로 정리한다. 아키텍처 선택과 케이스별 규칙은 [architecture](../architecture/choosing.md)에 있다.

## 규칙의 부류

모든 규칙에 부류를 표시한다. 환경이 바뀌면(IntelliJ로 이동, Zed가 Kotlin 디버깅·Spring 분석을 지원) 부류를 보고 풀어도 되는 규칙을 고른다.

| 표시 | 뜻 | 환경이 바뀌면 |
|---|---|---|
| **범용** | IDE와 무관하게 권장되는 모범 사례 | 유지 |
| **팀** | 합리적이지만 팀이 정한 선택 | 팀이 다시 결정 |
| **Zed** | Zed의 공백을 메우려는 보정. IntelliJ에서는 과한 제약 | 풀어도 됨 |

## 강제 수단

| 수단 | 시점 | 위치 | 상태 |
|---|---|---|---|
| **Claude 훅** | Claude Code가 `.kt` 파일을 쓰거나 고치기 직전. 새로 생기는 위반만 차단 | `.claude/settings.json` → `scripts/conventions/check_kotlin_conventions.py` | 동작 |
| **pre-commit 훅** | 커밋할 때. 커밋되는 `.kt` 파일 전체 검사 | `.githooks/pre-commit` (같은 스크립트) | 동작 (활성화 필요) |
| **detekt** | `./gradlew detekt`, CI. 정규식으로 못 잡는 구조 규칙 | — | 설정 템플릿 예정 |
| **ArchUnit** | `./gradlew test`. 패키지 의존 방향 | — | 테스트 템플릿 예정 |
| **테스트** | `./gradlew test` | 컨텍스트 로딩 테스트 등 | 프로젝트별 |
| **리뷰** | PR | 도구로 잡을 수 없는 규칙 | — |
| **Claude 규칙** | Claude Code 작업 중 | `.claude/rules/*.md` | 동작 |

pre-commit 훅은 저장소마다 한 번 활성화한다.

```sh
git config core.hooksPath .githooks
```

## 문서

| 문서 | 다루는 공백 |
|---|---|
| [영속성](persistence.md) | 이름 규칙 메서드·JPQL 문자열 검사 불가 |
| [의존성 주입](dependency-injection.md) | 주입될 빈을 미리 볼 수 없음, 컴포넌트 스캔 빈의 생성 지점 없음 |
| [설정값](configuration.md) | `@Value` ↔ yml 이동 불가 |
| [웹 API](web-api.md) | Endpoints 창 없음 |
| [테스트](testing.md) | 빈 연결 오류 사전 검사 불가, 디버거 없음 |
| [코루틴](coroutines.md) | 코루틴 디버거 없음 |
| [Kotlin + Spring 기본](kotlin-spring.md) | Kotlin `final` 기본값과 Spring·JPA 충돌 |

## 검사 규칙 색인

검사 스크립트가 출력하는 `rule id` 전체 목록이다. "강제"가 "훅"인 규칙은 Claude 훅과 pre-commit 훅 둘 다 적용된다.

| rule id | 부류 | 내용 | 문서 |
|---|---|---|---|
| `jdsl/no-string-query` | Zed | `@Query`, `@NativeQuery` 금지 | [영속성](persistence.md) |
| `jdsl/no-create-query` | Zed | `createQuery/createNativeQuery` 문자열 쿼리 금지 | [영속성](persistence.md) |
| `jdsl/derived-query-max-2` | 팀 | 이름 규칙 메서드는 조건 2개까지 | [영속성](persistence.md) |
| `jpa/no-data-class-entity` | 범용 | `@Entity`를 `data class`로 만들지 않음 | [Kotlin + Spring 기본](kotlin-spring.md) |
| `di/no-autowired` | 범용 | `@Autowired`, `@Inject` 금지 (테스트 제외) | [의존성 주입](dependency-injection.md) |
| `di/selection-in-config-only` | Zed | `@Primary/@Qualifier/@Profile/@ConditionalOn*`은 `config`에서만 | [의존성 주입](dependency-injection.md) |
| `config/generic-name` | 범용 | `AppConfig`처럼 기능이 안 드러나는 Config 이름 금지 | [의존성 주입](dependency-injection.md) |
| `config/too-many-beans` | 팀 | Config 하나에 `@Bean` 6개까지 | [의존성 주입](dependency-injection.md) |
| `config/no-value` | 범용 | `@Value` 금지 | [설정값](configuration.md) |
| `domain/no-spring` | 범용 | `domain`에서 Spring import 금지 | [의존성 주입](dependency-injection.md) |
| `domain/no-coroutines` | 팀 | `domain`에서 `suspend`, 코루틴 금지 | [코루틴](coroutines.md) |
| `arch/domain-no-outer` | 범용 | `domain`이 바깥 계층 import 금지 | [아키텍처 선택](../architecture/choosing.md) |
| `arch/application-no-adapter` | 범용 | `application`이 `adapter` import 금지 (헥사고날) | [아키텍처 선택](../architecture/choosing.md) |
| `arch/tech-client-outside-adapter` | 범용 | Redis·Kafka·HTTP·JDBC 클라이언트는 어댑터와 `config`에서만 | [아키텍처 선택](../architecture/choosing.md) |
| `cache/name-constant` | 팀 | 캐시 이름 문자열 직접 사용 금지 | [캐시](../architecture/cache.md) |
| `event/listener-concrete-type` | Zed | 리스너는 구체 이벤트 타입 하나만 받음 | [이벤트 드리븐](../architecture/event-driven.md) |
| `event/topic-constant` | 범용 | 토픽·큐 이름 문자열 직접 사용 금지 | [이벤트 드리븐](../architecture/event-driven.md) |
| `coroutine/no-global-scope` | 범용 | `GlobalScope` 금지 | [코루틴](coroutines.md) |
| `coroutine/no-run-blocking` | 범용 | 메인 코드에서 `runBlocking` 금지 | [코루틴](coroutines.md) |
| `coroutine/name-required` | 범용 | `launch/async`에 `CoroutineName` 필수 | [코루틴](coroutines.md) |
| `coroutine/inject-dispatcher` | 범용 | `config` 밖에서 `Dispatchers.IO/Default` 금지 | [코루틴](coroutines.md) |
| `coroutine/no-suspend-transactional` | 범용 | `@Transactional` 파일에 `suspend fun` 금지 | [코루틴](coroutines.md) |

## 검사 스크립트의 한계

검사는 줄 단위 정규식이다(이벤트 리스너와 파일 단위 규칙만 여러 줄을 본다). 다음은 detekt·ArchUnit·리뷰로 확인한다.

- 여러 줄에 걸친 `launch(` 인자의 `CoroutineName` 여부 (첫 줄만 본다)
- suspend 호출을 감싼 `runCatching` → detekt `SuspendFunSwallowedCancellation`
- 계층 간 의존 방향 전체 → ArchUnit (검사 스크립트는 import 몇 가지만 본다)
- 구현체가 여러 개인 인터페이스의 `@Component` 자동 등록, 상태를 가진 `object`, 컨트롤러 경로 규칙 → 리뷰
- 패키지 이름이 이 컨벤션(`domain`, `application`, `adapter`, `infrastructure`, `api`, `config`)과 다르면 경로 기반 규칙이 동작하지 않는다.

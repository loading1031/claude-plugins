---
name: coroutines
description: 코루틴 사용 위치와 규칙(GlobalScope·runBlocking 금지, CoroutineName, Dispatcher 주입, @Transactional과 suspend 분리). 코루틴 코드를 쓸 때 사용
paths: "**/*.kt, **/*.kts"
user-invocable: false
---

# 코루틴

근거: ${CLAUDE_SKILL_DIR}/../../docs/conventions/coroutines.md. Zed에는 Kotlin 디버거가 없어 코루틴을 스텝 실행할 수 없다. 그래서 디버깅이 필요한 상황 자체를 줄이고, 로그·덤프·테스트로 문제를 찾을 수 있게 쓴다.

## 어디에 쓰나

- `domain`에는 `suspend`와 `kotlinx.coroutines`를 쓰지 않는다. 핵심 규칙은 동기 코드로 쓰고 단위 테스트한다.
- 코루틴은 웹 진입(WebSocket, SSE)과 외부 호출 어댑터에서만 쓴다.
- `@Transactional`이 있는 클래스·파일에 `suspend fun`을 쓰지 않는다. JPA 트랜잭션은 ThreadLocal 기반이라 코루틴이 스레드를 바꾸면 깨진다. DB 호출은 호출하는 쪽에서 `withContext(ioDispatcher) { service.method() }`로 감싼다.

## 어떻게 쓰나

- `GlobalScope`를 쓰지 않는다. `config/CoroutineConfig`가 만든 `CoroutineScope`를 생성자로 주입받는다.
- 메인 코드에서 `runBlocking`을 쓰지 않는다. 테스트는 `runTest`를 쓴다.
- `Dispatchers.IO`/`Default`를 직접 쓰지 않는다. `config`에서 만든 `CoroutineDispatcher`를 주입받는다.
- `launch`/`async`에는 `CoroutineName`을 붙인다. 이름은 `<작업>-<식별자>` 형태로 쓴다. 로그 MDC가 필요하면 `MDCContext()`를 더한다.
  ```kotlin
  scope.launch(CoroutineName("stock-stream-$sku") + MDCContext()) { ... }
  ```
- suspend 호출을 `runCatching`으로 감싸지 않는다. `catch (e: Exception)`을 쓰면 `CancellationException`은 다시 던진다.
- `Thread.sleep` 대신 `delay`를 쓴다.
- suspend 함수가 `Flow`를 반환하지 않게 한다(`fun ...(): Flow<T>`).

## 디버깅 설정 (빌드에 유지)

- `bootRun`과 `test`에 `-Dkotlinx.coroutines.debug`를 켠다.
- `-Xdebug` 컴파일 옵션은 `-PcoroutineDebug`가 있을 때만 켠다. 운영 빌드에 넣지 않는다.
- `local` 프로필에서 `DebugProbes.install()`을 실행한다.

훅이 `domain/no-coroutines`, `coroutine/no-global-scope`, `coroutine/no-run-blocking`, `coroutine/name-required`, `coroutine/inject-dispatcher`, `coroutine/no-suspend-transactional` 위반을 차단한다.

# 값: 시각·소수·비밀

시각, 소수, 비밀값은 타입만 봐서는 실수가 드러나지 않는다. 컴파일도 되고 테스트도 대개 통과하지만, 운영 중에 틀린 값이 나오거나 비밀이 로그로 샌다. 아래 네 규칙은 도메인과 상관없이 적용한다.

| 규칙 | 부류 | 강제 |
|---|---|---|
| 현재 시각은 주입받은 `Clock`에서 읽는다. `Instant.now()`, `LocalDateTime.now(zone)` 금지 (테스트와 `config` 제외) | 범용 | 훅 (`time/inject-clock`) |
| `BigDecimal.divide`, `setScale`에는 반올림 방식(`RoundingMode` 또는 `MathContext`)을 넘긴다 | 범용 | 훅 (`bigdecimal/rounding-mode`) |
| `BigDecimal`을 `Double` 값으로 만들지 않는다. 문자열이나 `toBigDecimal()`을 쓴다 | 범용 | 훅 (`bigdecimal/no-double-ctor`) |
| 비밀번호·키·토큰을 로그에 남기지 않는다 | 범용 | 훅 (`log/no-secret`) |

## 시각: `Clock` 주입

```kotlin
// config
@Configuration
class ClockConfig {
    @Bean
    fun clock(): Clock = Clock.systemUTC()
}

// 사용
class OrderService(private val clock: Clock) {
    fun place() = Order(placedAt = Instant.now(clock))
}

// 테스트
val clock = Clock.fixed(Instant.parse("2026-10-12T00:30:00Z"), ZoneOffset.UTC)
```

- 시스템 시계를 바로 읽으면 "장 마감 5분 전", "만료 하루 전" 같은 시각 의존 로직을 테스트할 수 없다.
- `now(ZoneId.of("Asia/Seoul"))`도 시스템 시계를 읽는다. 시간대는 `LocalDateTime.now(clock.withZone(zone))`로 바꾼다.
- 검사는 `now()`의 인자가 비었거나 시간대(`Zone…`)일 때만 막는다. `now(clock)`, `now(c)`처럼 다른 인자는 통과한다.

## 소수: `BigDecimal`

```kotlin
BigDecimal(0.1)                    // 0.1000000000000000055511151231257827…  ✗
BigDecimal("0.1")                  // 0.1                                     ✓
"0.1".toBigDecimal()               // 0.1                                     ✓

BigDecimal(10).divide(BigDecimal(3))                       // ArithmeticException  ✗
BigDecimal(10).divide(BigDecimal(3), 0, RoundingMode.DOWN) // 3                    ✓
BigDecimal("1.005").setScale(2)                            // ArithmeticException  ✗
```

- 나누어떨어지지 않는 `divide(x)`와 반올림이 필요한 `setScale(n)`은 실행 중에 예외를 던진다. 어느 쪽으로 자를지(버림, 반올림)는 업무 규칙이므로 코드에 드러나게 쓴다.
- 금액 라이브러리(JSR 354 Moneta 등)를 써도 이 규칙은 필요하다. Moneta는 `BigDecimal(0.1)`로 만든 값을 그대로 받고, `divide`는 통화 자릿수로 자르지 않는다.

### 검사가 못 잡는 것

- Kotlin 연산자 `a / b`(`BigDecimal.div`)는 예외 없이 `a`의 자릿수와 `HALF_EVEN`으로 자른다. `BigDecimal("1") / BigDecimal("3")`은 `0`이다. 줄 단위 검사로는 타입을 알 수 없어서 잡지 못한다. 소수 나눗셈은 `divide(x, scale, mode)`로 쓴다.
- `BigDecimal(someDouble)`처럼 변수의 타입이 `Double`인 경우. 리터럴(`0.1`)과 `.toDouble()`·`.toFloat()`만 잡는다.
- 여러 줄에 걸친 `divide(` 인자. 첫 줄만 본다.

## 비밀: 로그

```kotlin
log.info("token issued: $accessToken")          // ✗
log.info("token issued for account {}", accountId) // ✓ 식별자만
```

- 로그 호출(`log`, `logger`의 `trace/debug/info/warn/error`) 줄에서 문자열 템플릿(`$x`, `${...}`)과 인자에 `appKey`, `appSecret`, `clientSecret`, `secretKey`, `apiKey`, `accessToken`, `refreshToken`, `password`, `passwd`, `secret`이 있으면 막는다.
- 문자열 리터럴 안의 단어("password reset mail sent")는 검사하지 않는다.
- 도메인 전용 비밀(계좌번호 등)은 이 범용 목록에 넣지 않는다. 프로젝트 `CLAUDE.md`나 리뷰로 다룬다.

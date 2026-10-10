# 설정값

Zed에는 `@Value("${...}")` ↔ `application.yml` 사이를 오가는 기능이 없다. 설정값을 타입이 있는 클래스 하나로 묶어서, 키 이름이 코드 한 곳에만 있게 한다.

| 컨벤션 | 부류 | 강제 |
|---|---|---|
| `@Value`를 쓰지 않는다. 설정은 `@ConfigurationProperties` 클래스로 묶는다 | 범용 | 훅 (`config/no-value`) |
| 설정 클래스는 `config` 패키지에 `*Properties`라는 이름으로 두고, 접두사는 `<앱>.<영역>`으로 한다 | 팀 | 리뷰 |
| 애플리케이션 클래스에 `@ConfigurationPropertiesScan`을 붙인다 | 범용 | 리뷰 |
| `application.yml`에 키를 추가하면 대응하는 `*Properties` 필드도 같이 추가한다 | 범용 | 리뷰 |
| 비밀값(비밀번호, API 키)은 `application.yml`에 쓰지 않고 환경 변수로 주입한다 | 범용 | 리뷰 |

```kotlin
@ConfigurationProperties("wms.allocation")
data class AllocationProperties(
    val maxQuantityPerPick: Int,
    val policy: String = "FIFO",
)
```

설정값을 쓰는 곳은 `AllocationProperties`의 사용처 찾기로 전부 나온다.

`application.yml` 자동완성이 필요하면 `spring-boot-configuration-processor`를 kapt 없이 쓸 수 없다는 점에 주의한다. Kotlin에서는 자동완성 메타데이터 생성에 kapt가 필요하고, Zed에서는 yml 자동완성을 해 줄 도구도 없으므로 이 컨벤션에서는 쓰지 않는다.

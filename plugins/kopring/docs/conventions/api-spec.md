# API 스펙 계약

서버(Spring)와 프론트(Next 등)는 저장소 루트의 `openapi/openapi.json` 하나로 API를 맞춘다. 서버가 PR마다 이 파일을 최신으로 커밋하고, 프론트는 이 파일에서 타입을 만든다(nextts `docs/conventions/api-client.md`).

## 흐름

| 순서 | 누가 | 하는 일 |
|---|---|---|
| 1 | 서버 PR | 컨트롤러·DTO를 바꾸고 `./gradlew test --tests '*OpenApiSpecTest'`로 스펙을 다시 만들어 같이 커밋 |
| 2 | CI(`api-spec-drift.yml`) | 스펙을 다시 만들어 커밋된 파일과 비교. 다르면 PR 실패 |
| 3 | 개발 브랜치에 머지 | 프론트의 Action이 타입을 다시 생성해 PR을 연다(nextts) |

## 스펙 만들기: 테스트 (`OpenApiSpecTest`)

`@SpringBootTest` + MockMvc로 `/v3/api-docs`를 받아 키를 정렬해 `openapi/openapi.json`에 쓴다.

- Gradle 플러그인(`org.springdoc.openapi-gradle-plugin`)은 쓰지 않는다. 마지막 릴리스 1.9.0이 2024-06이고 Spring Boot 4 지원이 확인되지 않았다. 앱을 따로 띄워야 한다.
- 키 정렬(`SerializationFeature.ORDER_MAP_ENTRIES_BY_KEYS`)은 중첩된 객체까지 정렬하고 배열 순서는 그대로 둔다(Jackson 3.2.3 실행 확인). 그래서 diff가 실제 변경만 보인다.
- 출력 경로는 Gradle이 시스템 속성으로 넘긴다:
  ```kotlin
  // build.gradle.kts
  tasks.test {
      systemProperty("openapi.output", rootProject.file("openapi/openapi.json").path)  // Gradle 루트가 하위 폴더면 "../openapi/openapi.json"
  }
  ```
- DB 등 통합 테스트 설정(Testcontainers 등)은 프로젝트의 것을 그대로 쓴다.
- `/v3/api-docs`가 보안 필터(서비스 키 등) 뒤에 있으면 테스트에서 헤더를 붙이거나 테스트 프로필에서 그 경로를 연다.

## 꼭 넣을 설정

```yaml
# application.yml
springdoc:
  default-produces-media-type: application/json   # 없으면 응답 미디어 타입이 */*로 나온다
```

- Kotlin non-null 필드는 springdoc 3.1.1이 스펙에 `required`로 표시하지 않는다. 대신 nullable 필드(`String?`)는 `"type": ["string", "null"]`로 정확히 표시한다(OpenAPI 3.1). 그래서 프론트가 `openapi-typescript --properties-required-by-default`로 생성하면 non-null은 `string`, nullable은 `string | null`이 된다(nextts `api-client.md`). Jackson은 null 필드도 키를 넣어 보내므로 응답과 맞는다.

## BigDecimal은 문자열 (`JacksonConfig`, `OpenApiConfig`)

JSON 숫자는 받는 쪽(JavaScript)에서 double이 되어 소수 정밀도를 잃는다. 금액·가격·비율·환율은 문자열로 보내고, 정수(수량·건수)는 숫자로 둔다.

- Jackson: `JsonMapperBuilderCustomizer`(`org.springframework.boot.jackson.autoconfigure`) 빈에서 `withConfigOverride(BigDecimal::class.java) { it.setFormat(JsonFormat.Value.forShape(STRING)) }`. 전역이라 DTO마다 달 필요가 없다. Jackson 3.2.3에서 `"price":"72350.50"`, `"quantity":10`, 문자열 → BigDecimal 읽기를 실행해 확인했다.
- springdoc: Jackson 설정을 스펙에 반영하지 않으므로 `SpringDocUtils.getConfig().replaceWithSchema(BigDecimal::class.java, StringSchema().format("decimal"))`로 따로 맞춘다. 스펙의 BigDecimal 필드는 `type: string, format: decimal`이 된다.
- Jackson 3의 패키지는 `tools.jackson`이지만 어노테이션(`@JsonFormat`)은 `com.fasterxml.jackson.annotation` 그대로다.

## 버전 (2026-10-14 확인)

| 대상 | 버전 | 출처 |
|---|---|---|
| springdoc-openapi | 3.1.1 (Spring Boot 4.1.0 기준 빌드) | Maven Central `springdoc-openapi-3.1.1.pom` |
| `AutoConfigureMockMvc` | `org.springframework.boot.webmvc.test.autoconfigure` (spring-boot-webmvc-test 4.1.1) | jar 확인 |
| `SpringDocUtils` | `org.springdoc.core.utils.SpringDocUtils.replaceWithSchema(Class, Schema)` | jar 확인 |
| GitHub Actions | checkout v7, setup-java v6, gradle/actions v6 | 각 저장소 최신 릴리스 |

템플릿: `${CLAUDE_PLUGIN_ROOT}/templates/api-spec/` (`/kopring:init`이 복사한다).

## 실제로 돌려 본 결과 (2026-10-15)

stock 저장소의 테스트 브랜치에 Spring Boot 4.1.1(Kotlin 2.4.21, JDK 17) 최소 앱과 이 템플릿을 그대로 넣어 GitHub Actions에서 돌렸다(브랜치는 확인 후 지움).

| 확인 | 결과 |
|---|---|
| `OpenApiSpecTest`가 스펙을 만드나 | 만든다. BigDecimal은 `"type": "string", "format": "decimal"`, Long은 `integer/int64`, nullable은 `["string","null"]` |
| 스펙과 코드가 같을 때 drift 검사 | 통과 |
| 스펙을 갱신하지 않고 응답 필드를 추가 | drift 검사 실패, 빠진 필드가 diff로 보이고 안내 문구가 나온다 |

---
name: api-spec
description: API 스펙 계약(openapi/openapi.json은 테스트가 만들고 서버 PR마다 갱신, BigDecimal은 JSON 문자열). REST 컨트롤러·요청/응답 DTO를 고칠 때 사용
paths: "**/*.kt"
user-invocable: false
---

# API 스펙

근거: ${CLAUDE_SKILL_DIR}/../../docs/conventions/api-spec.md. 저장소에 `openapi/openapi.json`이 있는 프로젝트에 적용한다.

- 컨트롤러·요청/응답 DTO를 바꾸면 `./gradlew test --tests '*OpenApiSpecTest'`로 `openapi/openapi.json`을 다시 만들어 같은 PR에 커밋한다. 스펙 파일은 손으로 고치지 않는다.
- 금액·가격·비율·환율은 DTO에서도 `BigDecimal`. JSON에서는 문자열로 나간다(`JacksonConfig`·`OpenApiConfig` 전역 설정). 정수(수량·건수)는 `Int`/`Long`.
- 프론트는 표시만 한다. 화면에 필요한 계산값(평가 금액, 원화 환산 등)은 서버가 응답에 넣는다.

훅이 `api/spec-generated`(스펙 파일 직접 수정)를 차단하고, CI(`api-spec-drift.yml`)가 스펙이 코드와 다르면 PR을 막는다.

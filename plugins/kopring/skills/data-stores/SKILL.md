---
name: data-stores
description: 다중 저장소(RDB + 시계열)와 읽기·쓰기 분리 규칙. 저장소를 추가하거나 Replica·CQRS를 다룰 때 사용
paths: "**/*.kt"
user-invocable: false
---

# 다중 저장소와 읽기·쓰기 분리

근거: ${CLAUDE_SKILL_DIR}/../../docs/architecture/multi-datastore.md, ${CLAUDE_SKILL_DIR}/../../docs/architecture/read-write-split.md

## 다중 저장소 (RDB + 시계열 DB 등)

- 저장소마다 out 포트를 **데이터 종류** 단위로 만들고(`LoadCandlesPort`, `SaveOrderPort`), 어댑터는 기술별 패키지(`adapter/out/persistence`, `adapter/out/timeseries`)에 둔다.
- `@Transactional`은 RDB만 묶는다. 한 유스케이스에서 두 저장소에 쓰지 않는 것을 기본으로 한다. 필요하면 RDB에 먼저 쓰고, 다른 저장소 쓰기는 커밋 후 이벤트로 넘기며 멱등하게 만든다.
- 분산 트랜잭션(XA)을 쓰지 않는다.
- 시간은 `Instant`(UTC)로 다룬다.
- JPA 데이터소스가 여러 개면 데이터소스마다 패키지와 `<이름>DataSourceConfig`를 둔다. 서비스에 트랜잭션 매니저 이름 문자열을 쓰지 말고 `@MarketTransactional` 같은 합성 애너테이션을 만든다.

## 읽기·쓰기 분리

- Replica 라우팅은 `config`에서만 처리하고 포트를 만들지 않는다. 라우팅 DataSource는 `LazyConnectionDataSourceProxy`로 감싼다.
- 읽기 전용 서비스는 `*QueryService`로 이름 짓고 클래스에 `@Transactional(readOnly = true)`를 붙인다. 쓰기 메서드만 `@Transactional`로 덮어쓴다.
- 방금 쓴 데이터를 바로 읽어야 하면 쓰기 트랜잭션 안에서 읽는다(복제 지연).
- CQRS는 사용자가 요청했을 때만 도입한다. 도입하면 `*CommandService`/`*QueryService`를 나누고, 읽기 포트는 조회 전용 DTO를 반환하며, 읽기 모델은 커밋 후 이벤트로 멱등하게 갱신한다.

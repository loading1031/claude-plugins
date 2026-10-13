---
name: event-driven
description: 내부 이벤트와 메시지 브로커 규칙(과거형 이벤트, 구체 타입 리스너, AFTER_COMMIT, Modulith 발행 기록·Outbox, 멱등 소비). 이벤트·Kafka를 다룰 때 사용
paths: "**/*.kt"
user-invocable: false
---

# 이벤트 드리븐

근거: ${CLAUDE_SKILL_DIR}/../../docs/architecture/event-driven.md. Zed에는 이벤트 발행 ↔ 리스너 이동 기능이 없으므로, **이벤트 클래스의 사용처 찾기로 흐름 전체가 보이게** 쓴다.

## 이벤트와 리스너

- 이벤트 하나당 클래스 하나, 이름은 과거형(`StockAllocated`). `domain/event`에 순수 data class로 두고 `ApplicationEvent`를 상속하지 않는다.
- 이벤트에는 `eventId`와 `occurredAt`을 넣는다.
- 범용 이벤트(`GenericEvent(type, payload)`)를 만들지 않는다.
- 리스너는 구체 이벤트 클래스 하나를 파라미터로 받는다. `Any`, `ApplicationEvent`, 상위 타입, `@EventListener(classes = [...])`를 쓰지 않는다.
- 리스너는 `adapter/in/messaging`(계층형: `api`)에 두고 변환과 서비스 호출만 한다.
- 부수 효과는 `@TransactionalEventListener(phase = AFTER_COMMIT)`로 처리한다. 그 안에서 DB에 쓰면 `REQUIRES_NEW`를 붙인다.
- 유실되면 안 되는 이벤트는 발행 기록을 남긴다: Spring Modulith 이벤트 발행 기록(`event_publication`) 또는 직접 만든 Outbox. 프로젝트 CLAUDE.md에 정한 것이 없으면 사용자에게 먼저 묻는다.
- Spring Modulith를 쓰면 모듈 사이 리스너는 `@ApplicationModuleListener`(= 커밋 후 + 비동기 + `REQUIRES_NEW`)로 쓰고, 같은 구체 타입 규칙을 지킨다.

## 메시지 브로커

- 토픽·큐 이름은 `Topics` 상수로만 쓴다.
- 발행은 out 포트(`PublishStockEventPort`) 뒤에 두고 `adapter/out/messaging`에서 `KafkaTemplate`으로 구현한다.
- 메시지 클래스는 `<이벤트>Message`로 이벤트와 1:1 대응시킨다.
- 소비자는 `eventId`로 중복 처리를 막아 멱등하게 만든다.
- 순서가 중요하면 같은 파티션 키를 쓴다. 재시도 횟수를 제한하고 실패는 DLQ로 보낸다.
- 스키마는 필드 추가만 한다. 그 외 변경은 새 버전 이벤트로 만든다.

## 추적

- `correlationId`를 요청 진입 시 만들어 이벤트·메시지 헤더·MDC로 넘긴다.
- 발행·수신 시 이벤트 이름, `eventId`, `correlationId`를 INFO 로그로 남긴다.

훅이 `event/listener-concrete-type`, `event/topic-constant`, `arch/tech-client-outside-adapter` 위반을 차단한다.

---
name: guide
description: kopring 컨벤션 전체 안내 — 규칙 부류(범용/팀/Zed), 강제 수단, 검사 rule id 색인, 케이스별 아키텍처 문서. 훅이 위반을 차단했을 때, 규칙의 근거를 찾을 때, 새 기술(캐시·시계열·외부 API·브로커)을 도입할 때 사용
---

# kopring 컨벤션 안내

Zed + Claude Code로 Kotlin + Spring Boot를 개발할 때의 컨벤션이다. Zed + Kotlin LSP에 없는 Spring 분석·디버거 기능의 공백을 컨벤션으로 메우고, 훅으로 강제한다.

## 어디를 보나

| 상황 | 문서 |
|---|---|
| 훅이 `[rule-id]`로 차단했다 | `${CLAUDE_SKILL_DIR}/../../docs/conventions/README.md`의 "검사 규칙 색인"에서 rule id → 근거 문서 |
| 규칙이 왜 있는지 | `${CLAUDE_SKILL_DIR}/../../docs/environment/zed.md` (Zed에서 안 되는 것) |
| 계층형 vs 헥사고날 선택 | `${CLAUDE_SKILL_DIR}/../../docs/architecture/choosing.md` |
| 캐시 / 다중 저장소 / 읽기·쓰기 분리 / 외부 API / 이벤트 | `${CLAUDE_SKILL_DIR}/../../docs/architecture/` 아래 `cache.md`, `multi-datastore.md`, `read-write-split.md`, `external-api.md`, `event-driven.md` |
| 주제별 컨벤션 | `${CLAUDE_SKILL_DIR}/../../docs/conventions/` 아래 `persistence.md`, `dependency-injection.md`, `configuration.md`, `web-api.md`, `testing.md`, `coroutines.md`, `kotlin-spring.md`, `values.md`(시각·소수·비밀) |

## 지킬 것

- 훅이 차단하면 규칙을 우회하지 말고 근거 문서의 방식으로 고친다.
- 훅은 **새로 생기는 위반만** 막는다. 기존 위반은 따로 정리한다.
- 프로젝트 `CLAUDE.md`의 "컨벤션" 절(아키텍처, 케이스, 명시적 예외)이 이 플러그인의 기본값보다 우선한다. 그 절이 없으면 `/kopring:init`을 안내한다.
- 규칙의 부류: **범용**(항상 유지), **팀**(팀이 다시 정할 수 있음), **Zed**(IntelliJ로 옮기면 풀어도 됨), **프로젝트**(CLAUDE.md "컨벤션"의 "쓰지 않는 기술"·"클라이언트 위치"에서 읽음).

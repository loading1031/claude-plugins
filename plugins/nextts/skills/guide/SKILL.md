---
name: guide
description: nextts 컨벤션 전체 안내 — 규칙 부류(범용/팀/프로젝트), 강제 수단, 검사 rule id 색인. 훅이 위반을 차단했을 때, 규칙의 근거를 찾을 때, 프로젝트 선언을 바꿀 때 사용
---

# nextts 컨벤션 안내

Next.js(16+, App Router) + TypeScript 컨벤션이다. Tailwind·UI 규칙을 포함한다. 특정 앱 설계(차트, 실시간, 백엔드 종류)는 다루지 않고 각 프로젝트의 CLAUDE.md에 둔다. 디자인 문서 작업 방식은 `design` 플러그인.

## 어디를 보나

| 상황 | 문서 |
|---|---|
| 훅이 `[rule-id]`로 차단했다 | `${CLAUDE_SKILL_DIR}/../../docs/conventions/README.md`의 "검사 규칙 색인"에서 rule id → 근거 문서 |
| 무엇을 규칙으로 두고 무엇을 뺐나 | 같은 문서 "무엇을 규칙으로 두나" |
| 주제별 근거 | `${CLAUDE_SKILL_DIR}/../../docs/conventions/` 아래 `components.md`, `typescript.md`, `backend-and-secrets.md`, `tailwind-and-ui.md` |

## 지킬 것

- 훅이 차단하면 규칙을 우회하지 말고 근거 문서의 방식으로 고친다. `NEXT_PUBLIC_`을 붙이거나 `"use client"`를 넓히는 것으로 고치지 않는다.
- 훅은 **새로 생기는 위반만** 막는다. 기존 위반은 따로 정리한다.
- 프로젝트 `CLAUDE.md`의 "프론트엔드 컨벤션" 절이 이 플러그인의 기본값보다 우선한다. 그 절이 없으면 `/nextts:init`을 안내한다.
- 규칙의 부류: **범용**(항상 적용), **팀**(React Compiler·`tailwindcss`·`components.json`이 있을 때만, 또는 선언으로 끔), **프로젝트**(CLAUDE.md "프론트엔드 컨벤션"의 "백엔드 호출"·"쓰지 않는 라이브러리"에서 읽음).

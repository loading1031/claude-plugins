---
name: ui
description: 화면 규칙(UI 컴포넌트 재사용, 로딩·빈·오류 상태, 접근성, 모바일 우선). 화면·컴포넌트(.tsx)를 만들 때 사용
paths: "**/*.tsx"
user-invocable: false
---

# 화면

근거: ${CLAUDE_SKILL_DIR}/../../docs/conventions/tailwind-and-ui.md

- `components.json`이 있으면 그 `aliases.ui` 폴더(기본 `components/ui`)의 컴포넌트를 먼저 쓴다. `<button>`·`<input>`을 직접 만들지 않고, 없으면 shadcn으로 추가한다. 클래스 합치기는 `cn()`.
- 데이터를 보여 주는 화면은 로딩(`loading.tsx` 또는 `<Suspense>`), 빈 목록, 오류(`error.tsx`) 상태를 함께 만든다.
- 클릭은 `<button>`/`<Link>`. 아이콘만 있는 버튼에는 `aria-label`. 이미지는 `next/image`와 `alt`.
- 모바일 우선: 접두어 없는 클래스가 모바일, `md:` 이상으로 넓힌다.

훅이 `ui/use-ui-component`, `a11y/no-click-on-div`, `a11y/image` 위반을 차단한다.

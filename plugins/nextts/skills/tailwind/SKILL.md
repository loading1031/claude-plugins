---
name: tailwind
description: Tailwind v4 규칙(설정은 @theme, 클래스 이름 조립 금지, 색은 토큰, 다크 모드는 토큰으로). Tailwind 프로젝트에서 className·CSS를 쓸 때 사용
paths: "**/*.tsx, **/*.css"
user-invocable: false
---

# Tailwind

근거: ${CLAUDE_SKILL_DIR}/../../docs/conventions/tailwind-and-ui.md. `package.json`에 `tailwindcss`가 있는 프로젝트에만 적용한다.

- v4 방식: 설정은 `globals.css`의 `@import "tailwindcss"`와 `@theme`. `tailwind.config.*`를 만들지 않는다.
- 클래스 이름을 조립하지 않는다(`` `bg-${color}-500` ``, `"text-" + size`). 완전한 클래스 이름을 객체로 고른다: `{ blue: "bg-blue-600" }[color]`.
- 색은 토큰(`bg-primary`, `text-muted-foreground`). 색 임의값(`text-[#f00]`)과 `style`의 색 금지. 필요한 색이 없으면 `@theme`에 토큰부터 추가한다. 크기·간격 임의값은 허용.
- 다크 모드는 모드에 따라 값이 바뀌는 토큰으로. `dark:bg-zinc-900`처럼 `dark:` 뒤에 팔레트 색을 쓰지 않는다.

훅이 `tailwind/no-config-file`, `tailwind/no-dynamic-class`, `tailwind/no-arbitrary-color`, `tailwind/dark-via-token` 위반을 차단한다.

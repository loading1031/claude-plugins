---
name: components
description: Next.js 컴포넌트 규칙("use client"는 말단에만, server-only, React Compiler 프로젝트의 메모이제이션 금지, 선언 시 백엔드는 서버에서만). .ts/.tsx 코드를 쓸 때 사용
paths: "**/*.tsx, **/*.ts, **/*.mts"
user-invocable: false
---

# 컴포넌트

근거: ${CLAUDE_SKILL_DIR}/../../docs/conventions/components.md

- `"use client"`는 상태·효과·이벤트·브라우저 API가 필요한 가장 작은 컴포넌트에만 붙인다. 페이지·레이아웃에 붙이지 않는다. 그 부분만 파일로 빼고, 데이터는 서버 컴포넌트에서 가져와 props로 넘긴다. 서버 UI는 `children`으로 받는다.
- 비밀값·DB·백엔드를 다루는 모듈은 맨 위에 `import "server-only"`.
- `next.config.*`에 `reactCompiler`가 켜져 있으면 `useMemo`·`useCallback`·`memo`를 쓰지 않는다. 컴파일러가 잘못 최적화할 때만 `"use no memo"`와 이유 주석.
- 프로젝트 CLAUDE.md "프론트엔드 컨벤션"이 "백엔드 호출: 서버만"이면 백엔드는 서버 컴포넌트·라우트 핸들러·서버 액션에서만 부른다.
- JavaScript 파일을 만들지 않는다. 설정 파일도 `.ts`.

훅이 `memo/no-manual-memo`, `secret/no-public-secret`, `project/backend-server-only`, `project/forbidden-lib`, `ts/no-js-file` 위반을 차단한다.

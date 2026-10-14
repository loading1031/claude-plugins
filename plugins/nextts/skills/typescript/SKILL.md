---
name: typescript
description: TypeScript 전용 프로젝트 설정 규칙(JS·설정 파일을 .ts로, allowJs false, Turbopack, tsc --noEmit). package.json·tsconfig·설정 파일을 고칠 때 사용
paths: "**/package.json, **/tsconfig*.json, **/*.config.*, **/.env*"
user-invocable: false
---

# TypeScript와 도구

근거: ${CLAUDE_SKILL_DIR}/../../docs/conventions/typescript.md

- JavaScript 파일(`.js`·`.jsx`·`.mjs`·`.cjs`)을 만들지 않는다(`public/` 제외). 설정은 `next.config.ts`, `postcss.config.ts`, `eslint.config.ts`(개발 의존성 `jiti` 2.2+).
- `tsconfig.json`은 `"allowJs": false`.
- `next dev`·`next build`에 `--webpack`을 붙이지 않는다(Turbopack 기본). 프로젝트가 "번들러: webpack 허용"을 선언했으면 예외.
- `next dev`는 타입 검사를 안 한다. 코드를 고친 뒤 `tsc --noEmit`으로 확인한다.

훅이 `ts/no-js-file`, `ts/no-allow-js`, `bundler/no-webpack` 위반을 차단한다.

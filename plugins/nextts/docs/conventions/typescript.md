# TypeScript와 도구

## JavaScript 파일을 쓰지 않는다 (범용, `ts/no-js-file`, `ts/no-allow-js`)

소스와 설정 파일 모두 TypeScript로 쓴다. create-next-app의 TypeScript 템플릿도 `postcss.config.mjs`, `eslint.config.mjs`는 JS로 만들므로 처음에 옮긴다.

| 파일 | TypeScript로 | 조건 |
|---|---|---|
| Next 설정 | `next.config.ts` | Next 15부터. ESM 문법(top-level `await`)이 필요하면 `next.config.mts` |
| PostCSS | `postcss.config.ts` | Turbopack에서만 읽는다(webpack 미지원). 이 플러그인은 webpack을 쓰지 않으므로 문제없다 |
| ESLint | `eslint.config.ts` | 개발 의존성 `jiti` 2.2.0 이상. Node 22.13+에서 jiti 없이 쓰려면 `--experimental-strip-types`와 ESLint `unstable_native_nodejs_ts_config` 플래그가 필요해 jiti를 권한다 |
| `tsconfig.json` | `"allowJs": false` | Next는 `allowJs`가 없을 때만 `true`를 넣는다(추천값). `false`로 두면 그대로 둔다 |

- `public/`은 빌드하지 않고 그대로 내보내는 정적 파일이라 검사하지 않는다.
- 훅은 새 JS 파일만 막는다. 이미 있는 JS 파일을 고치는 것은 막지 않지만 pre-commit은 커밋되는 JS 파일을 막는다. `/nextts:init`이 기존 JS 파일을 옮길지 묻는다.

출처: [Next.js TypeScript](https://nextjs.org/docs/app/api-reference/config/typescript), Next 저장소 `test/e2e/postcss-config-ts`(Turbopack 전용), `packages/next/src/lib/typescript/writeConfigurationDefaults.ts`(`allowJs: { suggested: true }`), [ESLint 설정 파일](https://eslint.org/docs/latest/use/configure/configuration-files) "TypeScript Configuration Files"

## Turbopack, 타입 검사는 따로 (팀, `bundler/no-webpack`)

- Next 16부터 `next dev`, `next build`의 기본 번들러는 Turbopack이다. `--webpack`을 붙이지 않는다. webpack 전용 플러그인이 꼭 필요하면 CLAUDE.md "프론트엔드 컨벤션"에 "번들러: webpack 허용"을 선언한다.
- Turbopack은 타입 검사를 하지 않아 `next dev`에서는 타입 오류가 드러나지 않는다. `next build`는 프로젝트의 `tsc`로 검사하지만 커밋 뒤에야 알게 된다. 그래서 pre-commit에서 `tsc --noEmit`을 돌린다(`check_next_conventions.py --typecheck`). 명령은 lockfile로 고른다: `pnpm exec`, `yarn`, `bun x`, `npx --no-install`.

출처: [Next.js Turbopack](https://nextjs.org/docs/app/api-reference/turbopack), [Next.js TypeScript](https://nextjs.org/docs/app/api-reference/config/typescript) "Disabling TypeScript errors in production"

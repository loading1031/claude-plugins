# 컴포넌트

## `"use client"`는 말단에만 (범용, 스킬)

`"use client"`를 붙인 파일은 그 파일이 가져오는 모듈과 직접 그리는 컴포넌트까지 모두 클라이언트 번들에 들어간다. 페이지나 레이아웃에 붙이면 그 아래 전체가 클라이언트 컴포넌트가 되어 서버에서 데이터를 가져오는 이점이 사라진다.

- 상태·효과·이벤트 핸들러·브라우저 API가 필요한 가장 작은 컴포넌트만 따로 파일로 빼서 `"use client"`를 붙인다.
- 페이지·레이아웃은 서버 컴포넌트로 두고, 서버에서 가져온 데이터를 props로 넘긴다.
- 클라이언트 컴포넌트 안에 서버 UI가 필요하면 `children`으로 받는다(서버 컴포넌트는 서버에서 그려진 결과로 들어온다).
- context provider도 `children`만 감싸는 클라이언트 컴포넌트로 만들고 트리에서 가능한 한 깊게 둔다.

Claude가 자주 어기는 규칙이다. 훅 위반 하나를 고치려다 페이지 전체에 `"use client"`를 붙이는 식이다. 정규식으로는 "말단인지"를 판단할 수 없어 스킬로만 둔다.

출처: [Next.js Server and Client Components](https://nextjs.org/docs/app/getting-started/server-and-client-components) "Reducing JS bundle size", "Interleaving Server and Client Components"

## `server-only` (범용, 스킬)

비밀값·DB·백엔드 호출을 다루는 모듈은 맨 위에 `import "server-only"`를 둔다. 클라이언트 컴포넌트가 이 모듈을 가져오면 빌드 오류가 난다.

- 접두어 없는 환경변수는 클라이언트 번들에서 빈 문자열이 되므로, 실수로 가져와도 조용히 동작이 깨질 뿐 오류가 나지 않는다. `server-only`가 그것을 빌드 오류로 바꾼다.
- Next에서는 패키지를 설치하지 않아도 된다(Next가 내부에서 처리하고 타입도 제공). ESLint가 선언 안 된 의존성을 막으면 설치한다.
- 반대로 `window` 등을 쓰는 모듈에는 `import "client-only"`.

출처: 같은 문서 "Preventing environment poisoning"

## 메모이제이션은 React Compiler에 (팀, 스킬 + `memo/no-manual-memo`)

`next.config.ts`에 `reactCompiler: true`(Next 16에서 정식, 개발 의존성 `babel-plugin-react-compiler`)가 켜져 있으면 `useMemo`, `useCallback`, `React.memo`를 쓰지 않는다.

- 컴파일러가 컴포넌트와 훅을 자동으로 메모이제이션한다. 손으로 쓴 메모이제이션은 의존성 배열 실수가 잦고 컴파일러와 겹친다.
- 다시 렌더링되는 것은 클라이언트 컴포넌트뿐이라 효과는 클라이언트 컴포넌트에서 난다.
- 컴파일러가 잘못 최적화하는 컴포넌트에만 함수 맨 위에 `"use no memo"`를 두고, 이유를 주석으로 남긴다.
- 컴파일러를 켜지 않은 프로젝트에서는 이 규칙과 검사가 꺼진다. 검사기는 `next.config.*`에서 `reactCompiler: true` 또는 `reactCompiler: { … }`를 찾는다.

출처: [Next.js reactCompiler](https://nextjs.org/docs/app/api-reference/config/next-config-js/reactCompiler), create-next-app `--react-compiler` 옵션

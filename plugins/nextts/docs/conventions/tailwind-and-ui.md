# Tailwind와 화면

Tailwind 규칙은 Next 루트의 `package.json`에 `tailwindcss`가 있을 때만 켜진다. 설정 파일 규칙은 주 버전이 4 이상일 때만 켜진다. UI 컴포넌트 재사용은 `components.json`(shadcn)이 있을 때만 켜진다. 접근성 규칙은 항상 켜진다.

## v4 설정 방식 (팀, `tailwind/no-config-file`)

Tailwind v4는 설정을 CSS에 둔다: `@import "tailwindcss";`와 `@theme { --color-primary: … }`. `tailwind.config.*`와 `@tailwind base;` 같은 지시어는 v3 방식이다. Claude가 v3 방식으로 쓰는 일이 잦아 막는다.

shadcn의 `components.json`도 v4에서는 `tailwind.config`를 비워 둔다.

출처: [Tailwind CSS](https://tailwindcss.com/docs) v4.3, [shadcn components.json](https://ui.shadcn.com/docs/components-json) "For Tailwind CSS v4, leave this blank"

## 클래스 이름을 조립하지 않는다 (팀, `tailwind/no-dynamic-class`)

Tailwind는 소스를 글자로만 읽어 쓰인 클래스를 찾는다. `` `bg-${color}-500` ``이나 `"text-" + size`로 만든 클래스는 소스에 없어서 CSS가 만들어지지 않는다. 오류 없이 스타일만 빠지는 버그다.

완전한 클래스 이름을 객체나 조건으로 고른다:

```tsx
const variants = { blue: "bg-blue-600 hover:bg-blue-500", red: "bg-red-600 hover:bg-red-500" }
<button className={variants[color]} />
```

검사는 Tailwind 접두어 바로 뒤에 `${`가 붙거나(`bg-${`) `"bg-" +`처럼 접두어로 끝나는 문자열을 이어 붙일 때만 막는다. `${variants[color]}`처럼 완전한 이름을 끼우는 것은 통과한다.

출처: [Detecting classes in source files](https://tailwindcss.com/docs/detecting-classes-in-source-files) "Dynamic class names"

## 색은 토큰으로 (팀, `tailwind/no-arbitrary-color`)

색은 `globals.css`의 `@theme`(shadcn이면 `--primary`, `--muted-foreground` 같은 CSS 변수)에 둔 토큰으로 쓴다. 화면마다 색을 따로 적으면 디자인을 바꿀 때 다 찾아 고쳐야 하고, 다크 모드에서 어긋난다.

- 막는 것: 색 임의값(`text-[#ff0000]`, `bg-[rgb(…)]`, `border-[oklch(…)]`), `style={{ color: "#fff" }}`처럼 style에 색 리터럴
- 허용: `bg-[var(--brand)]`(토큰 참조), 크기·간격·레이아웃 임의값(`w-[137px]`, `grid-cols-[1fr_2fr]`), 투명도(`bg-black/[.06]`)
- 필요한 색이 토큰에 없으면 `@theme`에 토큰을 먼저 추가한다
- Canvas 차트 라이브러리처럼 색 문자열을 직접 받는 설정 객체는 검사하지 않는다(style 속성만 본다)

## 다크 모드는 토큰으로 (팀, `tailwind/dark-via-token`)

색 토큰을 `:root`와 다크 모드에서 다른 값으로 정의하면 `bg-background` 하나로 두 모드가 처리된다. `bg-white dark:bg-zinc-900`처럼 클래스마다 다크 색을 붙이면 토큰을 우회한다.

- 막는 것: `dark:` 뒤의 팔레트 색(`dark:bg-zinc-900`, `dark:hover:text-white/80`)
- 허용: `dark:bg-background`(토큰), `dark:invert` 같은 색이 아닌 유틸리티
- 다크 모드 기본은 `prefers-color-scheme`. 토글이 필요하면 `@custom-variant dark (&:where(.dark, .dark *));`

출처: [Tailwind Dark mode](https://tailwindcss.com/docs/dark-mode)

## UI 컴포넌트 재사용 (팀, `ui/use-ui-component`)

`components.json`이 있으면 `aliases.ui` 폴더(없으면 `components/ui`)의 컴포넌트를 먼저 쓴다. 그 폴더 밖에서 `<button>`, `<input>`, `<select>`, `<textarea>`를 직접 쓰면 막는다. 같은 버튼이 화면마다 다른 모양이 되는 것을 막는다. 필요한 컴포넌트가 없으면 shadcn으로 추가한다(`pnpm dlx shadcn@latest add button`). 클래스 합치기는 `cn()`(`aliases.utils`).

## 화면 상태 (팀, 스킬)

데이터를 보여 주는 화면은 세 상태를 같이 만든다: 로딩(`loading.tsx` 또는 `<Suspense fallback>`), 빈 목록, 오류(`error.tsx`). 정규식으로 판단할 수 없어 스킬로만 둔다.

## 접근성 (범용, `a11y/no-click-on-div`, `a11y/image`)

- 클릭은 `<button>`이나 `<Link>`. `<div onClick>`, `<span onClick>`은 키보드와 스크린 리더로 쓸 수 없다. `role`을 준 경우는 통과한다(직접 키보드 처리를 했다고 본다)
- 이미지는 `next/image`의 `<Image>`와 `alt`. 꾸밈용이면 `alt=""`
- 아이콘만 있는 버튼에는 `aria-label`(스킬만)

## 모바일 우선 (팀, 스킬)

접두어 없는 클래스가 모바일이고 `md:`, `lg:`로 넓힌다. 데스크톱 클래스를 먼저 쓰고 `max-md:`로 줄이지 않는다.

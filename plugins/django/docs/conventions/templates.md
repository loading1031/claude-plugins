# Django 템플릿 프런트엔드

## 페이지와 컴포넌트

- Django Template Language의 extends/block/include와 namespaced URL을 사용한다. 페이지 골격은 base template에, 반복되는 UI는 재사용 include에 둔다.
- 표준 HTML 링크와 form 제출을 기본으로 한다. 부분 갱신의 필요가 있고 프로젝트가 쓰는 경우에만 [HTMX](htmx.md)를 적용한다.
- React·Next.js·shadcn·SPA·클라이언트 라우터를 기본 의존성에 넣지 않는다. 브라우저 동작은 필요한 만큼의 JavaScript로 보완한다.
- include에 필요한 값을 with로 전달하고 공유 컨텍스트 의존을 줄인다. 사용법 주석이 필요하면 한 줄 `{# ... #}`로 작성하고, 주석 안에 실제 템플릿 태그를 넣지 않는다. 긴 주석은 comment/endcomment 블록을 쓴다.
- 기존 템플릿 폴더·이름 규칙을 따른다. components/·partials/·pages/는 새 프로젝트의 선택 가능한 정리 방식이며 필수 디렉터리 구조가 아니다.

## 폼·안전한 출력

- Django Form의 bound 값·필드 오류·non-field 오류를 표시한다. 서버 검증 결과를 브라우저 JavaScript에서 별도로 추정하지 않는다.
- 내부 POST form에는 csrf_token을 넣는다. GET은 조회용으로 유지하며 CSRF 검사를 부분 갱신 때문에 해제하지 않는다.
- autoescape를 기본으로 유지한다. 사용자 HTML을 safe 처리해야 한다면 저장/출력 경계에서 허용 태그·속성·URL을 검증하는 별도 정책이 있어야 한다.
- 이미지 업로드는 확장자만 믿지 말고 크기·유형·접근 권한을 검증한다. 업로드 URL과 정적 자산 URL을 구분한다.

## 접근성과 상태

- 클릭 동작은 button, 이동은 a를 사용한다. 폼 필드에는 연결된 label을 두고 오류는 aria-describedby/aria-invalid 등으로 연결한다.
- 기본·빈 목록·검증 실패·권한 없음·로딩 상태를 작업 범위에 맞게 확인한다. 색상만으로 오류나 선택을 표시하지 않는다.
- 모달의 열기/닫기·초점·키보드 동작을 확인한다. HTML dialog를 쓰면 showModal/close와 접근 가능한 이름을 사용한다.
- UI 스타일은 [Tailwind + DaisyUI](tailwind-daisyui.md)를 따른다. 토큰·컴포넌트의 실제 값은 코드가 기준이다.

## 디자인·컴포넌트 전시

- design 플러그인이 설치되고 프로젝트 디자인 기준이 있으면 화면 구현 전에 해당 기준을 읽는다. 제공 도구로 읽을 수 없는 아티팩트를 읽었다고 표시하거나 그림 버전을 만들어 기록하지 않는다.
- design은 화면 기준과 문서 연결, 이 플러그인은 Django 구현·UI 코드 규칙을 담당한다. 디자인 문서 도구 자체는 여기서 구현하지 않는다.
- 이미 pattern library가 있다면 실제 컴포넌트를 include해 상태를 전시한다. 없는 프로젝트에 django-pattern-library를 필수로 설치하지 않는다.

출처: [Django templates](https://docs.djangoproject.com/en/6.0/topics/templates/), [CSRF](https://docs.djangoproject.com/en/6.0/howto/csrf/).

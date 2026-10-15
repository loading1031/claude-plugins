# Tailwind CSS 4 + DaisyUI 5

## 기본 선택

Django가 HTML을 만들고 빌드된 CSS를 static으로 제공한다. 기본 UI는 DaisyUI 컴포넌트, 레이아웃·간격·세부 크기는 Tailwind 유틸리티로 구성한다. 기존 v3/v4 프로젝트를 자동 업그레이드하지 않고 설치 버전과 빌드 방식을 먼저 확인한다.

- 버튼·폼·카드·모달은 btn/input/card/modal 등 기존 DaisyUI 컴포넌트를 우선 쓴다. 동일한 이름의 .btn/.card를 자체 CSS로 재정의하지 않는다.
- 색상은 primary/base-100/base-content/error 같은 의미 토큰을 사용한다. 제품 고유 팔레트는 테마·CSS 변수에서 정의하고 화면마다 임의 값을 복제하지 않는다.
- Tailwind 클래스는 소스에 완전한 문자열로 둔다. `bg-{{ color }}-500`처럼 조합하지 말고 허용된 전체 클래스 문자열로 매핑한다.
- 템플릿·부분 템플릿·위젯 클래스가 들어 있는 Python/JS 파일까지 실제 소스 경로를 빌드 검색 범위에 포함한다.

## v4/v5 최소 CSS 예시

아래 상대 경로는 CSS 파일 위치를 기준으로 조정한다. 기본 테마는 프로젝트 설정을 따른다.

```css
@import "tailwindcss";
@plugin "daisyui" {
  themes: light --default, dark --prefersdark;
}
@source "../../templates";
@source "../../apps";
```

DaisyUI 5 CSS 설정에 이전 버전의 JS 테마 객체나 darkTheme 옵션을 복사하지 않는다. 새로운 custom theme은 설치된 DaisyUI 버전의 테마 문법을 확인한다. 선택되지 않은 테마나 런타임 다크 모드를 임의로 추가하지 않는다.

## Django 연결·빌드

- `{% load static %}`와 static 태그로 빌드 CSS를 연결한다. 입력 CSS와 출력 CSS를 구분한다.
- 새 프로젝트는 프로젝트의 패키지 매니저로 tailwindcss/@tailwindcss/cli/daisyui를 관리할 수 있다. 기존 standalone CLI가 있으면 버전·DaisyUI 지원 방식을 확인하고 유지한다. standalone 바이너리만 있으면 모든 npm 플러그인이 자동 제공된다고 가정하지 않는다.
- 버전은 lockfile/고정된 도구에서 재현한다. CSS 빌드는 배포 과정에서 실행하고 collectstatic 대상에 출력 CSS를 포함한다. CDN 런타임 CSS를 운영 기본값으로 사용하지 않는다.
- Django Forms widget의 class도 완전한 문자열로 지정한다. 입력 유형에 맞춰 input/select/textarea/checkbox 등을 적용한다.

```python
name = forms.CharField(widget=forms.TextInput(attrs={"class": "input w-full"}))
```

이 예시는 `from django import forms`를 사용하는 Form 필드다. 공통 위젯 규칙이 이미 있으면 재사용한다. v4의 input-bordered/card-compact 같은 예제를 v5 필수 규칙으로 남기지 않는다.

출처: [DaisyUI 설치](https://daisyui.com/docs/install/), [DaisyUI 설정](https://daisyui.com/docs/config/), [Tailwind 클래스 탐색](https://tailwindcss.com/docs/detecting-classes-in-source-files).

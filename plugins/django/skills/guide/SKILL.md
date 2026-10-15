---
name: guide
description: "기본 Django 서버와 Django 템플릿 프런트엔드 규칙을 안내한다. Django 프로젝트 작업·컨벤션 확인 시 사용하며 UI 기본은 Tailwind CSS 4 + DaisyUI 5다."
---

# Django 프로젝트 작업

프로젝트의 AGENTS.md/CLAUDE.md 중 사용 환경의 진입점과 Django 설정을 먼저 읽는다. Django 버전, manage.py, settings, 템플릿·정적 자산, lockfile을 확인한다.

기본은 Django 서버 + Django Template Language + Tailwind CSS 4 + DaisyUI 5다. 일반 view/form/ORM을 사용하며 React·별도 API 프런트·일괄 async 전환을 추가하지 않는다. 제품 도메인 규칙과 디자인·기획·Git 정책은 프로젝트와 각 플러그인이 담당한다.

필요한 문서만 읽는다. 경로는 이 SKILL.md 기준이다.

| 작업 | 규칙 |
|---|---|
| 모델·뷰·폼·인증·DB·선택적 async | [서버](../../docs/conventions/server.md) |
| HTML·폼·컴포넌트 | [템플릿](../../docs/conventions/templates.md) |
| CSS·DaisyUI·테마·빌드 | [Tailwind + DaisyUI](../../docs/conventions/tailwind-daisyui.md) |
| 부분 갱신을 쓰는 경우 | [HTMX](../../docs/conventions/htmx.md) |
| 테스트·검증 | [검증](../../docs/conventions/testing.md) |

이 플러그인은 지침 패키지다. 설치만으로 Django/CSS 의존성이나 훅이 설치되거나 제품 코드가 바뀌지 않는다. 기존 Django 프로젝트가 없으면 생성 요청의 범위를 확인하고, 규칙 연결 요청을 앱 생성으로 확대하지 않는다.

---
name: templates
description: "Django HTML 템플릿·Form UI·재사용 컴포넌트·CSS를 만들거나 고칠 때 사용한다. Django 템플릿과 Tailwind CSS 4 + DaisyUI 5가 기본이다."
---

# Django 화면 작업

프로젝트 디자인 기준과 템플릿·빌드·설치 버전을 확인한다. [템플릿 규칙](../../docs/conventions/templates.md)과 [Tailwind + DaisyUI](../../docs/conventions/tailwind-daisyui.md)를 따른다.

화면은 Django 템플릿, UI는 DaisyUI 컴포넌트와 Tailwind 유틸리티로 구현한다. 기존 include와 Form 위젯을 재사용한다. 디자인 플러그인이 있으면 선언된 화면 기준을 읽되 없는 문서 도구를 요구하거나 버전 정보를 만들어 쓰지 않는다. 관련 검증은 [테스트 규칙](../../docs/conventions/testing.md)을 따른다.

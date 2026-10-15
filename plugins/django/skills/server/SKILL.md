---
name: server
description: "Django 모델·뷰·폼·인증·ORM·마이그레이션을 작성하거나 검토할 때 사용한다. 일반 Django 서버가 기본이며 async는 필요한 경우에만 적용한다."
---

# Django 서버 작업

프로젝트 지침과 설치 버전·기존 앱 패턴을 확인한 뒤 [서버 규칙](../../docs/conventions/server.md)을 따른다. 검증에는 [테스트 규칙](../../docs/conventions/testing.md)을 사용한다.

일반 요청은 sync view와 Django Form/ORM을 기본으로 한다. 기존 async·ASGI 동작은 보존하고 스트리밍 등 해당 기능을 고칠 때 async 절을 읽는다. API 프레임워크·서비스 계층·DB 교체를 규칙 적용에 포함하지 않는다.

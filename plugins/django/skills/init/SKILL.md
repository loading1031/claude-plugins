---
name: init
description: "Django 프로젝트에 이 플러그인의 서버·템플릿·Tailwind·DaisyUI 컨벤션 설정을 연결한다. 기존 제품 코드·의존성·Git 훅을 자동 변경하지 않는다."
---

# /django:init — 프로젝트 연결

1. 프로젝트 지침과 manage.py·settings·lockfile·템플릿·CSS 빌드를 읽는다. 이미 정해진 경로·버전·도구를 다시 묻지 않는다. Django 프로젝트가 없으면 그 사실을 보고하고 새 프로젝트 생성까지 요청됐는지 구분한다.
2. 공통 프로젝트 지침에 `## Django 컨벤션` 절을 추가하거나 기존 값만 갱신한다. 별도 공통 지침이 없으면 사용 중인 AGENTS.md/CLAUDE.md를 사용한다. 양쪽을 쓰면 같은 공통 설정 파일을 참조하게 하고 절차를 복제하지 않는다.

```markdown
## Django 컨벤션
- 플러그인: django (loading1031-plugins)
- 서버: Django view + Form/ModelForm + ORM
- 프런트엔드: Django Template Language
- UI: Tailwind CSS 4 + DaisyUI 5
- HTMX: 미사용 또는 기존 사용 범위
- async: 필요한 I/O·스트리밍에서만 사용, 기존 동작 보존
- 프로젝트 경로·버전·명령: 실제 프로젝트에서 확인한 값
```

3. 새 기본 선택과 기존 설치 버전이 다르면 차이를 기록한다. 설정 연결만 요청됐다면 업그레이드하지 않는다. `.claude/rules` 등의 공통 규칙은 플러그인 도입 후 짧은 참조로 줄일 수 있지만 제품 고유 규칙을 삭제하지 않는다. 설치 전 원본 문서를 지워 프로젝트 지침을 잃게 하지 않는다.
4. 실제 설치 여부·선택된 프로젝트 설정·남은 차이를 보고한다. manifest 존재와 플랫폼에서 활성화된 상태를 구분한다. 이 명령은 의존성 설치·migration·훅 설치·commit/push 권한을 추가하지 않는다.

기본 동작은 [guide](../guide/SKILL.md)에 있다. design과 planning은 별도 플러그인이며 이 init에서 원격 아티팩트를 만들거나 이슈·브랜치를 자동 생성하지 않는다.

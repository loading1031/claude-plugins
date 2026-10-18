# 플러그인 기준 연결

리뷰 기준의 단일 원본은 각 플러그인의 스킬·참조 문서다. 이 디렉터리에 규칙 전문을 복사하지 말고, 아래 연결과 코드 변경의 맥락을 사용해 현재 원본을 읽는다. 저장소 외부 프로젝트에서는 설치된 플러그인의 프로젝트별 초기화 결과와 로컬 지침도 함께 확인한다.

| 영역 | 원본 경로 | 리뷰 시 읽을 기준 |
|---|---|---|
| Design | `plugins/design/skills/design/SKILL.md`, `plugins/design/docs/design-doc.md` | 승인 기준, 와이어프레임, 토큰·컴포넌트 원본, 카탈로그와 실제 화면의 관계, PR 인라인 리뷰 원칙 |
| Django | `plugins/django/skills/guide/SKILL.md`, 필요에 따라 `server/`, `templates/`, `htmx/` | 일반 규칙 및 변경한 서버·템플릿·HTMX 영역의 세부 규칙 |
| Kopring | `plugins/kopring/skills/guide/SKILL.md`, 관련 스킬과 `docs/conventions/` | 공통 아키텍처 및 변경 영역의 주입·영속성·API·코루틴 등 기준 |
| NextTS | `plugins/nextts/skills/guide/SKILL.md`, 필요에 따라 `typescript/`, `components/`, `tailwind/`, `ui/` | TypeScript, App Router 및 변경 UI 영역의 세부 기준 |
| Planning | `plugins/planning/skills/rules/SKILL.md`, 필요에 따라 `spec/`, `done/`, `backlog/`, `handoff/` | 저장소 계획 설정, 문서 구조, 완료·의존성·이슈 정합성 기준 |

경로가 이동했거나 문서가 분리되었으면 실제 파일을 탐색하고 현재 원본을 확인한다. 존재하지 않는 기준을 추정하거나 리뷰 기준으로 단정하지 않는다.

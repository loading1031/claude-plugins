---
name: init
description: 프로젝트에 기획 진행 방식을 설정한다 — 프로젝트 설정에 이슈 또는 파일 백로그 방식을 지정한다
disable-model-invocation: true
argument-hint: "[기획 폴더 경로]"
---

# /planning:init — 기획 진행 방식 설정


먼저 `rules`에서 백로그 모드를 확인한다. **이슈 모드이면 [이슈 모드 참조](../rules/references/issue-backlog.md)의 이 명령 절차를 적용하고 아래 파일 모드 절차는 실행하지 않는다.** 프로젝트의 명시적 예외와 기존 사용자 승인 범위를 우선한다.

## 절차

1. 프로젝트 루트 `CLAUDE.md`를 읽는다. 없으면 만들지 묻는다.
2. `## 기획 설정` 절이 이미 있으면 내용을 보여 주고 바꿀 것만 묻는다. 없으면 아래 값을 사용자와 정한다.
   - 기획 폴더 (인자 `$ARGUMENTS`가 있으면 그 값, 없으면 `docs/planning` 제안)
   - 기준 문서 (기본 `plan.md`. 폴더에 이미 기획 문서가 있으면 그중 전체 기획에 해당하는 것)
   - 시각화 문서 URL (없으면 "없음")
   - 용어 (정해 둔 용어, 쓰지 않을 말. 없으면 "없음")
   - 기본 브랜치 (보통 `main`. `git symbolic-ref --short HEAD`나 기존 브랜치로 확인)
   - 개발 브랜치 (코드를 기본 브랜치와 따로 모을 브랜치. 예 `dev`. 쓰지 않으면 "없음". 쓰는데 브랜치가 없으면 기본 브랜치에서 만들고 push할지 묻는다)
   - 백로그 방식 (`issue` 또는 `file`). `issue`이면 작업 추적 저장소 `OWNER/REPO`를 확인한다
   - 작업지시서를 둘 곳 (원격이 GitHub이면 `issue`, 아니면 `file`)
   - 금지어 (기획 문서에 쓰지 않을 말. 없으면 "없음")
   - 동기화 표 (프로젝트 고유의 "무엇이 바뀌면 어디를 함께 고치나". 없으면 플러그인 기본 표를 씀)
3. `CLAUDE.md`에 절을 추가한다. 다른 내용은 건드리지 않는다. 진행 절차(명령 순서, 커밋 규칙)는 CLAUDE.md에 옮겨 적지 않는다(`rules` 0).

```markdown
## 기획 설정
planning 플러그인(/planning:backlog → /planning:spec → /planning:commit)이 읽는다.

- 기획 폴더: docs/planning
- 기준 문서: plan.md
- 시각화 문서: 없음
- 용어: 없음
- 기본 브랜치: main
- 개발 브랜치: 없음   <!-- 예: dev. 코드 브랜치는 여기서 분기하고 여기로 PR -->
- 기획 브랜치: plan/<ID>-<slug>
- 합치기 방식: PR (원격이 GitHub이 아니면 local)
- 작업지시서: issue (원격이 GitHub이 아니면 file)
- 금지어: 없음

### 동기화 표
| 바뀐 것 | 함께 고칠 곳 |
|---|---|
```

4. `.claude/settings.json`의 `extraKnownMarketplaces`에 이 마켓플레이스가 `"autoUpdate": true`로 없으면 추가할지 묻는다(`rules` 0 "버전").
5. `<폴더>/backlog.md`, `<폴더>/log.md`가 없으면 `rules` 스킬의 형식으로 빈 틀을 만든다. 이미 있으면 건드리지 않는다.
6. 기존 문서가 있으면 `/planning:backlog sweep`으로 첫 후보를 추릴지 묻는다.
7. 만들거나 바꾼 파일을 요약한다. 커밋은 하지 않는다(사용자가 `/planning:commit`으로).

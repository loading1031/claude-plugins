---
name: commit
description: 변경을 분석해 접두어 규칙에 맞는 커밋을 만든다. 기획(docs:)과 코드 커밋을 섞지 않는다
disable-model-invocation: true
argument-hint: "[msg \"메시지\"]"
---

# /planning:commit — 커밋

인자: `$ARGUMENTS` (`msg "메시지"`면 그 메시지를 쓴다)

## 접두어

| 작업 | 접두어 | 예 |
|---|---|---|
| 기획 문서 | `docs:` | `docs: 알림 채널을 텔레그램 봇으로 결정` |
| 기능 개발 | `feat:` | |
| 버그 수정 | `fix:` | |
| 리팩토링 | `refactor:` | |
| 테스트 | `test:` | |
| 설정·도구 | `chore:` | |

메시지:
- 프로젝트 언어로, 50자 이내
- "무엇을 바꿨나"보다 **무엇을 결정했나 / 왜**: "plan.md 수정"이 아니라 "모의 계좌 리셋 판정 기준 추가"
- 필요하면 빈 줄 뒤 본문에 바뀐 문서 목록

## 절차

1. 변경 확인: `git status --short`, `git diff --stat`
2. git 저장소가 아니면 멈추고 `git init`을 할지 묻는다.
3. 스테이징: 관련 파일만 이름으로 `git add`. `git add -A`, `git add .`는 쓰지 않는다. `.env`, 키, 토큰, 계좌 정보가 든 파일은 절대 넣지 않는다.
4. 기획 변경과 코드 변경이 섞여 있으면 커밋을 나눈다.
5. 브랜치 확인: 기본 브랜치(`main` 등)에 `docs:` 커밋을 하려 하면, 기획 브랜치에서 할 일이 아닌지 확인을 받는다. 설정·도구 변경(`chore:`)은 기본 브랜치에 바로 해도 된다.
6. 커밋. 저자 표시(Co-Authored-By 등)는 현재 세션의 시스템 지시를 따르고, 지시가 없으면 넣지 않는다.
   ```bash
   git commit -m "$(cat <<'EOF'
   docs: <메시지>

   <필요하면 본문>
   EOF
   )"
   ```
7. 확인: `git log --oneline -3`, `git status --short`, 현재 브랜치 이름

## 규칙
- amend는 사용자가 요청할 때만, push되지 않은 커밋에만 한다.
- push는 사용자가 요청할 때만 한다.
- pre-commit 훅이 실패하면 고친 뒤 새로 커밋한다. `--no-verify`를 쓰지 않는다.

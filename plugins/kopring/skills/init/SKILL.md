---
name: init
description: 프로젝트에 kopring 컨벤션을 적용한다 — CLAUDE.md에 구조·케이스 선언, pre-commit 훅 설치
disable-model-invocation: true
argument-hint: "[hexagonal | layered]"
---

# /kopring:init — 프로젝트에 컨벤션 적용

Claude 훅과 코드 규칙은 플러그인을 켜면 바로 동작한다. 이 명령은 플러그인이 대신할 수 없는 두 가지만 한다.

1. **CLAUDE.md 선언**: 아키텍처 규칙(`architecture` 스킬)은 프로젝트가 어느 구조를 쓰는지 알아야 한다.
2. **pre-commit 훅**: 사람이 Zed에서 직접 고친 코드도 검사하려면 git 훅이 저장소 안의 고정 경로에 있어야 한다. 플러그인 캐시 경로는 버전마다 바뀌므로 검사 스크립트를 저장소에 복사한다.

## 절차

### 1. 구조 확인
- 인자로 `hexagonal`(out 포트 헥사고날) 또는 `layered`(계층형)를 받는다. 없으면 `${CLAUDE_SKILL_DIR}/../../docs/architecture/choosing.md`의 기준을 요약해 보여 주고 사용자에게 묻는다.
- 사용하는 케이스(Redis 캐시, 시계열 DB, 외부 API, Kafka 등), **쓰지 않기로 한 기술**, 특정 경로에만 둘 클라이언트(명시적 예외), 기본 패키지를 묻는다. 이미 CLAUDE.md에 적혀 있으면("결정된 사항" 등) 거기서 옮기고 묻지 않는다.

### 2. CLAUDE.md
프로젝트 루트 `CLAUDE.md`에 아래 절이 없으면 추가하고, 있으면 값만 맞춘다. 다른 내용은 건드리지 않는다.

```markdown
## 컨벤션
- kopring 플러그인을 따른다 (규칙은 .kt 작업 시 자동 적용, 검사 훅 동작)
- 아키텍처: out 포트 헥사고날   <!-- 또는: 계층형 -->
- 사용하는 케이스: <예: 시계열 DB, 외부 API>
- 기본 패키지: <com.example.app>
- 명시적 예외: <없으면 "없음". 예: adapter/out/timeseries에서만 JdbcClient + SQL 허용>
- 쓰지 않는 기술: <없으면 "없음". 예: Redis, Kafka, R2DBC>   <!-- 훅 project/forbidden-tech -->
- 클라이언트 위치: <없으면 "없음". 예: JdbcClient → adapter/out/timeseries>   <!-- 훅 project/client-location -->
```

### 3. pre-commit 훅
1. `${CLAUDE_PLUGIN_ROOT}/scripts/check_kotlin_conventions.py`를 프로젝트의 `scripts/conventions/check_kotlin_conventions.py`로 복사한다. 이미 있고 내용이 다르면 차이를 보여 주고 덮어쓸지 묻는다.
2. `.githooks/pre-commit`이 없으면 아래 내용으로 만들고 실행 권한을 준다. 있으면 이 검사 줄이 들어 있는지만 확인한다.
   ```sh
   #!/usr/bin/env sh
   # 커밋되는 .kt 파일의 Kotlin + Spring 컨벤션 검사 (kopring 플러그인)
   files=$(git diff --cached --name-only --diff-filter=ACM -- '*.kt')
   [ -z "$files" ] && exit 0
   # shellcheck disable=SC2086
   exec python3 "$(git rev-parse --show-toplevel)/scripts/conventions/check_kotlin_conventions.py" --files $files
   ```
3. git 저장소면 `git config core.hooksPath .githooks`를 실행한다. 이미 다른 hooksPath가 설정돼 있으면 바꾸지 말고 사용자에게 알린다.
4. 플러그인을 업데이트한 뒤에는 이 명령을 다시 실행해 복사본을 맞추라고 안내한다. 복사본이 플러그인 검사기와 다르면 Claude 훅이 편집 때마다 경고한다.

### 4. 확인
- `python3 --version`이 3.10 이상인지 확인한다.
- 결과를 요약한다: CLAUDE.md에 쓴 값, 복사한 파일, hooksPath 설정 여부.

## 참고
- 규칙 전체와 rule id 색인: `${CLAUDE_SKILL_DIR}/../../docs/conventions/README.md`
- 저장소의 `.kt` 전체를 한 번에 검사: Bash에서 `kopring-check`

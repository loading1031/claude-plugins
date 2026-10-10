#!/usr/bin/env python3
"""Kotlin + Spring 컨벤션 검사기.

규칙 목록과 근거는 docs/conventions/README.md 참고.

사용법:
  - Claude Code PreToolUse 훅: 인자 없이 실행, stdin으로 훅 JSON을 받는다.
    Write/Edit/MultiEdit 결과 파일을 재구성해서 "새로 생긴" 위반만 막는다(exit 2).
  - git pre-commit / CI: --files <경로...> 로 실행, 위반이 있으면 exit 1.
"""
import json
import os
import re
import sys
from collections import Counter
from pathlib import Path

DERIVED_QUERY = re.compile(
    r"\bfun\s+((?:find|read|get|query|search|stream|count|exists|delete|remove)\w*?By)(\w+)\s*\("
)
CONDITION_JOINER = re.compile(r"(?:And|Or)(?=[A-Z])")


def _derived_query_too_long(line: str) -> bool:
    m = DERIVED_QUERY.search(line)
    return bool(m) and len(CONDITION_JOINER.findall(m.group(2))) >= 2


# launch { / async(ctx) { 처럼 코루틴 빌더를 여는 줄. 인자에 CoroutineName이 없으면 위반
COROUTINE_BUILDER = re.compile(r"\b(?:launch|async)\s*(?:\(((?:[^()]|\([^()]*\))*)\))?\s*\{")


def _unnamed_coroutine(line: str) -> bool:
    m = COROUTINE_BUILDER.search(line)
    return bool(m) and "CoroutineName" not in (m.group(1) or "")


GENERIC_CONFIG_NAME = re.compile(
    r"\bclass\s+(?:App|Application|Common|Global|Main|Base|Default|Misc|Etc|Bean)Config\b"
)
MAX_BEANS_PER_CONFIG = 6

# 외부 기술 클라이언트. 어댑터(계층형: infrastructure, 헥사고날: adapter/out)와 config에서만 쓴다
TECH_CLIENT = re.compile(
    r"\b(?:RedisTemplate|StringRedisTemplate|ReactiveRedisTemplate|RedissonClient|"
    r"KafkaTemplate|RabbitTemplate|RestClient|RestTemplate|WebClient|"
    r"JdbcTemplate|NamedParameterJdbcTemplate|EntityManager|MongoTemplate|"
    r"ElasticsearchOperations|InfluxDBClient)\b"
)
TECH_CLIENT_ALLOWED = ("/infrastructure/", "/adapter/out/", "/config/")

# 리스너가 구체 이벤트 타입을 받는지. 상위 타입이나 classes= 지정은 사용처 찾기로 추적이 안 된다
EVENT_LISTENER = re.compile(
    r"@(?:Transactional)?EventListener\b(\([^)]*\))?"
    r"(?:\s*@\w+(?:\([^)]*\))?)*"
    r"\s*(?:(?:public|internal|private|protected|suspend|open|override)\s+)*"
    r"fun\s+\w+\s*\(\s*(?:\w+\s*:\s*([\w.]+))?",
    re.S,
)
NON_SPECIFIC_EVENT_TYPES = {"Any", "Object", "ApplicationEvent", "PayloadApplicationEvent"}


# (id, 설명, 매칭 함수, main 소스에만 적용 여부, 경로 조건)
RULES = [
    (
        "jdsl/no-string-query",
        "@Query/@NativeQuery 문자열 쿼리 금지 → Kotlin JDSL(KotlinJdslJpqlExecutor)로 작성",
        lambda line: re.search(r"@(?:Query|NativeQuery)\s*\(", line),
        False,
        None,
    ),
    (
        "jdsl/no-create-query",
        "EntityManager.createQuery/createNativeQuery 문자열 쿼리 금지 → Kotlin JDSL로 작성",
        lambda line: re.search(r"\.create(?:Native)?Query\s*\(", line),
        False,
        None,
    ),
    (
        "jdsl/derived-query-max-2",
        "이름 규칙 쿼리 메서드는 조건 2개까지 → 3개 이상이면 Kotlin JDSL로 작성",
        _derived_query_too_long,
        False,
        None,
    ),
    (
        "di/no-autowired",
        "@Autowired/@Inject 금지 → 생성자 주입(생성자가 하나면 애너테이션 생략)",
        lambda line: re.search(r"@(?:field:)?(?:Autowired|Inject)\b", line),
        True,
        None,
    ),
    (
        "config/no-value",
        "@Value 금지 → @ConfigurationProperties 클래스로 묶어서 주입",
        lambda line: re.search(r"@(?:field:)?Value\s*\(", line),
        True,
        None,
    ),
    (
        "di/selection-in-config-only",
        "@Primary/@Qualifier/@Profile/@ConditionalOn* 은 config 패키지에서만 → 구현체 선택은 @Configuration에서 명시",
        lambda line: re.search(r"@(?:Primary|Qualifier|Profile|ConditionalOn\w+)\b", line),
        True,
        lambda path: "/config/" not in path,
    ),
    (
        "domain/no-spring",
        "domain 패키지는 Spring에 의존하지 않는다 → 빈 등록은 config의 @Bean으로",
        lambda line: re.match(r"\s*import\s+org\.springframework\.", line),
        True,
        lambda path: "/domain/" in path,
    ),
    (
        "domain/no-coroutines",
        "domain 패키지는 동기 코드로 쓴다 → 코루틴은 api·infrastructure 경계에서만",
        lambda line: re.match(r"\s*import\s+kotlinx\.coroutines\.", line)
        or re.search(r"\bsuspend\s+fun\b", line),
        True,
        lambda path: "/domain/" in path,
    ),
    (
        "config/generic-name",
        "기능이 드러나지 않는 Config 이름 금지 → <기능>Config (예: LabelPrinterConfig)",
        lambda line: GENERIC_CONFIG_NAME.search(line),
        True,
        None,
    ),
    (
        "coroutine/no-global-scope",
        "GlobalScope 금지 → 수명이 관리되는 CoroutineScope를 주입받아 사용",
        lambda line: re.search(r"\bGlobalScope\b", line),
        False,
        None,
    ),
    (
        "coroutine/no-run-blocking",
        "메인 코드에서 runBlocking 금지 → suspend 함수로 만들거나 경계에서 스코프로 실행",
        lambda line: re.search(r"\brunBlocking\b", line),
        True,
        None,
    ),
    (
        "coroutine/name-required",
        "launch/async에는 CoroutineName을 붙인다 → launch(CoroutineName(\"…\")) { }",
        _unnamed_coroutine,
        True,
        None,
    ),
    (
        "arch/tech-client-outside-adapter",
        "Redis·Kafka·HTTP·JDBC 등 외부 기술 클라이언트는 어댑터에서만 → infrastructure 또는 adapter/out, 설정은 config",
        lambda line: TECH_CLIENT.search(line),
        True,
        lambda path: not any(p in path for p in TECH_CLIENT_ALLOWED),
    ),
    (
        "arch/application-no-adapter",
        "application은 adapter를 import하지 않는다 → application/port/out 인터페이스에 의존",
        lambda line: re.match(r"\s*import\s+[\w.]*\.adapter\.", line),
        True,
        lambda path: "/application/" in path,
    ),
    (
        "arch/domain-no-outer",
        "domain은 바깥 계층을 import하지 않는다",
        lambda line: re.match(
            r"\s*import\s+[\w.]*\.(?:application|adapter|infrastructure|api|config)\.", line
        ),
        True,
        lambda path: "/domain/" in path,
    ),
    (
        "cache/name-constant",
        "캐시 이름 문자열 직접 사용 금지 → config의 CacheNames 상수 사용",
        lambda line: re.search(
            r"@(?:Cacheable|CachePut|CacheEvict)\s*\(\s*(?:(?:value|cacheNames)\s*=\s*)?\[?\s*\"",
            line,
        ),
        True,
        None,
    ),
    (
        "event/topic-constant",
        "토픽·큐 이름 문자열 직접 사용 금지 → 토픽 상수 object 사용",
        lambda line: re.search(
            r"@(?:KafkaListener|RabbitListener)\s*\([^)]*\b(?:topics|queues)\s*=\s*\[?\s*\"", line
        )
        or re.search(r"\b\w*[kK]afkaTemplate\.send\(\s*\"", line),
        True,
        None,
    ),
    (
        "coroutine/inject-dispatcher",
        "Dispatchers.IO/Default를 직접 쓰지 않는다 → config에서 만든 Dispatcher를 주입",
        lambda line: re.search(r"\bDispatchers\.(?:IO|Default|Unconfined)\b", line),
        True,
        lambda path: "/config/" not in path,
    ),
]


def find_violations(path: str, content: str) -> list[tuple[str, str, int, str]]:
    if not path.endswith(".kt"):
        return []
    is_test = "/src/test/" in path
    found = []
    lines = content.splitlines()
    for no, line in enumerate(lines, 1):
        if line.lstrip().startswith("//"):
            continue
        for rule_id, msg, match, main_only, path_cond in RULES:
            if main_only and is_test:
                continue
            if path_cond and not path_cond(path):
                continue
            if match(line):
                found.append((rule_id, msg, no, line.strip()))
    # 파일 단위 규칙: 트랜잭션(ThreadLocal 기반)과 suspend를 섞지 않는다
    if not is_test and re.search(r"@Transactional\b", content):
        for no, line in enumerate(lines, 1):
            if re.search(r"\bsuspend\s+fun\b", line):
                found.append(
                    (
                        "coroutine/no-suspend-transactional",
                        "@Transactional이 있는 파일에 suspend fun 금지 → DB 계층은 동기로, 호출 측에서 withContext(ioDispatcher)",
                        no,
                        line.strip(),
                    )
                )
    # 파일 단위 규칙: Config 하나에 @Bean이 너무 많으면 기능별로 나눈다
    if not is_test and re.search(r"@Configuration\b", content):
        bean_count = len(re.findall(r"@Bean\b", content))
        if bean_count > MAX_BEANS_PER_CONFIG:
            found.append(
                (
                    "config/too-many-beans",
                    f"Config 하나에 @Bean은 {MAX_BEANS_PER_CONFIG}개까지 → 기능별 Config로 나눈다",
                    1,
                    f"@Bean {bean_count}개",
                )
            )
    # 파일 단위 규칙: 이벤트 리스너는 구체 이벤트 타입 하나만 받는다
    for m in EVENT_LISTENER.finditer(content):
        args, param_type = m.group(1) or "", m.group(2) or ""
        base_type = param_type.split(".")[-1]
        if "classes" in args or base_type in NON_SPECIFIC_EVENT_TYPES or not param_type:
            no = content.count("\n", 0, m.start()) + 1
            found.append(
                (
                    "event/listener-concrete-type",
                    "리스너는 구체 이벤트 클래스 하나를 파라미터로 받는다 → classes= 나 Any/ApplicationEvent 금지",
                    no,
                    lines[no - 1].strip(),
                )
            )
    # 파일 단위 규칙: JPA 엔티티를 data class로 만들지 않는다
    if re.search(r"@Entity\b", content):
        for no, line in enumerate(lines, 1):
            if re.search(r"\bdata\s+class\b", line):
                found.append(
                    (
                        "jpa/no-data-class-entity",
                        "@Entity를 data class로 만들지 않는다 → 일반 class + kotlin(\"plugin.jpa\")",
                        no,
                        line.strip(),
                    )
                )
    return found


def _resulting_content(tool: str, tool_input: dict, before: str) -> str | None:
    if tool == "Write":
        return tool_input.get("content", "")
    if tool == "Edit":
        edits = [tool_input]
    elif tool == "MultiEdit":
        edits = tool_input.get("edits", [])
    else:
        return None
    after = before
    for e in edits:
        old, new = e.get("old_string", ""), e.get("new_string", "")
        if e.get("replace_all"):
            after = after.replace(old, new)
        else:
            after = after.replace(old, new, 1)
    return after


def _format(path: str, violations) -> str:
    out = [f"[kotlin-conventions] {path}"]
    for rule_id, msg, no, line in violations:
        out.append(f"  {no}: [{rule_id}] {msg}\n      > {line}")
    root = os.environ.get("CLAUDE_PLUGIN_ROOT")
    ref = f"{root}/docs/conventions/README.md" if root else "kopring 플러그인의 docs/conventions/README.md"
    out.append(f"  근거: {ref}")
    return "\n".join(out)


def run_hook() -> int:
    payload = json.load(sys.stdin)
    tool = payload.get("tool_name", "")
    tool_input = payload.get("tool_input", {}) or {}
    path = tool_input.get("file_path", "")
    if not path.endswith(".kt"):
        return 0
    p = Path(path)
    before = p.read_text(encoding="utf-8") if p.exists() else ""
    after = _resulting_content(tool, tool_input, before)
    if after is None:
        return 0
    # 기존 위반은 두고, 이번 변경으로 새로 생긴 위반만 막는다
    old = Counter((r, l) for r, _, _, l in find_violations(path, before))
    new_violations = []
    for v in find_violations(path, after):
        key = (v[0], v[3])
        if old[key] > 0:
            old[key] -= 1
        else:
            new_violations.append(v)
    if new_violations:
        print(_format(path, new_violations), file=sys.stderr)
        return 2
    return 0


def run_files(paths: list[str]) -> int:
    failed = False
    for path in paths:
        p = Path(path)
        if not p.is_file():
            continue
        violations = find_violations(str(p.resolve()), p.read_text(encoding="utf-8"))
        if violations:
            failed = True
            print(_format(path, violations), file=sys.stderr)
    return 1 if failed else 0


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--files":
        sys.exit(run_files(sys.argv[2:]))
    sys.exit(run_hook())

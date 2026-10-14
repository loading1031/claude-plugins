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
    r"JdbcTemplate|NamedParameterJdbcTemplate|JdbcClient|EntityManager|MongoTemplate|"
    r"ElasticsearchOperations|InfluxDBClient)\b"
)
TECH_CLIENT_ALLOWED = ("/infrastructure/", "/adapter/out/", "/config/")

# 리스너가 구체 이벤트 타입을 받는지. 상위 타입이나 classes= 지정은 사용처 찾기로 추적이 안 된다
EVENT_LISTENER = re.compile(
    r"@(?:(?:Transactional)?EventListener|ApplicationModuleListener)\b(\([^)]*\))?"
    r"(?:\s*@\w+(?:\([^)]*\))?)*"
    r"\s*(?:(?:public|internal|private|protected|suspend|open|override)\s+)*"
    r"fun\s+\w+\s*\(\s*(?:\w+\s*:\s*([\w.]+))?",
    re.S,
)
NON_SPECIFIC_EVENT_TYPES = {"Any", "Object", "ApplicationEvent", "PayloadApplicationEvent"}


# 현재 시각을 시스템 시계에서 바로 읽는 호출
NOW_CALL = re.compile(
    r"\b(?:Instant|LocalDateTime|LocalDate|LocalTime|ZonedDateTime|OffsetDateTime|OffsetTime|"
    r"Year|YearMonth|MonthDay)\.now\("
)


def _call_args(text: str, start: int) -> str:
    depth = 0
    for i, ch in enumerate(text[start:], start):
        if ch == "(":
            depth += 1
        elif ch == ")":
            if depth == 0:
                return text[start:i]
            depth -= 1
    return text[start:]


# now()와 now(zone)은 시스템 시계를 읽는다. now(clock)처럼 다른 인자를 넘기면 통과
def _now_without_clock(line: str) -> bool:
    for m in NOW_CALL.finditer(line):
        args = _call_args(line, m.end()).strip()
        if not args or re.search(r"Zone|zone", args):
            return True
    return False


# 괄호 안의 최상위 인자 개수. 문자열 안의 쉼표는 세지 않는다(줄 단위 근사)
def _arg_count(text: str, start: int) -> int:
    depth, count, in_str, seen = 0, 1, False, False
    for ch in text[start:]:
        if in_str:
            in_str = ch != '"'
            continue
        if ch == '"':
            in_str, seen = True, True
        elif ch in "([{":
            depth += 1
        elif ch in ")]}":
            if depth == 0:
                return count if seen else 0
            depth -= 1
        elif ch == "," and depth == 0:
            count += 1
        elif not ch.isspace():
            seen = True
    return count


# 나눗셈·자릿수 조정에서 반올림 방식을 정하지 않은 호출
SCALE_CALL = re.compile(r"\.(divide|setScale)\(")


def _missing_rounding(line: str) -> bool:
    if "RoundingMode" in line or "MathContext" in line:
        return False
    return any(_arg_count(line, m.end()) == 1 for m in SCALE_CALL.finditer(line))


# Double 값을 BigDecimal 생성자에 넘기는 것. 문자열 생성자나 toBigDecimal()을 쓴다
DOUBLE_CTOR = re.compile(
    r"\bBigDecimal\(\s*(?:-?\d+\.\d*(?:[eE][-+]?\d+)?[fFdD]?|-?\d+(?:[eE][-+]?\d+)?[fFdD]|[^()\"]*\.toDouble\(\)|[^()\"]*\.toFloat\(\))\s*\)"
)

# 로그 호출. 문자열 리터럴은 빼고, 문자열 템플릿($x, ${...})과 인자만 본다
LOG_CALL = re.compile(r"\b(?:log|logger|LOG|LOGGER)\.(?:trace|debug|info|warn|error)\s*[({]")
SECRET_NAME = re.compile(
    r"\b(?:app_?key|app_?secret|client_?secret|secret_?key|api_?key|access_?token|refresh_?token|"
    r"password|passwd|secret)\b",
    re.I,
)


def _code_and_templates(line: str) -> str:
    out, i, in_str = [], 0, False
    while i < len(line):
        ch = line[i]
        if in_str:
            if ch == "\\":
                i += 2
                continue
            if ch == '"':
                in_str = False
            elif ch == "$" and i + 1 < len(line) and line[i + 1] == "{":
                end = line.find("}", i)
                end = len(line) if end < 0 else end
                out.append(" " + line[i + 2 : end] + " ")
                i = end + 1
                continue
            elif ch == "$":
                m = re.match(r"\$(\w+)", line[i:])
                if m:
                    out.append(" " + m.group(1) + " ")
                    i += len(m.group(0))
                    continue
        elif ch == '"':
            in_str = True
        else:
            out.append(ch)
        i += 1
    return "".join(out)


def _logs_secret(line: str) -> bool:
    m = LOG_CALL.search(line)
    return bool(m) and bool(SECRET_NAME.search(_code_and_templates(line[m.end() :])))


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
    (
        "time/inject-clock",
        "현재 시각을 시스템 시계에서 바로 읽지 않는다 → 주입받은 Clock으로 Instant.now(clock)",
        _now_without_clock,
        True,
        lambda path: "/config/" not in path,
    ),
    (
        "bigdecimal/rounding-mode",
        "divide/setScale에 반올림 방식을 정한다 → divide(x, scale, RoundingMode.DOWN), setScale(n, RoundingMode.HALF_UP)",
        _missing_rounding,
        True,
        None,
    ),
    (
        "bigdecimal/no-double-ctor",
        "BigDecimal(Double) 금지(0.1이 0.1000000000000000055…가 된다) → BigDecimal(\"0.1\") 또는 \"0.1\".toBigDecimal()",
        lambda line: DOUBLE_CTOR.search(line),
        False,
        None,
    ),
    (
        "log/no-secret",
        "비밀번호·키·토큰을 로그에 남기지 않는다 → 마스킹하거나 식별자만 남긴다",
        _logs_secret,
        True,
        None,
    ),
]


# 프로젝트 CLAUDE.md "## 컨벤션" 절의 선언. 기술 이름 → 그 기술을 쓰는 import 접두어
TECH_IMPORTS = {
    "redis": ("org.springframework.data.redis", "org.redisson", "io.lettuce", "redis.clients"),
    "kafka": ("org.springframework.kafka", "org.apache.kafka"),
    "rabbitmq": ("org.springframework.amqp", "com.rabbitmq"),
    "r2dbc": ("org.springframework.r2dbc", "org.springframework.data.r2dbc", "io.r2dbc"),
    "mongodb": ("org.springframework.data.mongodb", "com.mongodb"),
    "elasticsearch": ("org.springframework.data.elasticsearch", "co.elastic"),
    "webflux": ("org.springframework.web.reactive",),
}
_project_cache: dict[str, dict] = {}


def project_conventions(path: str) -> dict:
    """파일에서 위로 올라가며 "## 컨벤션" 절이 있는 CLAUDE.md를 찾아 선언을 읽는다.

    - 쓰지 않는 기술: Redis, Kafka, R2DBC   → 그 기술의 import 금지
    - 클라이언트 위치: JdbcClient → adapter/out/timeseries, …   → 그 클라이언트는 그 경로에서만
    """
    d = Path(path).resolve().parent
    for cand in [d, *d.parents]:
        key = str(cand)
        if key in _project_cache:
            return _project_cache[key]
        claude = cand / "CLAUDE.md"
        if claude.is_file():
            text = claude.read_text(encoding="utf-8", errors="ignore")
            m = re.search(r"^## 컨벤션\s*$(.*?)(?=^## |\Z)", text, re.M | re.S)
            if m:
                conf = _parse_conventions(m.group(1))
                _project_cache[key] = conf
                return conf
        if (cand / ".git").exists():
            break
    return {"forbidden": {}, "locations": {}}


def _setting(body: str, key: str) -> str:
    m = re.search(rf"^- {key}:\s*(.+)$", body, re.M)
    v = m.group(1).split("<!--")[0].strip() if m else ""
    return "" if v in ("", "없음") else v


def _parse_conventions(body: str) -> dict:
    forbidden = {}
    for name in re.split(r"[,、]", _setting(body, "쓰지 않는 기술")):
        name = name.strip().strip("`").lower()
        if name in TECH_IMPORTS:
            forbidden[name] = TECH_IMPORTS[name]
    locations = {}
    for item in re.split(r",(?![^()]*\))", _setting(body, "클라이언트 위치")):
        m = re.match(r"\s*`?(\w+)`?\s*(?:→|->|=|:)\s*`?([\w/.-]+?)`?\s*$", item)
        if m:
            locations.setdefault(m.group(1), []).append("/" + m.group(2).strip("/") + "/")
    return {"forbidden": forbidden, "locations": locations}


def _project_violations(path: str, lines: list[str], is_test: bool) -> list[tuple[str, str, int, str]]:
    conf = project_conventions(path)
    found = []
    for no, line in enumerate(lines, 1):
        imp = re.match(r"\s*import\s+([\w.]+)", line)
        if imp:
            for tech, prefixes in conf["forbidden"].items():
                if imp.group(1).startswith(prefixes):
                    found.append((
                        "project/forbidden-tech",
                        f"이 프로젝트는 {tech}를 쓰지 않는다(CLAUDE.md \"컨벤션\"의 \"쓰지 않는 기술\") → 선언을 바꾸려면 사용자에게 먼저 묻는다",
                        no, line.strip()))
        if is_test or line.lstrip().startswith(("//", "import ")):
            continue
        for client, dirs in conf["locations"].items():
            if re.search(rf"\b{re.escape(client)}\b", line) and not any(d in path for d in dirs) and "/config/" not in path:
                found.append((
                    "project/client-location",
                    f"{client}는 {', '.join(d.strip('/') for d in dirs)}에서만 쓴다(CLAUDE.md \"컨벤션\"의 \"클라이언트 위치\")",
                    no, line.strip()))
    return found


def find_violations(path: str, content: str) -> list[tuple[str, str, int, str]]:
    if not path.endswith(".kt"):
        return []
    is_test = "/src/test/" in path
    lines = content.splitlines()
    found = _project_violations(path, lines, is_test)
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


def _stale_copy_warning(path: str) -> None:
    """저장소에 복사한 pre-commit 검사기가 플러그인 것과 다르면 사용자에게 알린다(막지는 않는다)."""
    d = Path(path).resolve().parent
    for cand in [d, *d.parents]:
        copy = cand / "scripts" / "conventions" / "check_kotlin_conventions.py"
        if copy.is_file():
            if copy.read_bytes() != Path(__file__).read_bytes():
                print(json.dumps({"systemMessage": "kopring: 저장소의 scripts/conventions/check_kotlin_conventions.py가 플러그인 검사기와 다르다. "
                                  "git pre-commit 규칙이 어긋나 있으니 /kopring:init을 다시 실행해 맞춘다."}, ensure_ascii=False))
            return
        if (cand / ".git").exists():
            return


def run_hook() -> int:
    payload = json.load(sys.stdin)
    tool = payload.get("tool_name", "")
    tool_input = payload.get("tool_input", {}) or {}
    path = tool_input.get("file_path", "")
    # 테스트(OpenApiSpecTest)가 만드는 API 스펙은 손으로 고치지 않는다
    if path.replace("\\", "/").endswith("openapi/openapi.json") and tool in ("Write", "Edit", "MultiEdit"):
        print(f"[kotlin-conventions] {path}\n  [api/spec-generated] openapi/openapi.json은 테스트가 만든다 → 컨트롤러·DTO를 고치고 ./gradlew test --tests '*OpenApiSpecTest'로 다시 만든다", file=sys.stderr)
        return 2
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
    _stale_copy_warning(path)
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

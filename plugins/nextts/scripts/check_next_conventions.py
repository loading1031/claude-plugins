#!/usr/bin/env python3
"""Next.js + TypeScript 컨벤션 검사기.

규칙 목록과 근거는 docs/conventions/README.md 참고.

사용법:
  - Claude Code PreToolUse 훅: 인자 없이 실행, stdin으로 훅 JSON을 받는다.
    Write/Edit/MultiEdit 결과 파일을 재구성해서 "새로 생긴" 위반만 막는다(exit 2).
  - git pre-commit / CI: --files <경로...> 로 실행, 위반이 있으면 exit 1.
  - 타입 검사: --typecheck <경로...> 로 실행, 파일이 속한 Next 프로젝트마다 tsc --noEmit.

Next 프로젝트(가장 가까운 package.json의 의존성에 next가 있는 폴더) 안의 파일만 검사한다.
"""
import json
import os
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

TS_EXT = (".ts", ".tsx", ".mts", ".cts")
JS_EXT = (".js", ".jsx", ".mjs", ".cjs")
# public/은 빌드하지 않고 그대로 내보내는 정적 파일이라 JS를 둘 수 있다
JS_ALLOWED_DIRS = ("/public/", "/node_modules/", "/.next/")

SECRET_PUBLIC_ENV = re.compile(
    r"\bNEXT_PUBLIC_\w*?(?:SECRET|PRIVATE|PASSWORD|PASSWD|SERVICE_ROLE|SERVICE_KEY|DATABASE_URL|DB_URL)\w*"
)
MEMO_NAMES = ("useMemo", "useCallback", "memo")
REACT_IMPORT = re.compile(r"import\s+(?:type\s+)?(?:\w+\s*,\s*)?\{([^}]*)\}\s*from\s*['\"]react['\"]", re.S)
REACT_NS_MEMO = re.compile(r"\bReact\.(?:useMemo|useCallback|memo)\b")
USE_CLIENT = re.compile(r"\A(?:\s|//[^\n]*\n|/\*.*?\*/)*['\"]use client['\"]", re.S)
REACT_COMPILER_ON = re.compile(r"\breactCompiler\s*:\s*(?:true|\{)")

_root_cache: dict[str, Path | None] = {}
_conv_cache: dict[str, dict] = {}


def next_root(path: str) -> Path | None:
    """파일에서 위로 올라가며 next를 의존성에 둔 package.json이 있는 폴더를 찾는다."""
    d = Path(path).resolve().parent
    for cand in [d, *d.parents]:
        key = str(cand)
        if key in _root_cache:
            return _root_cache[key]
        pkg = cand / "package.json"
        if pkg.is_file():
            try:
                data = json.loads(pkg.read_text(encoding="utf-8"))
            except (ValueError, OSError):
                data = {}
            deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
            if "next" in deps:
                _root_cache[key] = cand
                return cand
        if (cand / ".git").exists():
            break
    _root_cache[str(d)] = None
    return None


def react_compiler_on(root: Path) -> bool:
    for name in ("next.config.ts", "next.config.mts", "next.config.js", "next.config.mjs"):
        f = root / name
        if f.is_file() and REACT_COMPILER_ON.search(f.read_text(encoding="utf-8", errors="ignore")):
            return True
    return False


def _setting(body: str, key: str) -> str:
    m = re.search(rf"^- {key}:\s*(.+)$", body, re.M)
    v = m.group(1).split("<!--")[0].strip().strip("`") if m else ""
    return "" if v in ("", "없음") else v


def project_conventions(path: str) -> dict:
    """파일에서 위로 올라가며 "## 프론트엔드 컨벤션" 절이 있는 CLAUDE.md를 찾아 선언을 읽는다.

    - 백엔드 호출: 서버만 / 백엔드 주소 환경변수: BACKEND_URL   → 클라이언트에서 그 주소를 쓰지 않는다
    - 번들러: webpack 허용                                    → --webpack 검사를 끈다
    - 쓰지 않는 라이브러리: axios, moment                      → 그 패키지 import·의존성 추가 금지
    """
    d = Path(path).resolve().parent
    for cand in [d, *d.parents]:
        key = str(cand)
        if key in _conv_cache:
            return _conv_cache[key]
        claude = cand / "CLAUDE.md"
        if claude.is_file():
            text = claude.read_text(encoding="utf-8", errors="ignore")
            m = re.search(r"^## 프론트엔드 컨벤션\s*$(.*?)(?=^## |\Z)", text, re.M | re.S)
            if m:
                body = m.group(1)
                env = _setting(body, "백엔드 주소 환경변수")
                conf = {
                    "backend_env": env if "서버" in _setting(body, "백엔드 호출") and env else "",
                    "webpack_ok": "webpack" in _setting(body, "번들러").lower(),
                    "forbidden_libs": [
                        n.strip().strip("`") for n in re.split(r"[,、]", _setting(body, "쓰지 않는 라이브러리")) if n.strip()
                    ],
                }
                _conv_cache[key] = conf
                return conf
        if (cand / ".git").exists():
            break
    return {"backend_env": "", "webpack_ok": False, "forbidden_libs": []}


def _is_comment(line: str, is_env: bool = False) -> bool:
    s = line.lstrip()
    return s.startswith("#") if is_env else s.startswith(("//", "/*", "*"))


def _memo_violations(lines: list[str], content: str) -> list[tuple[int, str]]:
    found = []
    for m in REACT_IMPORT.finditer(content):
        names = {n.strip().split(" as ")[0].strip() for n in m.group(1).split(",")}
        if not names & set(MEMO_NAMES):
            continue
        first = content.count("\n", 0, m.start())
        last = content.count("\n", 0, m.end())
        for no in range(first, last + 1):
            if re.search(r"\b(?:useMemo|useCallback|memo)\b", lines[no]):
                found.append((no + 1, lines[no].strip()))
    for no, line in enumerate(lines, 1):
        if not _is_comment(line) and REACT_NS_MEMO.search(line):
            found.append((no, line.strip()))
    return found


def _imports_package(line: str, lib: str) -> bool:
    return bool(re.search(rf"""(?:from\s+|import\s+|require\(\s*|import\(\s*)['"]{re.escape(lib)}(?:/[^'"]*)?['"]""", line))


def find_violations(path: str, content: str) -> list[tuple[str, str, int, str]]:
    root = next_root(path)
    if root is None:
        return []
    name = Path(path).name
    lines = content.splitlines()
    conf = project_conventions(path)
    found = []

    def add(rule_id, msg, no, line):
        found.append((rule_id, msg, no, line))

    if name.endswith(JS_EXT) and not any(d in path for d in JS_ALLOWED_DIRS):
        add("ts/no-js-file", "JavaScript 파일을 만들지 않는다 → .ts/.tsx로 쓴다(설정 파일도 next.config.ts, postcss.config.ts, eslint.config.ts)",
            1, name)
        return found

    if name == "tsconfig.json":
        for no, line in enumerate(lines, 1):
            if re.search(r"\"allowJs\"\s*:\s*true", line):
                add("ts/no-allow-js", "tsconfig의 allowJs는 false → JS 파일을 프로젝트에 들이지 않는다", no, line.strip())
        return found

    if name == "package.json":
        for no, line in enumerate(lines, 1):
            if not conf["webpack_ok"] and re.search(r"\bnext\s+(?:dev|build)\b[^\"]*--webpack\b", line):
                add("bundler/no-webpack", "--webpack을 쓰지 않는다 → Turbopack(Next 16 기본). 필요하면 CLAUDE.md \"프론트엔드 컨벤션\"에 \"번들러: webpack 허용\"을 사용자와 정한다",
                    no, line.strip())
            for lib in conf["forbidden_libs"]:
                if re.search(rf"^\s*\"{re.escape(lib)}\"\s*:", line):
                    add("project/forbidden-lib", f"이 프로젝트는 {lib}를 쓰지 않는다(CLAUDE.md \"프론트엔드 컨벤션\"의 \"쓰지 않는 라이브러리\") → 선언을 바꾸려면 사용자에게 먼저 묻는다",
                        no, line.strip())
        return found

    is_env = name.startswith(".env")
    if not (name.endswith(TS_EXT) or is_env):
        return found

    is_client = not is_env and bool(USE_CLIENT.match(content))
    env = conf["backend_env"]
    public_backend = re.compile(rf"\bNEXT_PUBLIC_\w*{re.escape(env)}\b") if env else None
    for no, line in enumerate(lines, 1):
        if _is_comment(line, is_env):
            continue
        if SECRET_PUBLIC_ENV.search(line):
            add("secret/no-public-secret", "비밀값에 NEXT_PUBLIC_을 붙이지 않는다(브라우저 번들에 들어간다) → 서버 코드에서 접두어 없이 읽는다",
                no, line.strip())
        if public_backend and public_backend.search(line):
            add("project/backend-server-only", f"백엔드 주소({env})를 브라우저에 내보내지 않는다(CLAUDE.md \"프론트엔드 컨벤션\"의 \"백엔드 호출: 서버만\") → 서버 컴포넌트·라우트 핸들러·서버 액션에서 호출",
                no, line.strip())
        elif is_client and env and re.search(rf"\b{re.escape(env)}\b", line):
            add("project/backend-server-only", f"클라이언트 컴포넌트에서 백엔드({env})를 부르지 않는다 → 서버 컴포넌트·라우트 핸들러·서버 액션에서 호출하고 결과를 props로 넘긴다",
                no, line.strip())
        for lib in conf["forbidden_libs"]:
            if _imports_package(line, lib):
                add("project/forbidden-lib", f"이 프로젝트는 {lib}를 쓰지 않는다(CLAUDE.md \"프론트엔드 컨벤션\"의 \"쓰지 않는 라이브러리\") → 선언을 바꾸려면 사용자에게 먼저 묻는다",
                    no, line.strip())

    if not is_env and react_compiler_on(root):
        for no, line in _memo_violations(lines, content):
            add("memo/no-manual-memo", "useMemo·useCallback·memo를 쓰지 않는다(React Compiler가 맡는다) → 컴파일러가 잘못 최적화할 때만 \"use no memo\"와 이유 주석",
                no, line)
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
    out = [f"[nextts] {path}"]
    for rule_id, msg, no, line in violations:
        out.append(f"  {no}: [{rule_id}] {msg}\n      > {line}")
    root = os.environ.get("CLAUDE_PLUGIN_ROOT")
    ref = f"{root}/docs/conventions/README.md" if root else "nextts 플러그인의 docs/conventions/README.md"
    out.append(f"  근거: {ref}")
    return "\n".join(out)


def _stale_copy_warning(path: str) -> None:
    """저장소에 복사한 pre-commit 검사기가 플러그인 것과 다르면 사용자에게 알린다(막지는 않는다)."""
    d = Path(path).resolve().parent
    for cand in [d, *d.parents]:
        copy = cand / "scripts" / "conventions" / "check_next_conventions.py"
        if copy.is_file():
            if copy.read_bytes() != Path(__file__).read_bytes():
                print(json.dumps({"systemMessage": "nextts: 저장소의 scripts/conventions/check_next_conventions.py가 플러그인 검사기와 다르다. "
                                  "git pre-commit 규칙이 어긋나 있으니 /nextts:init을 다시 실행해 맞춘다."}, ensure_ascii=False))
            return
        if (cand / ".git").exists():
            return


def run_hook() -> int:
    payload = json.load(sys.stdin)
    tool = payload.get("tool_name", "")
    tool_input = payload.get("tool_input", {}) or {}
    path = tool_input.get("file_path", "")
    if not path or next_root(path) is None:
        return 0
    p = Path(path)
    before = p.read_text(encoding="utf-8") if p.exists() else ""
    after = _resulting_content(tool, tool_input, before)
    if after is None:
        return 0
    # 기존 위반은 두고, 이번 변경으로 새로 생긴 위반만 막는다. 이미 있는 JS 파일을 고치는 것은 막지 않는다
    old = Counter((r, l) for r, _, _, l in find_violations(path, before)) if p.exists() else Counter()
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
        violations = find_violations(str(p.resolve()), p.read_text(encoding="utf-8", errors="ignore"))
        if violations:
            failed = True
            print(_format(path, violations), file=sys.stderr)
    return 1 if failed else 0


def _tsc_command(root: Path) -> list[str]:
    if (root / "pnpm-lock.yaml").exists():
        return ["pnpm", "exec", "tsc", "--noEmit"]
    if (root / "yarn.lock").exists():
        return ["yarn", "tsc", "--noEmit"]
    if (root / "bun.lock").exists() or (root / "bun.lockb").exists():
        return ["bun", "x", "tsc", "--noEmit"]
    return ["npx", "--no-install", "tsc", "--noEmit"]


def run_typecheck(paths: list[str]) -> int:
    """next dev는 타입 검사를 하지 않으므로 커밋 전에 프로젝트 단위로 tsc --noEmit을 돌린다."""
    roots = {next_root(str(Path(p).resolve())) for p in paths if p.endswith(TS_EXT)} - {None}
    failed = False
    for root in sorted(roots):
        cmd = _tsc_command(root)
        try:
            result = subprocess.run(cmd, cwd=root)
        except FileNotFoundError:
            print(f"[nextts] {root}: {cmd[0]}을 찾을 수 없어 타입 검사를 못 했다", file=sys.stderr)
            return 1
        if result.returncode != 0:
            print(f"[nextts] {root}: {' '.join(cmd)} 실패", file=sys.stderr)
            failed = True
    return 1 if failed else 0


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--files":
        sys.exit(run_files(sys.argv[2:]))
    if len(sys.argv) > 1 and sys.argv[1] == "--typecheck":
        sys.exit(run_typecheck(sys.argv[2:]))
    sys.exit(run_hook())

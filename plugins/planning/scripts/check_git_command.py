#!/usr/bin/env python3
"""planning: Claude가 실행하려는 git 명령을 검사한다 (PreToolUse, Bash).

기획 설정(CLAUDE.md `## 기획 설정`)이 있는 저장소에서만 동작한다.
막으면 exit 2와 stderr로 이유를 알린다. 판단할 수 없으면 통과시킨다.

검사
- git-add-all     : `git add -A`, `git add --all`, `git add .` 금지 (관련 파일만 이름으로)
- commit-prefix   : 커밋 메시지 첫 줄에 접두어 (docs|feat|fix|refactor|test|chore):
- commit-refs     : 기획·코드 브랜치(기본 브랜치가 아닌 곳)의 커밋에 `Refs:` trailer
- code-branch-docs: 기획 브랜치(plan/…)가 아닌 작업 브랜치에서 기획 폴더 수정 금지
- banned-word     : 기획 폴더에 새로 쓰는 줄에 기획 설정 "금지어"가 있으면 금지
- dev-*           : 기획 설정에 "개발 브랜치"(예: dev)가 있을 때만. 코드는 개발 브랜치에서 분기한 작업 브랜치에서 하고 개발 브랜치로 PR 한다
  - dev-branch-from : 기본 브랜치에서 코드 브랜치(plan/ 아님)를 만들지 않는다
  - dev-code-commit : 기본·개발 브랜치에 바로 코드 커밋(feat|fix|refactor|test)을 하지 않는다
  - dev-pr-base     : 코드 브랜치의 PR base는 개발 브랜치
"""
import json
import re
import shlex
import subprocess
import sys
from pathlib import Path

PREFIX = re.compile(r"(?:^|[\"'])\s*(docs|feat|fix|refactor|test|chore)(\([^)]+\))?!?: \S", re.M)


def git(cwd, *args):
    r = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else ""


def settings(root):
    claude = Path(root) / "CLAUDE.md"
    if not claude.exists():
        return None
    text = claude.read_text(encoding="utf-8")
    m = re.search(r"^## 기획 설정\s*$(.*?)(?=^## |\Z)", text, re.M | re.S)
    if not m:
        return None
    body = m.group(1)

    def value(key, default):
        v = re.search(rf"^- {key}:\s*(.+)$", body, re.M)
        return v.group(1).strip() if v else default

    folder = value("기획 폴더", "docs/planning").split()[0].strip("`").rstrip("/")
    base = value("기본 브랜치", "main").split()[0].strip("`")
    words = value("금지어", "")
    banned = [w.strip().strip("`\"") for w in re.split(r"[,、]", words) if w.strip() and words != "없음"]
    dev = (value("개발 브랜치", "").split() or [""])[0].strip("`")
    dev = "" if dev == "없음" else dev
    return {"folder": folder, "base": base, "banned": banned, "dev": dev}


def block(rule, msg):
    print(f"[planning:{rule}] {msg}", file=sys.stderr)
    sys.exit(2)


def segments(command):
    """`&&`, `;`, `|`, 줄바꿈으로 나눈 명령 조각. heredoc 본문은 commit 조각에 남긴다."""
    return re.split(r"&&|\|\||;|\n(?=\s*git\s)", command)


def add_paths(command):
    paths = []
    for seg in segments(command):
        m = re.search(r"\bgit\s+add\b(.*)", seg)
        if not m:
            continue
        try:
            toks = shlex.split(m.group(1))
        except ValueError:
            toks = m.group(1).split()
        for t in toks:
            if t in ("-A", "--all", "."):
                block("git-add-all", "`git add -A`/`git add .` 대신 관련 파일만 이름으로 add 한다 (planning commit 규칙 3).")
            if not t.startswith("-"):
                paths.append(t.rstrip("/"))
    return paths


def changed_files(root, paths, commit_all):
    staged = set(git(root, "diff", "--cached", "--name-only").split())
    if commit_all:
        staged |= set(git(root, "diff", "--name-only").split())
    if paths:
        pending = set(git(root, "diff", "--name-only").split()) | set(
            git(root, "ls-files", "--others", "--exclude-standard").split())
        for f in pending:
            if any(f == p or f.startswith(p + "/") or (p.endswith("*") and f.startswith(p[:-1])) for p in paths):
                staged.add(f)
    return staged


def added_lines(root, f):
    if not git(root, "ls-files", "--", f).strip():
        p = Path(root) / f
        return p.read_text(encoding="utf-8", errors="ignore").splitlines() if p.is_file() else []
    diff = git(root, "diff", "HEAD", "-U0", "--", f)
    return [l[1:] for l in diff.splitlines() if l.startswith("+") and not l.startswith("+++")]


def check_dev_flow(root, conf, command, branch):
    """개발 브랜치 규칙: 코드 브랜치는 개발 브랜치에서 만들고 개발 브랜치로 PR 한다."""
    dev, base = conf["dev"], conf["base"]
    for seg in segments(command):
        m = re.search(r"\bgit\s+(?:switch\s+(?:-c|--create|-C)|checkout\s+-[bB])\s+(\S+)(?:\s+(\S+))?", seg)
        if m and not m.group(1).startswith("plan/"):
            start = m.group(2)
            if (start is None and branch == base) or start in (base, f"origin/{base}"):
                block("dev-branch-from", f"코드 브랜치 `{m.group(1)}`는 `{dev}`에서 만든다: `git switch -c {m.group(1)} {dev}` (기획 설정 \"개발 브랜치\").")
        pr = re.search(r"\bgh\s+pr\s+create\b(.*)", seg, re.S)
        if pr and branch and not branch.startswith("plan/") and branch not in (base, dev):
            target = re.search(r"(?:--base|-B)[=\s]+(\S+)", pr.group(1))
            if not target or target.group(1).strip("'\"") != dev:
                block("dev-pr-base", f"코드 브랜치 `{branch}`의 PR은 `{dev}`로 보낸다: `gh pr create --base {dev} …` (기획 설정 \"개발 브랜치\").")


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        return
    command = (data.get("tool_input") or {}).get("command") or ""
    is_dev_cmd = re.search(r"\bgit\s+(?:switch|checkout)\b|\bgh\s+pr\s+create\b", command)
    if not re.search(r"\bgit\s+(add|commit)\b", command) and not is_dev_cmd:
        return
    cwd = data.get("cwd") or "."
    m = re.match(r"\s*cd\s+(\S+)\s*&&", command)
    if m:
        cwd = str(Path(cwd, Path(m.group(1)).expanduser()))
    root = git(cwd, "rev-parse", "--show-toplevel").strip()
    if not root:
        return
    conf = settings(root)
    if not conf:
        return
    if conf["dev"] and is_dev_cmd:
        check_dev_flow(root, conf, command, git(root, "branch", "--show-current").strip())

    paths = add_paths(command)
    commit = re.search(r"\bgit\s+commit\b(.*)", command, re.S)
    if not commit:
        return
    args = commit.group(1)
    branch = git(root, "branch", "--show-current").strip()

    # 메시지는 -m/-F(heredoc) 로 주어질 때만 검사한다. 편집기·--amend --no-edit 는 건너뛴다.
    has_msg = re.search(r"(^|\s)(-m|--message|-F|--file)\b|-[a-z]*m\b", args)
    if has_msg and "--no-edit" not in args:
        if not PREFIX.search(args):
            block("commit-prefix", "커밋 메시지 첫 줄은 `docs:`, `feat:`, `fix:`, `refactor:`, `test:`, `chore:` 중 하나로 시작한다.")
        if conf["dev"] and branch in (conf["base"], conf["dev"]) and re.search(r"(?:^|[\"'])\s*(feat|fix|refactor|test)(\([^)]+\))?!?: ", args, re.M):
            block("dev-code-commit", f"`{branch}`에 바로 코드 커밋을 하지 않는다. `{conf['dev']}`에서 작업 브랜치를 만들어 커밋하고 `{conf['dev']}`로 PR 한다 (기획 설정 \"개발 브랜치\").")
        if branch and branch not in (conf["base"], conf["dev"]) and not re.search(r"^\s*Refs:\s*\S", args, re.M):
            block("commit-refs", f"`{branch}` 브랜치의 커밋 본문 끝에 `Refs: #<이슈>`(이슈가 없으면 `Refs: <백로그 ID>`)를 넣는다.")

    commit_all = bool(re.search(r"(^|\s)(-a|--all|-[a-z]*a[a-z]*)\b", args.split("-m")[0]))
    files = changed_files(root, paths, commit_all)
    planning = [f for f in files if f == conf["folder"] or f.startswith(conf["folder"] + "/")]

    if planning and branch and branch != conf["base"] and not branch.startswith("plan/"):
        block("code-branch-docs", f"`{branch}`는 기획 브랜치가 아니다. `{conf['folder']}/` 수정은 plan/<ID>-<slug> 브랜치에서 한다: {', '.join(sorted(planning))}")

    for f in planning:
        for line in added_lines(root, f):
            for w in conf["banned"]:
                # 금지어 자체를 인용하는 줄("단계"라는 말은 …)은 허용한다.
                if w in line and not re.search(rf"[\"'`“‘]{re.escape(w)}[\"'`”’]", line):
                    block("banned-word", f"{f}: 금지어 `{w}`가 있다 (기획 설정 \"금지어\"). 줄: {line.strip()[:80]}")


if __name__ == "__main__":
    main()

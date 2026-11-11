"""Checks the rules in docs/rules.md. Used by CI, and can be run locally.

Usage:
    python .github/scripts/check_rules.py branch <branch-name>
    python .github/scripts/check_rules.py commits <base-sha> <head-sha>
    python .github/scripts/check_rules.py files
    python .github/scripts/check_rules.py links
"""

import os
import re
import subprocess
import sys
from urllib.parse import unquote

TYPES_BRANCH = "feature|fix|exp|docs|chore|refactor"
TYPES_COMMIT = "feat|fix|exp|docs|chore|refactor"
NAMES = "hung|tuan|anh"

BRANCH_RE = re.compile(rf"^({TYPES_BRANCH})/({NAMES})-[a-z0-9]+(-[a-z0-9]+)*$")
COMMIT_RE = re.compile(rf"^({TYPES_COMMIT})(\([a-z0-9-]+\))?: \S")
COMMIT_SKIP_RE = re.compile(r'^(Merge |Revert ")')

FORBIDDEN_DIRS = ("data/", "models/", "indexes/")
FORBIDDEN_EXTS = (".faiss", ".index", ".npy", ".pt", ".bin", ".safetensors", ".pkl")
MAX_FILE_MB = 20

SECRET_PATTERNS = {
    "Gemini/Google API key": re.compile(r"AIza[0-9A-Za-z_\-]{35}"),
    "Groq API key": re.compile(r"gsk_[0-9A-Za-z]{20,}"),
    "Hugging Face token": re.compile(r"hf_[0-9A-Za-z]{30,}"),
    "OpenAI-style key": re.compile(r"sk-[0-9A-Za-z_\-]{20,}"),
}

LINK_RE = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
FENCE_RE = re.compile(r"```.*?```", re.S)


def git(*args):
    out = subprocess.run(["git", *args], capture_output=True, text=True, encoding="utf-8", check=True)
    return out.stdout


def repo_files():
    """Tracked files plus new files that are not ignored."""
    out = git("ls-files", "--cached", "--others", "--exclude-standard")
    return [f for f in out.splitlines() if f and os.path.exists(f)]


def fail(errors, title):
    if errors:
        print(f"FAILED: {title}")
        for e in errors:
            print(f"  - {e}")
        print("See docs/rules.md for the rules.")
        sys.exit(1)
    print(f"OK: {title}")


def check_branch(name):
    errors = []
    if not BRANCH_RE.match(name):
        errors.append(
            f"'{name}' should look like {{type}}/{{name}}-{{task}}, "
            f"for example feature/hung-dense-bge. Types: {TYPES_BRANCH.replace('|', ', ')}. "
            f"Names: {NAMES.replace('|', ', ')}."
        )
    fail(errors, "branch name")


def check_commits(base, head):
    errors = []
    for line in git("log", "--format=%h %s", f"{base}..{head}").splitlines():
        sha, _, subject = line.partition(" ")
        if COMMIT_SKIP_RE.match(subject):
            continue
        if not COMMIT_RE.match(subject):
            errors.append(f"{sha} '{subject}' should look like 'feat: add BM25 with Pyserini'")
    fail(errors, "commit messages")


def check_files():
    errors = []
    for f in repo_files():
        low = f.lower()
        name = os.path.basename(low)
        if low.startswith(FORBIDDEN_DIRS):
            errors.append(f"{f}: data, models and indexes must not be pushed")
        if name == ".env" or (name.startswith(".env.") and name != ".env.example"):
            errors.append(f"{f}: .env files hold secrets and must not be pushed")
        if low.endswith(FORBIDDEN_EXTS):
            errors.append(f"{f}: model or index file must not be pushed")
        size_mb = os.path.getsize(f) / 1e6
        if size_mb > MAX_FILE_MB:
            errors.append(f"{f}: {size_mb:.1f} MB is larger than {MAX_FILE_MB} MB")
        try:
            with open(f, encoding="utf-8") as fh:
                text = fh.read()
        except (UnicodeDecodeError, OSError):
            continue  # binary file, skip the secret scan
        for label, pattern in SECRET_PATTERNS.items():
            if pattern.search(text):
                errors.append(f"{f}: looks like it contains a {label}")
        if name == ".env.example":
            for i, line in enumerate(text.splitlines(), 1):
                line = line.strip()
                if line and not line.startswith("#") and "=" in line and line.split("=", 1)[1].strip():
                    errors.append(f"{f}:{i}: .env.example must have empty values, no real keys")
    fail(errors, "no data, models, large files or API keys")


def check_links():
    errors = []
    for f in repo_files():
        if not f.lower().endswith(".md"):
            continue
        with open(f, encoding="utf-8") as fh:
            text = FENCE_RE.sub("", fh.read())
        for target in LINK_RE.findall(text):
            if re.match(r"^(https?:|mailto:|#)", target):
                continue
            path = unquote(target.split("#", 1)[0])
            full = os.path.normpath(os.path.join(os.path.dirname(f), path))
            if not os.path.exists(full):
                errors.append(f"{f}: broken link '{target}'")
    fail(errors, "links in Markdown docs")


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "branch" and len(sys.argv) == 3:
        check_branch(sys.argv[2])
    elif cmd == "commits" and len(sys.argv) == 4:
        check_commits(sys.argv[2], sys.argv[3])
    elif cmd == "files":
        check_files()
    elif cmd == "links":
        check_links()
    else:
        print(__doc__)
        sys.exit(2)


if __name__ == "__main__":
    main()

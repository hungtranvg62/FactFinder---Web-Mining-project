# GitHub Rules

These rules keep `main` working and stop us from breaking each other's code. Read them once before your first commit.

## 1. Never commit to `main`

- `main` must always run.
- All work happens on a branch. Changes reach `main` only through a Pull Request (PR).

## 2. Branches

One branch per task. Name it `{type}/{name}-{task}`, using lowercase and dashes.

| Type | Use it for | Example |
| --- | --- | --- |
| `feature/` | A new method, script or app feature | `feature/hung-dense-bge` |
| `fix/` | A bug fix | `fix/anh-rrf-ties` |
| `exp/` | An experiment or tuning run | `exp/tuan-bm25-k1-b` |
| `docs/` | The README, `docs/` or report notes | `docs/hung-team-rules` |
| `chore/` | Setup, `requirements.txt`, `.gitignore`, cleanup | `chore/tuan-pyserini-setup` |
| `refactor/` | Cleaner code that gives the same results | `refactor/anh-rerank-args` |

Names: `hung`, `tuan`, `anh`.

```bash
git checkout main
git pull                          # always start from the newest main
git checkout -b feature/hung-dense-bge
```

## 3. Commits

Write commit messages as `type: short text`, in English, in the present tense.

| Type | Example |
| --- | --- |
| `feat` | `feat: add BM25 with Pyserini` |
| `fix` | `fix: handle claims with no qrels` |
| `exp` | `exp: tune k1 and b on dev` |
| `docs` | `docs: add GitHub rules` |
| `chore` | `chore: add faiss-cpu to requirements` |
| `refactor` | `refactor: split rerank into load and score` |

- Make small commits, one idea each.
- Run your code before you commit. Do not commit code that crashes.

## 4. Pull Requests

1. Push your branch: `git push -u origin <branch-name>`.
2. Open a PR into `main`. In the description, say what changed and how you tested it (for example, the dev NDCG@10).
3. Get **Hung's approval**. GitHub adds him as reviewer automatically (`.github/CODEOWNERS`), and the PR cannot be merged before he approves. Changes to `src/common/` need **all 3 members** to agree.
4. Merge, then delete the branch on GitHub and on your machine:

```bash
git checkout main
git pull
git branch -d feature/hung-dense-bge
```

If `main` changed while you were working, update your branch before merging:

```bash
git checkout main && git pull
git checkout feature/hung-dense-bge
git merge main                    # fix any conflicts, then commit
```

## 5. Who owns what

Only edit your own folder. If you need a change in someone else's folder, ask them or open an issue.

| Folder | Owner | GitHub |
| --- | --- | --- |
| `src/common/` | Hung (frozen after week 1, day 4) | `hungtranvg62` |
| `src/neural/` | Hung | `hungtranvg62` |
| `src/lexical/` | Tuan | `labrynth205-ship-it` |
| `src/fusion_rerank/`, `src/rag/`, `app/` | Hoai Anh | `rach-1873` |

Shared files (`requirements.txt`, `README.md`, `docs/`): pull `main` first, keep each change small, and merge it quickly.

## 6. Never push these

- `data/`: everyone makes it with `python src/common/data.py`.
- Models, indexes and embeddings (`*.faiss`, `*.npy`, `*.pt`, ...).
- API keys. Put them in `.env`, which is ignored. Only `.env.example` (no real keys) is pushed.

Run files (`runs/`) and results (`results/`) **are** pushed, because they are how we share our work.

If you push a key by mistake, tell the team and **revoke the key right away**. Deleting the commit is not enough.

## 7. CI checks

GitHub Actions (`.github/workflows/ci.yml`) checks these rules on every PR and every push to `main`. A PR with a red check must be fixed before it is merged.

| Check | What it tests |
| --- | --- |
| Branch name | `{type}/{name}-{task}` (PRs only) |
| Commit messages | `type: short text` (PRs only, merge commits are skipped) |
| Files | No `data/`, models, indexes, `.env`, API keys, or files over 20 MB. `.env.example` has empty values. |
| Links | Every relative link in a `.md` file points to a file that exists |
| Python | All files in `src/` and `app/` compile |

Run the same checks on your machine before you push:

```bash
python .github/scripts/check_rules.py branch "$(git branch --show-current)"
python .github/scripts/check_rules.py commits main HEAD
python .github/scripts/check_rules.py files
python .github/scripts/check_rules.py links
```

## 8. Other rules

- Every method writes run files in the TREC format, to `runs/{split}/{method}.trec` (see section 7 of the team plan).
- Each method writes its own results file in `results/`. Nobody edits a shared results table by hand.
- Add every new library to `requirements.txt` in the same PR.
- Tune on dev only. Run test once, at the end.

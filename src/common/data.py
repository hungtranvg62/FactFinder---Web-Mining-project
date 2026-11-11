"""Download BEIR SciFact, check it, and make the train / dev / test splits.

Run once, from the repo root:

    python src/common/data.py

Then load the data in your own code (run your script with `python -m`, for
example `python -m src.lexical.bm25`, so that `src` can be imported):

    from src.common.data import load_corpus, load_queries, load_qrels, load_labels, doc_text

    corpus  = load_corpus()          # {doc_id: {"title": ..., "text": ...}}
    queries = load_queries("dev")    # {claim_id: claim text}
    qrels   = load_qrels("dev")      # {claim_id: {doc_id: 1}}
    labels  = load_labels("dev")     # {claim_id: {"label": ..., "evidence": {...}}}
    text    = doc_text(corpus["4983"])   # title + " " + abstract

Splits
    train  709 claims   BEIR train minus dev (only for optional fine-tuning)
    dev    100 claims   taken from BEIR train, stratified by label, seed 42 (all tuning)
    test   300 claims   BEIR test, 339 claim-abstract pairs (final results only)
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
import shutil
import sys
import urllib.request
import zipfile
from pathlib import Path

URL = "https://public.ukp.informatik.tu-darmstadt.de/thakur/BEIR/datasets/scifact.zip"
MD5 = "5f7d1de60b170fc8027bb7898e2efca1"
SEED = 42
DEV_SIZE = 100
SPLITS = ("train", "dev", "test")

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
ZIP_PATH = RAW_DIR / "scifact.zip"
SCIFACT_DIR = RAW_DIR / "scifact"
SPLIT_DIR = DATA_DIR / "splits"

# Claim labels. SUPPORT and CONTRADICT come from the original SciFact release.
SUPPORT, CONTRADICT, NEI = "SUPPORT", "CONTRADICT", "NOT_ENOUGH_INFO"

# Published sizes. data.py stops if the files do not match them.
EXPECTED = {
    "corpus": 5183,
    "beir_train_claims": 809,
    "beir_train_pairs": 919,
    "test_claims": 300,
    "test_pairs": 339,
    "dev_claims": DEV_SIZE,
    "train_claims": 809 - DEV_SIZE,
}


# ---------------------------------------------------------------- download

def _md5(path: Path) -> str:
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def download(force: bool = False) -> None:
    """Download scifact.zip (if needed), check its MD5 and extract it."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    if force or not ZIP_PATH.exists() or _md5(ZIP_PATH) != MD5:
        print(f"Downloading {URL} ...")
        part = ZIP_PATH.with_suffix(".part")
        urllib.request.urlretrieve(URL, part)
        part.replace(ZIP_PATH)

    got = _md5(ZIP_PATH)
    if got != MD5:
        sys.exit(f"MD5 does not match: got {got}, expected {MD5}.\n"
                 f"Delete {ZIP_PATH} and run again.")
    print(f"MD5 OK: {MD5}")

    if force and SCIFACT_DIR.exists():
        shutil.rmtree(SCIFACT_DIR)
    if not (SCIFACT_DIR / "corpus.jsonl").exists():
        with zipfile.ZipFile(ZIP_PATH) as z:
            z.extractall(RAW_DIR)
        print(f"Extracted to {SCIFACT_DIR.relative_to(ROOT)}")


# ---------------------------------------------------------------- raw files

def _need(path: Path) -> Path:
    if not path.exists():
        raise FileNotFoundError(f"{path} not found. Run `python src/common/data.py` first.")
    return path


def _read_jsonl(path: Path) -> list[dict]:
    with open(_need(path), encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def _read_beir_qrels(name: str) -> dict[str, dict[str, int]]:
    """Read data/raw/scifact/qrels/{name}.tsv -> {claim_id: {doc_id: score}}."""
    qrels: dict[str, dict[str, int]] = {}
    with open(_need(SCIFACT_DIR / "qrels" / f"{name}.tsv"), encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f, delimiter="\t"):
            qrels.setdefault(row["query-id"], {})[row["corpus-id"]] = int(row["score"])
    return qrels


def _raw_queries() -> dict[str, dict]:
    return {q["_id"]: q for q in _read_jsonl(SCIFACT_DIR / "queries.jsonl")}


def _claim_label(metadata: dict) -> str:
    """SUPPORT, CONTRADICT, or NOT_ENOUGH_INFO when no abstract has evidence."""
    labels = {r["label"] for rationales in metadata.values() for r in rationales}
    if not labels:
        return NEI
    if len(labels) > 1:
        raise ValueError(f"Claim has mixed labels {labels}; this should not happen in SciFact.")
    return labels.pop()


def _numeric_sort(ids) -> list[str]:
    return sorted(ids, key=int)


# ---------------------------------------------------------------- splits

def _quotas(sizes: dict[str, int], total: int) -> dict[str, int]:
    """Share `total` between groups in proportion to their sizes (largest remainder)."""
    n = sum(sizes.values())
    exact = {k: total * s / n for k, s in sizes.items()}
    quota = {k: int(v) for k, v in exact.items()}
    left = total - sum(quota.values())
    for k in sorted(exact, key=lambda k: (-(exact[k] - quota[k]), k))[:left]:
        quota[k] += 1
    return quota


def make_splits() -> dict:
    """Make the dev split from BEIR train (stratified by label) and save the ID lists."""
    queries = _raw_queries()
    beir_train = _read_beir_qrels("train")
    beir_test = _read_beir_qrels("test")

    overlap = set(beir_train) & set(beir_test)
    if overlap:
        sys.exit(f"{len(overlap)} claims are in both BEIR train and test.")

    # Group the BEIR train claims by label, then take the same share of each group,
    # so dev has the same SUPPORT / CONTRADICT / NEI mix as train.
    groups: dict[str, list[str]] = {}
    for qid in _numeric_sort(beir_train):
        groups.setdefault(_claim_label(queries[qid]["metadata"]), []).append(qid)

    rng = random.Random(SEED)
    quota = _quotas({k: len(v) for k, v in groups.items()}, DEV_SIZE)
    dev: list[str] = []
    for label in sorted(groups):
        ids = list(groups[label])
        rng.shuffle(ids)
        dev += ids[: quota[label]]

    dev_set = set(dev)
    ids = {
        "train": [q for q in _numeric_sort(beir_train) if q not in dev_set],
        "dev": _numeric_sort(dev),
        "test": _numeric_sort(beir_test),
    }

    SPLIT_DIR.mkdir(parents=True, exist_ok=True)
    for split, split_ids in ids.items():
        (SPLIT_DIR / f"{split}_ids.txt").write_text("\n".join(split_ids) + "\n", encoding="utf-8")

    info = {
        "source": URL,
        "md5": MD5,
        "seed": SEED,
        "dev_fingerprint": fingerprint(ids["dev"]),
        "splits": {
            split: {
                "claims": len(split_ids),
                "labels": {lab: sum(_claim_label(queries[q]["metadata"]) == lab for q in split_ids)
                           for lab in (SUPPORT, CONTRADICT, NEI)},
            }
            for split, split_ids in ids.items()
        },
    }
    (SPLIT_DIR / "split_info.json").write_text(json.dumps(info, indent=2), encoding="utf-8")
    return info


def fingerprint(ids: list[str]) -> str:
    """Short hash of an ID list. Everyone's dev fingerprint must be the same."""
    return hashlib.md5("\n".join(_numeric_sort(ids)).encode()).hexdigest()[:8]


# ---------------------------------------------------------------- public loaders

def load_ids(split: str) -> list[str]:
    """Claim IDs of a split: 'train', 'dev' or 'test'."""
    if split not in SPLITS:
        raise ValueError(f"split must be one of {SPLITS}, got {split!r}")
    text = _need(SPLIT_DIR / f"{split}_ids.txt").read_text(encoding="utf-8")
    return text.split()


def load_corpus() -> dict[str, dict[str, str]]:
    """All 5,183 abstracts: {doc_id: {"title": ..., "text": ...}}."""
    return {d["_id"]: {"title": d["title"], "text": d["text"]}
            for d in _read_jsonl(SCIFACT_DIR / "corpus.jsonl")}


def doc_text(doc: dict[str, str]) -> str:
    """The text every method should index: title + " " + abstract."""
    return f"{doc['title']} {doc['text']}".strip()


def load_queries(split: str) -> dict[str, str]:
    """Claims of a split: {claim_id: claim text}."""
    queries = _raw_queries()
    return {qid: queries[qid]["text"] for qid in load_ids(split)}


def load_qrels(split: str) -> dict[str, dict[str, int]]:
    """Correct abstracts of a split: {claim_id: {doc_id: 1}}. Works with ranx.Qrels.from_dict."""
    beir = _read_beir_qrels("test" if split == "test" else "train")
    return {qid: dict(beir[qid]) for qid in load_ids(split)}


def load_labels(split: str) -> dict[str, dict]:
    """Claim labels for RAG: {claim_id: {"label": SUPPORT | CONTRADICT | NOT_ENOUGH_INFO,
    "evidence": {doc_id: [{"sentences": [...], "label": ...}]}}}."""
    queries = _raw_queries()
    return {qid: {"label": _claim_label(queries[qid]["metadata"]),
                  "evidence": queries[qid]["metadata"]}
            for qid in load_ids(split)}


# ---------------------------------------------------------------- checks

def check() -> None:
    """Stop with a clear message if any size differs from the published numbers."""
    corpus = load_corpus()
    beir_train = _read_beir_qrels("train")
    test_qrels = load_qrels("test")
    found = {
        "corpus": len(corpus),
        "beir_train_claims": len(beir_train),
        "beir_train_pairs": sum(len(d) for d in beir_train.values()),
        "test_claims": len(test_qrels),
        "test_pairs": sum(len(d) for d in test_qrels.values()),
        "dev_claims": len(load_ids("dev")),
        "train_claims": len(load_ids("train")),
    }
    wrong = {k: (found[k], EXPECTED[k]) for k in EXPECTED if found[k] != EXPECTED[k]}
    if wrong:
        sys.exit("Sizes do not match:\n" + "\n".join(
            f"  {k}: got {got}, expected {exp}" for k, (got, exp) in wrong.items()))

    ids = {s: set(load_ids(s)) for s in SPLITS}
    if ids["train"] & ids["dev"] or ids["train"] & ids["test"] or ids["dev"] & ids["test"]:
        sys.exit("Splits overlap.")
    for split in SPLITS:
        for docs in load_qrels(split).values():
            if any(d not in corpus for d in docs):
                sys.exit(f"A {split} qrel points to an abstract that is not in the corpus.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Download SciFact and make the splits.")
    parser.add_argument("--force", action="store_true", help="download and extract again")
    args = parser.parse_args()

    download(force=args.force)
    info = make_splits()
    check()

    print("All sizes match the published numbers.\n")
    print(f"{'split':<6} {'claims':>6} {'SUPPORT':>8} {'CONTRADICT':>11} {'NEI':>5}")
    for split in SPLITS:
        s = info["splits"][split]
        lab = s["labels"]
        print(f"{split:<6} {s['claims']:>6} {lab[SUPPORT]:>8} {lab[CONTRADICT]:>11} {lab[NEI]:>5}")
    print(f"\nDev fingerprint: {info['dev_fingerprint']}  (must be the same for all 3 members)")
    print(f"Saved ID lists to {SPLIT_DIR.relative_to(ROOT)}/")


if __name__ == "__main__":
    main()

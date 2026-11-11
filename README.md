# FactFinder

Classical vs. neural retrieval for scientific claim verification on BEIR SciFact (IT4868E Web Mining).

## Read first

| File | What it is |
| --- | --- |
| [docs/FactFinder Team Plan v2.md](docs/FactFinder%20Team%20Plan%20v2.md) | The full plan: methods, roles, dataset, evaluation, timeline |
| [docs/rules.md](docs/rules.md) | GitHub rules: branches, commits, Pull Requests, what never to push |
| [.env.example](.env.example) | Template for your API keys. Copy it to `.env`. |

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env              # then add your API keys
python src/common/data.py         # downloads SciFact into data/ (run once)
```

## Layout

```
docs/                team plan and GitHub rules
data/raw/  data/processed/   not pushed, made by data.py
runs/dev/  runs/test/  runs/train/   run files (TREC format)
src/common/          Hung: data.py, preprocess.py, evaluate.py (frozen)
src/neural/          Hung: dense_bge.py, medcpt.py, splade.py
src/lexical/         Tuan: tfidf.py, bm25.py, rm3.py, lsi.py
src/fusion_rerank/   Hoai Anh: rrf.py, rerank.py
src/rag/             Hoai Anh
app/app.py           Hoai Anh, Gradio
notebooks/  results/  report/
```

## Dataset

BEIR v1.0.0 SciFact: 5,183 abstracts, 809 train claims, 300 test claims.
`data.py` downloads it and checks the MD5 (`5f7d1de60b170fc8027bb7898e2efca1`).

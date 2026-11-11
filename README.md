# FactFinder

Classical vs. neural retrieval for scientific claim verification on BEIR SciFact (IT4868E Web Mining).

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env              # then add your API keys
python src/common/data.py         # downloads SciFact into data/ (run once)
```

## Layout

```
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

See `FactFinder Team Plan v2.md` for the full plan and team rules.

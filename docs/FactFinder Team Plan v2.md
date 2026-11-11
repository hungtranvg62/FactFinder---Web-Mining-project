# FactFinder: Team Plan v2

Nov 11, 2026 · @Hung

## 1. Project at a glance

FactFinder compares classical and neural search methods for scientific claim verification. We take a scientific claim, find the research abstracts that match it, and measure which methods find them best. Then an LLM reads the top abstracts and says if the claim is true.

- **Course:** IT4868E Web Mining, group project
- **Time:** 6 weeks
- **Team:** Tran Vuong Hung (leader, GitHub `hungtranvg62`), Tran Ngoc Tuan (`labrynth205-ship-it`), Nguyen Hoai Anh (`rach-1873`)
- **Dataset:** BEIR SciFact only

**What changed from v1**

- Hung now builds the neural methods and Tuan builds the lexical methods.
- LSI moves to the lexical part, because it is built on the TF-IDF matrix.
- 9 core methods, down from 15. The others are optional.
- Hung is the starter: he downloads and preprocesses the dataset, then freezes the shared code (3 files) by day 4 of week 1.
- Only Tuan needs Java and Pyserini.
- Fine-tuning the reranker is an optional extension, and the code leaves space for it.

**Research questions**

1. How do classical methods (TF-IDF, BM25, LSI) compare with neural methods (bge, MedCPT, SPLADE) on SciFact?
2. Does relevance feedback (RM3) help BM25?
3. Does a hybrid (RRF of BM25 and dense) beat each method alone?
4. Does a cross-encoder reranker improve the top 10, and how much slower is it?
5. Does better retrieval lead to better claim verification in RAG?
6. Optional: does fine-tuning the reranker on SciFact beat the zero-shot reranker?

No model is trained in the main plan. All neural models are used pre-trained. We only tune small settings (BM25's k1 and b, LSI's k) on the dev set.

## 2. Methods

Nine core methods answer all five research questions. BM25 is the baseline for everything.

| # | Method                                     | Owner    | Stage                           | Answers       | Run name      |
| - | ------------------------------------------ | -------- | ------------------------------- | ------------- | ------------- |
| 1 | TF-IDF + cosine                            | Tuan     | First stage, lexical            | RQ1           | `tfidf`     |
| 2 | BM25 (tune k1, b)                          | Tuan     | First stage, lexical            | RQ1, baseline | `bm25`      |
| 3 | BM25 + RM3                                 | Tuan     | First stage, lexical            | RQ2           | `bm25_rm3`  |
| 4 | LSI (try several k)                        | Tuan     | First stage, classical semantic | RQ1           | `lsi`       |
| 5 | Dense: bge-base + FAISS                    | Hung     | First stage, neural             | RQ1           | `dense_bge` |
| 6 | MedCPT (biomedical dense)                  | Hung     | First stage, neural             | RQ1           | `medcpt`    |
| 7 | SPLADE (neural sparse)                     | Hung     | First stage, neural             | RQ1           | `splade`    |
| 8 | RRF of BM25 + dense                        | Hoai Anh | Second stage, fusion            | RQ3           | `rrf`       |
| 9 | Cross-encoder reranker on the BM25 top 100 | Hoai Anh | Second stage, reranking         | RQ4           | `rerank`    |

RAG claim checking (RQ5) and the Gradio app come after retrieval. Both belong to Hoai Anh.

**Optional, only if we are ahead at the end of week 4**

| Extra                               | Owner    | Why                                               |
| ----------------------------------- | -------- | ------------------------------------------------- |
| Fine-tuned reranker (`rerank_ft`) | Hung     | Answers RQ6 and adds real model training          |
| Weighted linear fusion (`linear`) | Hoai Anh | Shows how much weight BM25 and dense each deserve |
| Boolean retrieval                   | Tuan     | A short lecture example for the report            |
| UMAP map of the embeddings          | Hung     | A picture for the report                          |

**Dropped from v1:** QLD, Rocchio, CombSUM, CombMNZ and Borda. Each one repeats a question that a core method already answers.

## 3. Team roles

Each member owns one stage of the pipeline and one code folder. Hung and Tuan both build first-stage retrievers, so their results can be compared directly, but their code never touches.

| Member                   | Part                               | Tasks                                                                                                                                                     | Tools                                                   | Code folder                                    |
| ------------------------ | ---------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------- | ---------------------------------------------- |
| Tran Vuong Hung (leader) | Shared code + neural retrieval     | Starter: dataset download, preprocessing, dev split, evaluation script. Then bge-base + FAISS, MedCPT, SPLADE. In week 5: merge results, t-tests, charts. | sentence-transformers, FAISS, Hugging Face, Colab GPU   | `src/common/`, `src/neural/`               |
| Tran Ngoc Tuan           | Lexical retrieval + reference runs | Pyserini reference runs, EDA. Then TF-IDF, BM25, RM3, LSI. In week 5: error analysis by claim type.                                                       | Pyserini (Java 21), scikit-learn, nltk, CPU only        | `src/lexical/`                               |
| Nguyen Hoai Anh          | Second stage, RAG, app             | RRF, cross-encoder reranker, RAG claim check, Gradio app.                                                                                                 | ranx, sentence-transformers, Gemini or Groq API, Gradio | `src/fusion_rerank/`, `src/rag/`, `app/` |

**How the parts stay independent**

1. **Hung is the starter.** `src/common/` holds `data.py`, `preprocess.py` and `evaluate.py`. Hung writes all three and freezes them by day 4 of week 1. After that, changes need all 3 members to agree.
2. **One command gives everyone the same data.** `python src/common/data.py` downloads SciFact, checks the MD5, makes the dev split, and saves the raw and the preprocessed corpus in `data/`. Data is not pushed, so each member runs this once.
3. **Two versions of the text.** The preprocessed version (lowercase, no stopwords, stemmed) is for Tuan's TF-IDF and LSI. The raw version is for Hung's neural models and for Pyserini, which does its own tokenizing.
4. **Java is Tuan's only.** Hung runs SPLADE with the Hugging Face model directly, not through Pyserini, so he never needs Java.
5. **Different machines.** Tuan works on CPU. Hung works on a Colab GPU.
6. **Hoai Anh never waits.** In week 1 Tuan makes two reference runs with Pyserini (BM25 and the prebuilt BGE index). Hoai Anh builds fusion, reranking and RAG on these, then swaps in the final runs in week 5.
7. **One hand-off format.** Every method writes a run file in the same format (section 7). Run files are the only thing passed between members.

**The 3 points where we still meet**

- End of week 1, day 4: `src/common/` is frozen and the reference runs are pushed.
- End of week 4: all final test runs are pushed. Hung and Hoai Anh need them for week 5.
- Shared files (`requirements.txt`, `README.md`): keep each change small and pull `main` before editing.

## 4. Dataset and splits

We use BEIR SciFact: 5,183 biomedical abstracts, expert-written claims, and expert labels saying which abstracts match each claim. It is small enough for Colab and has published baselines.

| Split      | Size                          | Use                                                       |
| ---------- | ----------------------------- | --------------------------------------------------------- |
| Corpus     | 5,183 abstracts               | The collection we search in                               |
| Dev        | 100 claims taken from train   | All tuning (k1, b, LSI k, prompts)                        |
| Train rest | 709 claims                    | Not used in the main plan. Kept for optional fine-tuning. |
| Test       | 300 claims, 339 correct pairs | Final results only. Run once at the end.                  |

The train and test sizes come from the published dataset statistics. Hung checks them in week 1 when `data.py` first loads the files.

**Rules**

- SciFact has no official dev set, so `data.py` takes 100 train claims with a fixed random seed and saves their IDs.
- `data.py` also saves the IDs of the other 709 train claims. This costs nothing now and makes fine-tuning possible later.
- Never tune on test. Never train on dev or test claims.
- Most test claims have only 1 correct abstract, so P@10 can be at most about 0.1. This is normal.
- Abstracts not listed in the qrels count as wrong.

## 5. Evaluation

BM25 is the baseline, and NDCG@10 on the 300 test claims is the main score. If our BM25 lands between 0.665 and 0.68, our setup matches published work.

**What each method is compared against**

| Method                           | Compared against                                            | Question                                       |
| -------------------------------- | ----------------------------------------------------------- | ---------------------------------------------- |
| TF-IDF, LSI, bge, MedCPT, SPLADE | BM25                                                        | Is it better than the standard baseline?       |
| BM25 + RM3                       | BM25                                                        | Does feedback help the same method?            |
| RRF                              | BM25 and bge, its two inputs                                | Does fusion beat both parts?                   |
| Reranker                         | The BM25 top 100 it reranks                                 | How much does the second stage add?            |
| RAG                              | No retrieval (lower bound) and gold abstracts (upper bound) | Where does each retriever sit between the two? |

**Metrics** (all computed by `src/common/evaluate.py`, using `ranx`)

| Metric                     | What it tells us                                                                   |
| -------------------------- | ---------------------------------------------------------------------------------- |
| NDCG@10 (main)             | How high the correct abstracts are in the top 10                                   |
| Recall@100                 | Whether the correct abstract is in the top 100 at all. Important before reranking. |
| MRR@10                     | How early the first correct abstract appears                                       |
| MAP and P@10               | The lecture metrics, reported for completeness                                     |
| Time per query, index size | The cost of each method                                                            |
| Paired t-test against BM25 | Whether a difference is real or just luck                                          |

**Fair comparison rules**

- Same corpus, same 300 test claims, top 100 per claim, same run format, same evaluation script.
- Tune only on dev. Run test once at the end.
- Add a P-R curve, since it is in the lecture.
- The t-test, NDCG and MRR are not in the lecture, so the report explains each in one or two sentences.

**Expected order** (a guide, not a target): reranker, then RRF, then MedCPT and bge, then SPLADE (about 0.70), then BM25 and RM3, then TF-IDF and LSI. A worse result is still fine if we explain why.

**Error analysis.** Tuan splits the test claims into groups, for example with and without numbers or gene names, and shows which methods win in each group. This explains the strong and weak points of each family.

## 6. RAG and the Gradio app

RAG shows whether better search leads to better answers. An LLM reads the top 3 abstracts for a claim and answers SUPPORTS, REFUTES or NOT ENOUGH INFO, with the evidence sentences it used.

- **Labels:** SUPPORT / CONTRADICT from the original SciFact release.
- **Metrics:** accuracy and macro-F1.
- **Four inputs to compare:** no retrieval, BM25 top 3, best method top 3, and the gold abstracts.
- **LLM:** Gemini or Groq API, with the key kept in `.env` and never pushed.
- **Order:** test the prompt on dev first, then run test once.

**Gradio app** (`app/app.py`)

- A search box for a claim and a method picker.
- The top 5 abstracts shown side by side for each chosen method. If the claim is from the test set, the correct abstracts are highlighted.
- A "Check claim" button that runs the RAG step.
- A tab with our results charts.

The app reads run files and saved indexes, so it works in week 2 with the two reference methods. Each new method is added as one more entry in the picker when its owner pushes it. For the live demo, use biomedical, full-sentence claims, because that is what the methods were tested on.

## 7. Repo, run files and GitHub rules

Everyone uses the same run file format and repo layout, so results merge without extra work.

**Repo layout**

```
factfinder/
  docs/                 (this plan, rules.md)
  data/raw/  data/processed/   (not pushed, made by data.py)
  runs/dev/  runs/test/  runs/train/
  src/common/           (Hung, frozen: data.py, preprocess.py, evaluate.py)
  src/neural/           (Hung: dense_bge.py, medcpt.py, splade.py)
  src/lexical/          (Tuan: tfidf.py, bm25.py, rm3.py, lsi.py)
  src/fusion_rerank/    (Hoai Anh: rrf.py, rerank.py)
  src/rag/              (Hoai Anh)
  app/app.py            (Hoai Anh, Gradio)
  notebooks/  results/  report/
  requirements.txt  README.md
```

**Run file** (TREC format), top 100 per claim, saved as `runs/{split}/{method}.trec`:

```
query_id Q0 doc_id rank score method_name
1 Q0 31715818 1 14.2 bm25
```

Method names: `tfidf`, `bm25`, `bm25_rm3`, `lsi`, `dense_bge`, `medcpt`, `splade`, `rrf`, `rerank`. Reference runs: `ref_bm25`, `ref_bge`. Optional: `rerank_ft`, `linear`, `boolean`.

**Space left for fine-tuning**

- `data.py` saves the 709 training claim IDs.
- Tuan's reference BM25 run also covers the train claims (`runs/train/ref_bm25.trec`). Hard negatives come from this file.
- `rerank.py` takes the model as an argument: `python src/fusion_rerank/rerank.py test --model <name or path>`. A fine-tuned model is then only a different path.

**Branch and review rules** (full version with examples: `docs/rules.md`)

1. Never commit to `main`. `main` must always run.
2. One branch per task, named `{type}/{name}-{task}`, for example `feature/hung-dense-bge` or `fix/anh-rrf`.
3. Push, open a Pull Request, get Hung's approval (required by `.github/CODEOWNERS`), then merge and delete the branch.
4. Changes to `src/common/` need all 3 members to agree.

**Other rules**

- Commit messages: `type: short text`, for example `feat: add BM25 with Pyserini` or `exp: tune k1 and b on dev`.
- Never push data, models, indexes or API keys. Run files can be pushed.
- Each method writes its own results file in `results/`. One script builds the full table, so nobody edits a shared table by hand.
- Add every new library to `requirements.txt`.
- Weekly meeting, 15 to 20 minutes: what is done, what is next, what is blocking.
- Report: LaTeX on Overleaf, about 30 pages at most. Code: GitHub, with Colab notebooks for the GPU parts.

## 8. Timeline (6 weeks)

Week 1 freezes the shared code, week 4 ends with all final runs and the checkpoint presentation, and week 6 is the report and slides.

| Week | Hung (starter + neural)                                                                                                                                                   | Tuan (lexical)                                                                                         | Hoai Anh (second stage, RAG, app)                                |
| ---- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------- |
| 1    | Repo. Download and preprocess SciFact (`data.py`, `preprocess.py`), dev split, `evaluate.py`. Freeze `src/common/` by day 4. Test bge on a small sample in Colab. | Java + Pyserini setup. Reference runs (BM25, BGE) for dev, test and train. EDA once the data is ready. | Read papers, get the LLM API key, Gradio skeleton.               |
| 2    | Dense retrieval: bge-base + FAISS                                                                                                                                         | TF-IDF, BM25 (tune k1, b)                                                                              | RRF on the reference runs. App shows the two reference methods.  |
| 3    | MedCPT, SPLADE                                                                                                                                                            | BM25 + RM3, LSI                                                                                        | Reranker on the BM25 top 100                                     |
| 4    | Final test runs. Lead the checkpoint presentation.                                                                                                                        | Tuning, final test runs                                                                                | RAG on dev, then test                                            |
| 5    | Merge results, t-tests, charts. Optional: fine-tune the reranker.                                                                                                         | Error analysis by claim type. Optional: Boolean example.                                               | Re-run RRF and reranker on the final runs. App with all methods. |
| 6    | Report: Intro, Neural methods, Results                                                                                                                                    | Report: Related Work, Lexical methods, Discussion                                                      | Report: Fusion, Reranking, RAG, Demo, Conclusion                 |

Slides for the final presentation are made by all three in week 6.

**Hard deadlines**

- Week 1, day 4: shared code frozen, reference runs pushed.
- End of week 4: every final test run is in `runs/test/`.
- End of week 5: results table, charts and app are final.

**Deliverables:** GitHub repo with README, results table and charts, LaTeX report, slides, live Gradio app, and the checkpoint presentation.

Open question: the week numbers here count from the project start. Check them against the dates the teacher gave for the proposal, the checkpoint and the final presentation.

## 9. Week 1 checklist

**Everyone**

- [ ] Read this plan and `docs/rules.md`, and ask questions in the first meeting
- [ ] Clone the repo and install `requirements.txt`
- [ ] Skim the BEIR paper (Thakur et al., 2021) and the SciFact paper (Wadden et al., 2020)

**Hung**

- [ ] Create the `factfinder` repo with the layout from section 7, `.gitignore` and a `.env` template
- [ ] Write `data.py`: download `scifact.zip`, check the MD5, load corpus, queries and qrels
- [ ] In `data.py`: take the 100-claim dev split with a fixed seed; save the dev IDs and the 709 training IDs
- [ ] Write `preprocess.py`: lowercase, stopwords, Porter stemming; save the preprocessed corpus and claims next to the raw ones
- [ ] Check the split sizes against section 4
- [ ] Write `evaluate.py`: read a run file, print NDCG@10, Recall@100, MRR@10, MAP and P@10, and run the paired t-test
- [ ] Freeze `src/common/` by day 4 and tell the team
- [ ] Set up Colab with a GPU, embed a few hundred abstracts with bge-base, and test FAISS
- [ ] Check the model cards of bge and MedCPT: was SciFact in their training data?

**Tuan**

- [ ] Set up Java 21 and Pyserini, and save the working setup cell in `notebooks/`
- [ ] Make the Pyserini reference runs (`ref_bm25`, `ref_bge`) for dev, test and train
- [ ] Check that `ref_bm25` scores between 0.665 and 0.68 NDCG@10 on test (after `evaluate.py` lands)
- [ ] Run `data.py` once Hung pushes it, and confirm the files load
- [ ] EDA charts: abstract and claim lengths, correct abstracts per claim, word overlap between claims and abstracts

**Hoai Anh**

- [ ] Get a Gemini or Groq API key and store it in `.env`
- [ ] Build the Gradio skeleton: search box, method picker, empty results area
- [ ] Read the RRF and RAG papers
- [ ] Once the reference runs are pushed, start RRF on dev

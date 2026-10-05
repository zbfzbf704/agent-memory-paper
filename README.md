# Agent Memory Papers

Research papers by Baofeng Zhao on long-running agent memory systems. All under TMLR review; preprints on Zenodo (CC BY 4.0).

| Paper | TMLR | Preprint (concept DOI) |
|---|---|---|
| **Salience, Ranking, and Metabolism** — three conflated signals; production failure evidence (~7 months live) | #12919 in review | [10.5281/zenodo.23068930](https://doi.org/10.5281/zenodo.23068930) |
| **Stopping as a Database Property** — reason-bearing termination for long-running LLM agents | #12935 in review | [10.5281/zenodo.23144013](https://doi.org/10.5281/zenodo.23144013) |
| **Cold-Start Ranking** — architectural semantic labels predict memory use where graph methods go blind | #12955 in review | [10.5281/zenodo.23160455](https://doi.org/10.5281/zenodo.23160455) |

---

# Salience, Ranking, and Metabolism

**Three Conflated Signals in Long-Running Agent Memory Systems**

[![DOI](https://img.shields.io/badge/DOI-10.5281%2Fzenodo.23068930-blue)](https://doi.org/10.5281/zenodo.23068930)
[![License: CC BY 4.0](https://img.shields.io/badge/Paper-CC%20BY%204.0-lightgrey)](https://creativecommons.org/licenses/by/4.0/)
[![License: MIT](https://img.shields.io/badge/Code-MIT-green)](https://opensource.org/licenses/MIT)

Baofeng Zhao · Independent Researcher · baofeng@hudiege.cn

> Preprint DOI: **[10.5281/zenodo.23068930](https://doi.org/10.5281/zenodo.23068930)** · Project page: **https://www.hudiege.cn/research/**

---

## What this is

Agent memory systems routinely treat "importance" as a single signal. We argue that it is **three conflated ones** — and that the conflation is not an implementation detail but a structural category error:

| Signal | Domain | What it is | What it must *not* be |
|---|---|---|---|
| **Salience** σ | data | how much derived content converges on this item (intrinsic, structural) | decided by retrieval behavior |
| **Ranking** ρ | service | a query-time score (bounded, decaying, recomputable) | written back into the data |
| **Metabolism** μ | lifecycle | item-level cascade retirement | triggered by popularity |

The paper contributes a signal taxonomy with four invariants (I0–I3), seven design laws, and two audit tools — with production failure evidence from about **7 months** of a live conversational memory system.

## The three failures (production-measured)

| | Before | After | What it shows |
|---|---|---|---|
| Field semantics | **93×** span in one counter | **2.2×** | three semantics sharing one field (violates I3) |
| Quality metric | reported **0.999** | reads **0.101** | a *structure-blind* metric (a ratio over link types, never counting real structure) |
| Island share | **88%** → **73%** | | most load-bearing roots are "islands" invisible to any popularity metric |
| Access inequality | Gini **0.960** | | top 1% of nodes absorb 51.9% of all accesses |

## Repository layout

```
paper/
  salience_ranking_metabolism.pdf      # Paper 1 (EN, DOI version)
  salience_ranking_metabolism_zh.pdf
  db_metacognition_en.pdf / db_metacognition_zh.pdf      # Paper 2
  coldstart_ranking_en.pdf / coldstart_ranking_zh.pdf    # Paper 3
  salience_ranking_metabolism_zh.pdf   # Chinese
  figures/                             # all 7 figures (PNG, 2x)
tools/
  silence_test.md                      # The Silence Test — audit protocol
  rag_test.md                          # The RAG Test — audit protocol
  sigma_access_check.py                # σ vs. access correlation check (self-contained)
CITATION.cff                           # machine-readable citation
```

## Audit tools

The paper claims two audits anyone can run today. Their protocols are in `tools/`:

- **The Silence Test** — suspend retrieval for T days (or replay history while intercepting writes), then recompute your "importance/quality" metrics. If they don't move, you measured data; if they drift, you measured behavior.
- **The RAG Test** — fix a workload and an outcome criterion in advance; replace your "memory layer" with a good-enough search engine. If behavior is unchanged on that criterion, the layer was retrieval only.

`tools/sigma_access_check.py` measures the correlation between a salience signal and an access counter in **any** SQLite table — pointing it at your own database:

```bash
python3 tools/sigma_access_check.py --db path/to/your.db --table nodes \
    --salience-col cv_diversity --access-col recall_count
```

**Honest note from our own run:** the correlation is *not* zero (Pearson ≈ 0.24). That is a shared-structural-cause artifact, not a write path — invariant I1 constrains the **write path** (which edges compute salience), not correlation. See §5 of the paper.

## Reproducibility & data availability

- All aggregate statistics appear as anonymized distribution plots in the paper and in `paper/figures/`.
- The **raw corpus is never released**, for privacy.
- The Silence-Test protocol is a public artifact — free to reuse and cite without permission.

## Citation

```bibtex
@misc{zhao2026salience,
  title  = {Salience, Ranking, and Metabolism: Three Conflated Signals in Long-Running Agent Memory Systems},
  author = {Zhao, Baofeng},
  year   = {2026},
  doi    = {10.5281/zenodo.23068930},
  url    = {https://www.hudiege.cn/research/salience-ranking.html},
  note   = {Preprint}
}
```

## License

- **Paper text & figures**: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) — reuse with attribution.
- **Code** (`tools/`): [MIT](LICENSE).

## 中文说明

本文论证：智能体记忆把"重要性"当成一个信号，但它其实是三个被混用的信号——**浓度（σ，数据固有）、排序（ρ，查询时服务）、代谢（μ，生命周期）**。混用不是实现瑕疵，是结构性类别错误。论文用约 7 个月（自 2026-03 起）的真实生产数据记录三类故障，并给出四条不变量、七条设计法则和两个当天可执行的自查工具（见 `tools/`）。

- 预印本 DOI：[10.5281/zenodo.23068930](https://doi.org/10.5281/zenodo.23068930)
- 项目页：https://www.hudiege.cn/research/
- 论文文本 CC BY 4.0，代码 MIT。

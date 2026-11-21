# Search relevance checks

Run the same CLI queries against a checkout and inspect the ranked results. The TSV files label acceptable results by source and server name, seed-pack ID, or linked catalog ID. Each row explains its judgment. The harness only needs Python.

```sh
python benchmarks/search/evaluate.py --mode lexical --output /tmp/lexical.json
python benchmarks/search/evaluate.py --mode bm25 --output /tmp/bm25.json
python benchmarks/search/evaluate.py --cases benchmarks/search/linked.tsv --mode bm25
python benchmarks/search/evaluate.py --cases benchmarks/search/held-out.tsv --mode bm25
```

To reproduce the historical baseline, pass `--checkout` pointing to MCP directory revision `334ec8ce2d5786f0fecbb55043b79e0ef7035b08` and omit `--mode`. Use `existing.tsv` for comparisons across revisions. Use `linked.tsv` separately for resources introduced with the RAG and ANN catalogs. The historical CLI did not offer those sources.

| Existing query group | Queries | Baseline hit@3 | Lexical hit@3 | BM25 hit@3 |
| --- | ---: | ---: | ---: | ---: |
| Exact names and IDs | 3 | 3 | 3 | 3 |
| Discovery by task or technique | 10 | 2 | 2 | 8 |
| Queries with several acceptable results | 2 | 2 | 2 | 2 |

Hit@3 counts queries with at least one labeled result in the first three. Across the ten discovery queries, the mean reciprocal rank of the first labeled result within five rose from 0.200 to 0.795. The baseline returned no matches for eight of those queries. BM25 placed at least one labeled result in the first five for each discovery query. Mux ranked fifth for the streaming-errors query. Both original negative controls returned zero results in all three configurations. For the separate six linked-source queries, lexical search found a labeled result in the first three for four queries and BM25 for all six.

The original discovery set informed the choice to try stemming after a singular/plural mismatch on a facet query. The ten additional judgments in `held-out.tsv` were frozen before testing that change. They include seven positive requests and three plausible or unrelated requests unsupported by the directory.

| Held-out measure | Lexical | BM25 without stemming (development) | BM25 with stemming |
| --- | ---: | ---: | ---: |
| Positive queries with a labeled result first | 0/7 | 5/7 | 7/7 |
| Unsupported queries returning no results | 3/3 | 2/3 | 1/3 |

BM25 returned Slack for a request to recover permanently deleted messages. Stemming also returned issue trackers for a passport-renewal query. A match can point to the right product or to a shared word without satisfying the requested action.

These hand-picked cases measure performance on the listed tasks. A traffic-weighted success rate would require representative usage data and broader relevance judgments. Keep the queries and labels fixed when comparing ranking changes.

## Design skills and motion tools

Run `python benchmarks/search/evaluate.py --cases benchmarks/search/creative.tsv --mode bm25` to check seven task queries and one unsupported request. With the 24-entry design and motion catalog pinned at `fd94c7066dd7667d6975d03354ce7d737d5cf350`, BM25 ranked the labeled item first for all seven tasks, including Manim Community for animating equations in Python and Scenario Storyboards for converting a shot list into panels. Lexical mode returned zero results for all eight natural-language queries. On the unsupported request to repair corrupted video files, BM25 returned motion tools that mention video or files. The labels were selected before running either mode.

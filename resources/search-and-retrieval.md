# Search and retrieval

Start with the collection you want to search. A question about a pack in this repository, an item in your own index and a fact on the public web each need a different source.

| Goal | Tools and source | What you get |
| --- | --- | --- |
| Find a tool or task template in this directory | `mcp-dir search retrieval --scope all --limit 5 --format json` | Ranked local metadata matches with links. Server records point to the upstream project. Pack records point to the pinned guide and manifest. |
| Query documents your team has already indexed | [OpenSearch MCP](https://github.com/opensearch-project/opensearch-mcp-server-py), [Elastic Agent Builder](https://www.elastic.co/docs/explore-analyze/ai-features/agent-builder/mcp-server), [Meilisearch MCP](https://www.meilisearch.com/docs/getting_started/integrations/mcp) | Return documents or run configured queries under the cluster's permissions. Meilisearch also exposes facets. |
| Manage hosted search infrastructure | [Typesense Cloud MCP](https://typesense.org/docs/guide/typesense-cloud/mcp-server.html) | Inspect cluster metrics, manage clusters and index data. Use a collection's search API for your application's end-user queries. |
| Discover pages and retrieve their contents | [Kagi](https://github.com/kagisearch/kagimcp), [Linkup](https://docs.linkup.so/pages/integrations/mcp/mcp), [Tavily](https://github.com/tavily-ai/tavily-mcp), [Exa](https://github.com/exa-labs/exa-mcp-server) | Search the provider's web coverage and fetch selected pages. Keep the URL, retrieval time and supporting passage with each result. |
| Find records with similar meaning | [Qdrant](https://github.com/qdrant/mcp-server-qdrant), [Weaviate](https://docs.weaviate.io/weaviate/configuration/mcp-server), [vector search and ANN libraries](https://github.com/Amarel-Taylor-Scott/vector-search-ann-libs-directory) | Nearest-neighbor search over embeddings. Hybrid retrieval also uses lexical evidence, which helps when exact identifiers matter. |
| Improve the order of a candidate set | [RAG Retrievers & Rerankers Directory](https://github.com/Amarel-Taylor-Scott/rag-retrievers-rerankers-directory) | Compare first-stage retrievers and second-stage rerankers. A reranker scores the candidates it receives, so measure how often the first stage retrieves the right document. |

### Connecting to your own index

- **OpenSearch.** Set `OPENSEARCH_URL` and credentials for your cluster. The local launcher also supports `OPENSEARCH_NO_AUTH=true` for an intentionally unauthenticated cluster. [Setup guide](https://github.com/opensearch-project/opensearch-mcp-server-py/blob/main/USER_GUIDE.md)
- **Elastic.** Supply a Kibana URL and an API key for the configured space. Custom spaces use `/s/{SPACE_ID}/api/agent_builder/mcp`. Serverless also supports OAuth through the URL shown in the client's settings. Check your deployment's Agent Builder entitlement. [Connection guide](https://www.elastic.co/docs/explore-analyze/ai-features/agent-builder/mcp-server)
- **Meilisearch.** On v1.54 or later, enable the experimental `mcpRoute` feature and use a client supporting MCP version `2026-07-28`. Scope the bearer key to the intended indexes with `indexes.get`, `documents.get` and `search` for the full tool set. [Version and access requirements](https://github.com/meilisearch/documentation/blob/main/getting_started/integrations/mcp.mdx)

### Try BM25 on the actual catalog

The directory CLI ranks metadata locally. For a reproducible full-text comparison, this example builds an in-memory SQLite FTS5 index over **both servers and seed packs**. Run it from the directory checkout with a Python build that includes FTS5. Change the query to try phrases, prefixes or boolean operators. [SQLite FTS5 query and ranking reference](https://sqlite.org/fts5.html)

```python
import json
import sqlite3
import subprocess
import sys

def catalog(*args):
    return json.loads(subprocess.check_output([sys.executable, "main.py", *args], text=True))

db = sqlite3.connect(":memory:")
db.execute("CREATE VIRTUAL TABLE docs USING fts5(title, terms, kind UNINDEXED, url UNINDEXED)")
servers = catalog("export", "--format", "json")
packs = catalog("packs", "--format", "json")
db.executemany("INSERT INTO docs VALUES (?, ?, ?, ?)", [
    (s["name"], " ".join([s["description"], *s["tags"]]), "server", s["repo"] or s["homepage"])
    for s in servers
])
db.executemany("INSERT INTO docs VALUES (?, ?, ?, ?)", [
    (p["title"], p["pack_id"].replace("-", " "), "pack", p["guide_url"]) for p in packs
])
for title, kind, url in db.execute(
    "SELECT title, kind, url FROM docs WHERE docs MATCH ? "
    "ORDER BY bm25(docs, 5, 1), title, url LIMIT 5", ("retrieval OR rerank*",)
):
    print(kind, title, url, sep="\t")
```

For a Baltor or Teleion evaluation, try three types of query: a known pack ID, a capability expressed in other words, and a question with no relevant record. Label expected results before the trial. Compare top-five recall, first relevant rank, latency and erroneous matches against a lexical baseline using the same corpus revision. The [evaluation design](ta-amps.md) and [full pack index](ta-amps-seedpacks.csv) provide starting points for recording the queries and evidence.

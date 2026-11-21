# Search and retrieval

Use `mcp-dir search` to discover a tool or seed pack offline. To search your own documents or the public web, choose a provider below and query it directly.

| Goal | Tools and source | What you get |
| --- | --- | --- |
| Find a server, seed pack, retriever, reranker or index library | `mcp-dir search retrieval --scope all --limit 5 --format json` | Ranked local metadata matches with links. Server records point to the upstream project. Pack records link to the pinned guide and manifest. Retrieval tools and libraries link to both the project and its pinned catalog entry. |
| Query documents your team has already indexed | [OpenSearch MCP](https://github.com/opensearch-project/opensearch-mcp-server-py), [Elastic Agent Builder](https://www.elastic.co/docs/explore-analyze/ai-features/agent-builder/mcp-server), [Meilisearch MCP](https://www.meilisearch.com/docs/getting_started/integrations/mcp) | Return documents or run configured queries under the cluster's permissions. Meilisearch also exposes facets. |
| Manage hosted search infrastructure | [Typesense Cloud MCP](https://typesense.org/docs/guide/typesense-cloud/mcp-server.html) | Inspect cluster metrics, manage clusters and index data. Use a collection's search API for your application's end-user queries. |
| Discover pages and retrieve their contents | [Kagi](https://github.com/kagisearch/kagimcp), [Linkup](https://docs.linkup.so/pages/integrations/mcp/mcp), [Tavily](https://github.com/tavily-ai/tavily-mcp), [Exa](https://github.com/exa-labs/exa-mcp-server) | Search the provider's web coverage and fetch selected pages. Keep the URL, retrieval time and supporting passage with each result. |
| Find records with similar meaning | [Qdrant](https://github.com/qdrant/mcp-server-qdrant), [Weaviate](https://docs.weaviate.io/weaviate/configuration/mcp-server), [vector search and ANN libraries](https://github.com/Amarel-Taylor-Scott/vector-search-ann-libs-directory) | Nearest-neighbor search over embeddings. Hybrid retrieval also uses lexical evidence, which helps when exact identifiers matter. |
| Improve the order of a candidate set | [RAG Retrievers & Rerankers Directory](https://github.com/Amarel-Taylor-Scott/rag-retrievers-rerankers-directory) | Compare first-stage retrievers and second-stage rerankers. A reranker scores the candidates it receives, so measure how often the first stage retrieves the right document. |

### Connecting to your own index

- **OpenSearch.** Set `OPENSEARCH_URL` and credentials for your cluster. The local launcher also supports `OPENSEARCH_NO_AUTH=true` for an intentionally unauthenticated cluster. [Setup guide](https://github.com/opensearch-project/opensearch-mcp-server-py/blob/main/USER_GUIDE.md)
- **Elastic.** Supply a Kibana URL and an API key for the configured space. Custom spaces use `/s/{SPACE_ID}/api/agent_builder/mcp`. Serverless also supports OAuth through the URL shown in the client's settings. Check your deployment's Agent Builder entitlement. [Connection guide](https://www.elastic.co/docs/explore-analyze/ai-features/agent-builder/mcp-server)
- **Meilisearch.** On v1.54 or later, enable the experimental `mcpRoute` feature and use a client supporting MCP version `2026-07-28`. Scope the bearer key to the intended indexes with `indexes.get`, `documents.get` and `search` for the full tool set. [Version and access requirements](https://github.com/meilisearch/documentation/blob/main/getting_started/integrations/mcp.mdx)

### Search the directories offline

The CLI searches metadata bundled in the checkout and Python wheel. Choose a scope to narrow the results.

| Scope | Records | Searchable examples |
| --- | --- | --- |
| `servers` (default) | MCP servers | Name, tags, description, maintainer, language, transport |
| `packs` | ta-amps seed packs | Pack ID, title, upstream manifest summary, status |
| `retrievers` | RAG retrievers, full-text engines and rerankers | Name or catalog ID, tags, project notes, organization, category, license |
| `libraries` | Vector search and approximate nearest neighbor libraries | Name or catalog ID, tags, index algorithms in project notes |
| `all` | All four collections | Search across record types with one query |

```bash
mcp-dir search rag:tantivy --scope retrievers --format json
mcp-dir search "CAGRA GPU acceleration" --scope libraries --mode bm25 --limit 3
mcp-dir search "frame by frame video quality assurance" --scope packs --mode bm25 --limit 3
mcp-dir search retrieval --scope all --limit 5 --format json
```

The default `lexical` mode requires every search term to appear as a substring. It handles partial names such as `postgre`. Use `bm25` when only some of your words are likely to appear in the catalog. An exact name or ID ranks first, followed by the number of distinct matching stems. English stemming lets a query for `facet` match `facets`. Weighted SQLite BM25 breaks ties using names, tags and descriptive metadata. Common English function words are ignored. Users can enter punctuation and operators as plain text. This mode requires Python with SQLite FTS5. A partial match can name the right product even when it lacks the requested capability. Check the linked project before acting on a result.

For the fixed query sets, measured rankings and commands to repeat the comparison, see the [search benchmark](../benchmarks/search/README.md).

Every JSON result has a `source`, `name` and `url`. Seed packs also have a `pack_id`, `manifest_url` and `summary`. A retriever or library includes an `id` such as `rag:tantivy` or `ann:faiss`, a project `url` and a `catalog_url` pointing to the source revision. A project can appear in several collections when the records serve different purposes.

### Refresh the bundled metadata

The [retrieval snapshot](retrieval-catalogs.json) records the full source commits for both sibling directories. Reproduce the committed snapshot with `python scripts/refresh_retrieval_catalog.py --check`. Add `--rag-repo PATH --ann-repo PATH` to use local Git clones offline. To update both pins to their latest main commits, run `python scripts/refresh_retrieval_catalog.py --update` and review the diff.

Regenerate the [seed pack index](ta-amps-seedpacks.csv) and its [attribution](ta-amps-seedpacks.LICENSE.txt) from a clone of [the ta-amps seed pack library](https://github.com/ta-amps/seed-packs-library-of-nouns-and-verbs). Supply the full revision you intend to reference. For the current snapshot, run this command from the checkout.

```bash
python scripts/refresh_seedpacks.py /path/to/seed-packs-library-of-nouns-and-verbs 24b7d2970de959cd4b4bdb5c33f6a45cc9c9326b
```

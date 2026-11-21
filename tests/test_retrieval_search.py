"""Check the linked search scopes, optional BM25 ranking, and error paths."""

from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
import json
import sys
from unittest.mock import patch

import main as cli


def search(*args):
    options = cli.build_parser().parse_args(["search", "--format", "json", *args])
    out = StringIO()
    with redirect_stdout(out):
        assert cli.cmd_search(options) == 0
    return json.loads(out.getvalue())


def test_scoped_results_keep_ids_and_upstream_provenance():
    lib = search("--scope", "libraries", "ann:faiss")[0]
    assert (lib["source"], lib["catalog"], lib["id"]) == ("library", "ann", "ann:faiss")
    assert lib["url"] == "https://github.com/facebookresearch/faiss"
    assert "/blob/" in lib["catalog_url"]
    tool = search("--scope", "retrievers", "rag:tantivy")[0]
    assert (tool["source"], tool["name"]) == ("retriever", "Tantivy")
    assert tool in search("--scope", "all", "rag:tantivy")
    assert not search("--scope", "servers", "rag:tantivy")


def test_pack_discovery_matches_upstream_summary():
    pack = search("--scope", "packs", "sidechain pause")[0]
    assert pack["pack_id"] == "audio-and-narration-qa"
    assert "sidechain pause-pumping" in pack["summary"]
    assert pack["manifest_url"].endswith("/audio-and-narration-qa/manifest.json")


def test_bm25_accepts_partial_queries_and_full_term_coverage_ranks_first():
    hits = search("--mode", "bm25", "--scope", "libraries", "where is CAGRA GPU acceleration documented?")
    assert hits[0]["id"] == "ann:cuvs"
    assert not search("--scope", "libraries", "where is CAGRA GPU acceleration documented?")
    assert hits == search("--mode", "bm25", "--scope", "libraries", "where is CAGRA GPU acceleration documented?")


def test_bm25_treats_query_syntax_as_plain_text_and_returns_empty_arrays():
    args = ("--scope", "libraries", "--mode", "bm25", "--limit", "1")
    assert search(*args, '"FAISS" OR * ? (') == search(*args, "faiss")
    assert search(*args, ':* ("') == []
    assert search(*args, "xyzzyxxxx") == []


def test_bm25_explains_missing_sqlite_without_breaking_lexical():
    options = cli.build_parser().parse_args(["search", "--mode", "bm25", "memory"])
    error = StringIO()
    with patch.dict(sys.modules, {"sqlite3": None}), redirect_stderr(error):
        assert cli.cmd_search(options) == 2
        assert search("memory")
    assert "FTS5" in error.getvalue() and "--mode lexical" in error.getvalue()


def test_bm25_counts_inflected_forms_once_for_coverage_and_ranking():
    def item(name, tags, description):
        row = {"name": name, "source": "server", "url": "https://example.org/"}
        return row, [name], tags, [description]

    corpus = [item("A", ["facet"], ""), item("B", [], "Facets and archives"), item("C", [], "An archive")]
    expected = cli._bm25_search(corpus, "facet archive")
    assert expected[0]["name"] == "B"  # Both query concepts, despite two different inflections.
    assert expected == cli._bm25_search(corpus, "facets archives")
    assert expected == cli._bm25_search(corpus, "facet facets archive archives")

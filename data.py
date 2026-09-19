"""MCP Servers Directory — curated registry.

A catalog of Model Context Protocol (MCP) servers: small programs that expose
tools, resources, and prompts to MCP-compatible clients (Claude Desktop, IDEs,
agents). Entries are public projects catalogued with links — no third-party
code is vendored here.

Each entry records: name, description, category, maintainer, whether it is an
official/reference server, the transport(s) it supports, the primary install
command, and links. Curation is best-effort and community-correctable via PRs.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Category(Enum):
    filesystem = "filesystem"
    version_control = "version_control"
    database = "database"
    search_web = "search_web"
    browser = "browser"
    dev_tools = "dev_tools"
    cloud_devops = "cloud_devops"
    communication = "communication"
    productivity = "productivity"
    data_apis = "data_apis"
    ai_ml = "ai_ml"
    memory_knowledge = "memory_knowledge"
    finance = "finance"
    monitoring = "monitoring"

    @property
    def label(self) -> str:
        return {
            "filesystem": "Filesystem & Local",
            "version_control": "Version Control",
            "database": "Databases",
            "search_web": "Search & Web",
            "browser": "Browser Automation",
            "dev_tools": "Developer Tools",
            "cloud_devops": "Cloud & DevOps",
            "communication": "Communication",
            "productivity": "Productivity & Docs",
            "data_apis": "Data & APIs",
            "ai_ml": "AI / ML",
            "memory_knowledge": "Memory & Knowledge",
            "finance": "Finance & Payments",
            "monitoring": "Monitoring & Observability",
        }[self.value]


class Transport(Enum):
    stdio = "stdio"
    sse = "sse"
    http = "http"


@dataclass(frozen=True)
class Server:
    name: str
    description: str
    category: Category
    maintainer: str
    official: bool = False            # official reference / first-party vendor server
    transports: tuple[Transport, ...] = (Transport.stdio,)
    language: str = ""
    install: str = ""                 # primary install / run command
    repo: str = ""
    homepage: str = ""
    auth_required: bool = False
    tags: tuple[str, ...] = field(default_factory=tuple)


# ---------------------------------------------------------------------------
# Registry — curated, public MCP servers (links only; no vendored code).
# ---------------------------------------------------------------------------
SERVERS: list[Server] = [
    # --- Filesystem & local ---
    Server("Filesystem", "Read/write files within allowed directories, with path sandboxing.",
           Category.filesystem, "Anthropic (reference)", official=True, language="TypeScript",
           install="npx -y @modelcontextprotocol/server-filesystem <dir>",
           repo="https://github.com/modelcontextprotocol/servers", tags=("files", "reference")),
    Server("Git", "Inspect and operate on local Git repositories (status, diff, log, commit).",
           Category.version_control, "Anthropic (reference)", official=True, language="Python",
           install="uvx mcp-server-git --repository <path>",
           repo="https://github.com/modelcontextprotocol/servers", tags=("git", "reference")),
    Server("Fetch", "Fetch a URL and return cleaned, LLM-friendly content (HTML→markdown).",
           Category.search_web, "Anthropic (reference)", official=True, language="Python",
           install="uvx mcp-server-fetch",
           repo="https://github.com/modelcontextprotocol/servers", tags=("http", "scrape", "reference")),
    Server("Memory", "Lightweight knowledge-graph memory that persists across sessions.",
           Category.memory_knowledge, "Anthropic (reference)", official=True, language="TypeScript",
           install="npx -y @modelcontextprotocol/server-memory",
           repo="https://github.com/modelcontextprotocol/servers", tags=("memory", "graph", "reference")),
    Server("Sequential Thinking", "Structured step-by-step reasoning scaffold exposed as a tool.",
           Category.ai_ml, "Anthropic (reference)", official=True, language="TypeScript",
           install="npx -y @modelcontextprotocol/server-sequential-thinking",
           repo="https://github.com/modelcontextprotocol/servers", tags=("reasoning", "reference")),
    Server("Everything", "Reference/test server exercising all MCP features (tools, resources, prompts).",
           Category.dev_tools, "Anthropic (reference)", official=True, language="TypeScript",
           install="npx -y @modelcontextprotocol/server-everything",
           repo="https://github.com/modelcontextprotocol/servers", tags=("reference", "testing")),

    # --- Version control / dev platforms ---
    Server("GitHub", "Manage repos, issues, PRs, code search and files via the GitHub API.",
           Category.version_control, "GitHub", official=True, language="Go",
           install="docker run -e GITHUB_PERSONAL_ACCESS_TOKEN ghcr.io/github/github-mcp-server",
           repo="https://github.com/github/github-mcp-server", auth_required=True, tags=("github", "issues", "pr")),
    Server("GitLab", "Interact with GitLab projects, MRs, issues and CI pipelines.",
           Category.version_control, "Community", language="TypeScript",
           install="npx -y @modelcontextprotocol/server-gitlab",
           repo="https://github.com/modelcontextprotocol/servers", auth_required=True, tags=("gitlab",)),
    Server("Sentry", "Pull and triage Sentry issues, events and stack traces.",
           Category.monitoring, "Sentry", official=True, language="Python",
           install="uvx mcp-server-sentry --auth-token <token>",
           repo="https://github.com/getsentry/sentry-mcp", auth_required=True, tags=("errors", "observability")),

    # --- Databases ---
    Server("PostgreSQL", "Read-only SQL queries and schema introspection over Postgres.",
           Category.database, "Community", language="TypeScript",
           install="npx -y @modelcontextprotocol/server-postgres <connection-url>",
           repo="https://github.com/modelcontextprotocol/servers", auth_required=True, tags=("sql", "postgres")),
    Server("SQLite", "Query and explore a local SQLite database file.",
           Category.database, "Community", language="Python",
           install="uvx mcp-server-sqlite --db-path <file>",
           repo="https://github.com/modelcontextprotocol/servers", tags=("sql", "sqlite", "local")),
    Server("Redis", "Get/set and inspect keys in a Redis instance.",
           Category.database, "Redis", official=True, language="Python",
           install="uvx --from redis-mcp redis-mcp",
           repo="https://github.com/redis/mcp-redis", auth_required=True, tags=("cache", "kv")),
    Server("MongoDB", "Query collections and inspect schema in MongoDB / Atlas.",
           Category.database, "MongoDB", official=True, language="TypeScript",
           install="npx -y mongodb-mcp-server",
           repo="https://github.com/mongodb-js/mongodb-mcp-server", auth_required=True, tags=("nosql", "documents")),
    Server("ClickHouse", "Run analytical SQL against ClickHouse.",
           Category.database, "ClickHouse", official=True, language="Python",
           install="uvx mcp-clickhouse",
           repo="https://github.com/ClickHouse/mcp-clickhouse", auth_required=True, tags=("olap", "analytics")),
    Server("Supabase", "Manage Supabase projects, run SQL, and work with auth/storage.",
           Category.database, "Supabase", official=True, language="TypeScript",
           install="npx -y @supabase/mcp-server-supabase --access-token <token>",
           repo="https://github.com/supabase-community/supabase-mcp", auth_required=True, tags=("postgres", "baas")),

    # --- Search & web ---
    Server("Brave Search", "Web and local search via the Brave Search API.",
           Category.search_web, "Brave / Community", language="TypeScript",
           install="npx -y @modelcontextprotocol/server-brave-search",
           repo="https://github.com/modelcontextprotocol/servers", auth_required=True, tags=("search", "web")),
    Server("Tavily", "LLM-optimized web search and extraction for agents.",
           Category.search_web, "Tavily", official=True, language="Python",
           install="uvx tavily-mcp",
           repo="https://github.com/tavily-ai/tavily-mcp", auth_required=True, tags=("search", "rag")),
    Server("Exa", "Neural/semantic web search and content retrieval.",
           Category.search_web, "Exa", official=True, language="TypeScript",
           install="npx -y exa-mcp-server",
           repo="https://github.com/exa-labs/exa-mcp-server", auth_required=True, tags=("search", "semantic")),
    Server("Firecrawl", "Crawl, scrape and convert websites to clean markdown.",
           Category.search_web, "Firecrawl", official=True, language="TypeScript",
           install="npx -y firecrawl-mcp",
           repo="https://github.com/mendableai/firecrawl-mcp-server", auth_required=True, tags=("scrape", "crawl")),

    # --- Browser automation ---
    Server("Puppeteer", "Drive a headless Chrome browser: navigate, click, screenshot, evaluate JS.",
           Category.browser, "Community", language="TypeScript",
           install="npx -y @modelcontextprotocol/server-puppeteer",
           repo="https://github.com/modelcontextprotocol/servers", tags=("browser", "automation")),
    Server("Playwright", "Cross-browser automation and accessibility-tree driven navigation.",
           Category.browser, "Microsoft", official=True, language="TypeScript",
           install="npx -y @playwright/mcp",
           repo="https://github.com/microsoft/playwright-mcp", tags=("browser", "automation", "testing")),
    Server("Browserbase", "Cloud headless browser sessions for agents (Stagehand).",
           Category.browser, "Browserbase", official=True, language="TypeScript",
           install="npx -y @browserbasehq/mcp-server-browserbase",
           repo="https://github.com/browserbase/mcp-server-browserbase", auth_required=True, tags=("browser", "cloud")),

    # --- Cloud & DevOps ---
    Server("AWS (Core)", "Suite of servers for AWS docs, CDK, cost, and core service operations.",
           Category.cloud_devops, "AWS", official=True, language="Python",
           install="uvx awslabs.core-mcp-server",
           repo="https://github.com/awslabs/mcp", auth_required=True, tags=("aws", "cloud")),
    Server("Cloudflare", "Operate Workers, KV, R2, D1 and analytics on Cloudflare.",
           Category.cloud_devops, "Cloudflare", official=True, language="TypeScript",
           install="npx -y @cloudflare/mcp-server-cloudflare",
           repo="https://github.com/cloudflare/mcp-server-cloudflare", auth_required=True, tags=("edge", "workers")),
    Server("Kubernetes", "Inspect and manage Kubernetes clusters, pods, and manifests.",
           Category.cloud_devops, "Community", language="TypeScript",
           install="npx -y mcp-server-kubernetes",
           repo="https://github.com/Flux159/mcp-server-kubernetes", auth_required=True, tags=("k8s", "devops")),
    Server("Docker", "Manage containers, images and compose stacks via the Docker engine.",
           Category.cloud_devops, "Community", language="Python",
           install="uvx docker-mcp",
           repo="https://github.com/QuantGeekDev/docker-mcp", tags=("containers", "devops")),

    # --- Communication ---
    Server("Slack", "Read channels and post messages to a Slack workspace.",
           Category.communication, "Community", language="TypeScript",
           install="npx -y @modelcontextprotocol/server-slack",
           repo="https://github.com/modelcontextprotocol/servers", auth_required=True, tags=("chat", "slack")),
    Server("Linear", "Create and update Linear issues, projects and cycles.",
           Category.productivity, "Linear", official=True, transports=(Transport.sse,), language="TypeScript",
           install="(remote SSE) https://mcp.linear.app/sse",
           repo="https://linear.app/docs/mcp", auth_required=True, tags=("issues", "pm")),

    # --- Productivity & docs ---
    Server("Google Drive", "Search and read files from Google Drive.",
           Category.productivity, "Community", language="TypeScript",
           install="npx -y @modelcontextprotocol/server-gdrive",
           repo="https://github.com/modelcontextprotocol/servers", auth_required=True, tags=("docs", "google")),
    Server("Notion", "Query and update Notion pages and databases.",
           Category.productivity, "Notion", official=True, transports=(Transport.http,), language="TypeScript",
           install="(remote) https://mcp.notion.com/mcp",
           repo="https://github.com/makenotion/notion-mcp-server", auth_required=True, tags=("notes", "wiki")),
    Server("Obsidian", "Read and search a local Obsidian vault of markdown notes.",
           Category.memory_knowledge, "Community", language="Python",
           install="uvx mcp-obsidian",
           repo="https://github.com/MarkusPfundstein/mcp-obsidian", tags=("notes", "markdown")),

    # --- Data & external APIs ---
    Server("Google Maps", "Geocoding, places, directions and distance via Google Maps APIs.",
           Category.data_apis, "Community", language="TypeScript",
           install="npx -y @modelcontextprotocol/server-google-maps",
           repo="https://github.com/modelcontextprotocol/servers", auth_required=True, tags=("maps", "geo")),
    Server("Stripe", "Create and inspect Stripe customers, payments, invoices and products.",
           Category.finance, "Stripe", official=True, language="TypeScript",
           install="npx -y @stripe/mcp --tools=all",
           repo="https://github.com/stripe/agent-toolkit", auth_required=True, tags=("payments", "billing")),
    Server("UnlockFlow MCP", "Unlock × capital-flow events as MCP tools (UnlockFlowEvent v1; illustrative seeds; NFA).",
           Category.finance, "Capital Flow Desk", language="TypeScript",
           transports=(Transport.http,),
           install="npx -y mcp-remote https://endorsement-development-configured-todd.trycloudflare.com/mcp",
           repo="https://github.com/mhr2027r-dotcom/mcp-unlockflow",
           homepage="https://mhr2027r-dotcom.github.io/capital-flow-desk-web/",
           auth_required=False, tags=("crypto", "unlocks", "capital-flow", "remote")),
    Server("Time", "Timezone-aware current time and conversions.",
           Category.data_apis, "Anthropic (reference)", official=True, language="Python",
           install="uvx mcp-server-time",
           repo="https://github.com/modelcontextprotocol/servers", tags=("time", "reference")),

    # --- AI / ML ---
    Server("EverArt", "Generate images via the EverArt API.",
           Category.ai_ml, "Community", language="TypeScript",
           install="npx -y @modelcontextprotocol/server-everart",
           repo="https://github.com/modelcontextprotocol/servers", auth_required=True, tags=("image", "generation")),
    Server("Qdrant", "Store and semantically search vectors in Qdrant as agent memory.",
           Category.memory_knowledge, "Qdrant", official=True, language="Python",
           install="uvx mcp-server-qdrant",
           repo="https://github.com/qdrant/mcp-server-qdrant", auth_required=True, tags=("vector", "rag", "memory")),
    Server("Chroma", "Vector store + retrieval over a Chroma collection.",
           Category.memory_knowledge, "Chroma", official=True, language="Python",
           install="uvx chroma-mcp",
           repo="https://github.com/chroma-core/chroma-mcp", tags=("vector", "rag")),
]

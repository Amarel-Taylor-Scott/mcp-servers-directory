# Additional resource notes

Reviewed against upstream documentation on 2026-11-21. Catalog entries are links, not a security certification or an assurance that every client has been tested.

| Resource | Setup and authentication | License and dependencies | Access implications |
| --- | --- | --- | --- |
| [Context7](https://github.com/upstash/context7) | Hosted HTTP: https://mcp.context7.com/mcp. Upstream recommends an optional API key for higher limits; configured keys use the Authorization bearer header. | MIT MCP source; supporting API backend, parser and crawler are private. Hosted service limits and terms apply. | Queries leave the client for the hosted service. The directory's required-auth flag remains false because upstream describes keys as recommended. |
| [Chrome DevTools](https://github.com/ChromeDevTools/chrome-devtools-mcp) | Node.js LTS, npm and Chrome required; stdio. | Apache-2.0. | Can inspect and modify browser data. Listed command disables default usage statistics and CrUX lookups. Use an isolated test browser profile for verification. |
| [MarkItDown MCP](https://github.com/microsoft/markitdown/tree/main/packages/markitdown-mcp) | Install with pip install markitdown-mcp, then run markitdown-mcp for stdio. HTTP/SSE modes bind to localhost by default. | MIT; conversion dependencies vary by format. | No server authentication. Can read files and network resources accessible to its process. Keep HTTP/SSE on localhost and restrict file/network access. |
| [Kilobat CLI](https://github.com/seifip/kilobat-cli) | macOS 14+; documented Homebrew build requires Xcode 16+. Start MCP with kilobat mcp. | Contributor discloses GPL-3.0-only CLI; proprietary companion app and license tiers for some features. | Includes settings-changing tools. Tool descriptions asking for confirmation do not independently enforce client approval. |

## Validation scope

The existing six registry/CLI test functions were executed directly with Python because pytest was unavailable in this environment. Generated README equality, JSON export, category counts, and duplicate names are checked locally. A regression test now compares the checked-in README to fresh generator output to catch stale totals after combining additions.

No paid account was created, OAuth grant issued, Homebrew install tested, or upstream server executed. The Kilobat contributor reports a source-build initialization and get_status smoke test. New entries were checked against upstream setup and license documentation; end-to-end compatibility remains unverified.

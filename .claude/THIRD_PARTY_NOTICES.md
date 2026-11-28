# Third-party skills and agents in `.claude/`

Fetched and audited 2026-11-23. Each copied file states its own changes at its top.

| Path | Source (commit) | License | Kept | Removed |
|---|---|---|---|---|
| `skills/nautilus-trader/` | github.com/HyperFrequency/skills `nautilus-trader/` (7532af7) | MIT (README; no LICENSE file upstream) | SKILL.md (edited), 6 scraped doc files minus 17 pages, index.md (rewritten) | `hyperliquid_patch.py`, `live_trading.py`, `set_leverage.py`, `requirements.txt`, `README.md`, `CHANGELOG.md`, `hyperliquid.md`, `other.md`; integration, adapter, live, developer-guide, installation pages |
| `skills/strategy-workflow/` | HyperFrequency/skills `strategy-workflow/` (7532af7) | MIT (README) | SKILL.md (edited) | `backtest-optimize.md`, `references/strategy_generation.md`; swarm, Vast.ai, watchdog, PAL MCP sections |
| `skills/tearsheet-generator/` | HyperFrequency/skills `tearsheet-generator/` (7532af7) | MIT (README) | SKILL.md (edited), `tearsheet_helpers.py` (unchanged), `commands/` (1 import edited), `references/` (index edited) | personal-path import, Hyperliquid SDK-patch row, nonexistent script references |
| `skills/nautilus-authoring/` | github.com/cajias/nautilus-trading `skills/nautilus-strategy-authoring/`, `agents/strategy-author.md` (998a4ae) | MIT, (c) 2026 Raul Cajias | pitfalls rewritten and checked on 1.231.0 | `nt` CLI registry contract, live/paper-node items, the agent |
| `skills/portfolio-optimizer/` | github.com/vignesh2027/claude-agentic-skills2.0-version `portfolio-optimizer/` (4c0a417) | MIT, (c) 2026 vignesh2027 | SKILL.md (edited) | tax-loss-harvesting section |
| `agents/quant-analyst.md` | github.com/VoltAgent/awesome-claude-code-subagents `categories/07-specialized-domains/quant-analyst.md` (ed74d11) | MIT, (c) 2025 VoltAgent | agent (edited) | context-manager protocol, live/HFT targets, invented delivery numbers, nonexistent collaborators |
| `skills/nautilus-portfolio-bridge/` | written for QUANTGEN | (repository) | | |

## MIT License

Copyright (c) HyperFrequency (skills); (c) 2026 Raul Cajias; (c) 2026 vignesh2027; (c) 2025 VoltAgent

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
documentation files (the "Software"), to deal in the Software without restriction, including without limitation the
rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit
persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the
Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

# AI-Powered Competitor News Monitor & Weekly Digest

An n8n workflow that watches AI/automation industry news, self-heals when a source goes dead, deduplicates overlapping coverage across outlets, and emails a synthesized weekly digest — no manual upkeep required.

Built as a take-home exercise, then extended past the base spec to explore a real production concern: **RSS feeds die, and a competitive-intelligence tool that silently degrades is worse than one that fails loudly.**

![Workflow architecture](docs/architecture-screenshot.png)

## What it does

Every Monday at 9am:
1. Reads which of 5 primary + 2 backup news sources are currently active from a Data Table.
2. Fetches each active source's RSS/Atom feed (with retries, timeouts, and graceful failure).
3. Extracts articles published in the last 7 days, tracks each source's health, and rotates in a backup if a source has gone silent for 2 weeks.
4. Sends the combined, deduplicated headlines to GPT-4o-mini with a prompt that forces synthesis (not headline-listing) into two sections.
5. Formats the result as a clean digest and emails it via Gmail.

See [`docs/sample-digest.md`](docs/sample-digest.md) for a real output from a live run.

## Why this is more than the base assignment

The original brief asked for: a schedule trigger, ≥2 RSS sources via HTTP Request, an AI summarization step, a formatting step, and an email/Slack output. All of that is here — but the part actually worth discussing in an interview is the **self-healing source rotation**, detailed in [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md):

- A Data Table (`source_tracker`) persists per-source health across scheduled runs — silent-week counts, active/backup status, which backup is covering for which primary.
- A source that goes quiet for 2 weeks automatically gets a backup promoted in its place; it's dropped entirely after 2 more silent weeks, or fully restored if it recovers first.
- Cross-source duplicate stories (the same funding round covered by 3 outlets) are merged by the LLM at the prompt layer, not guessed at with string matching.
- Every fetch is retried, time-boxed, and fails soft — one dead feed never takes down the whole run.

That doc also covers a real bug I hit and fixed: a race condition where two Data Table reads ran as parallel branches off the trigger with no guaranteed ordering, causing an intermittent "node hasn't executed" failure. Worth reading if you want to see the debugging, not just the finished diagram.

## Repo contents

```
.
├── README.md
├── workflow/
│   └── workflow.json          # Importable n8n workflow export
└── docs/
    ├── architecture-screenshot.png
    ├── ARCHITECTURE.md        # Design decisions, state machine, tradeoffs, what I'd change for prod
    └── sample-digest.md       # Real output from a live run
```

## Running it yourself

1. Import `workflow/workflow.json` into an n8n instance (free cloud tier or self-hosted).
2. Create a Data Table named `source_tracker` with columns: `name` (string), `url` (string), `pool` (string), `active` (boolean), `consecutive_silent_weeks` (number), `monitoring` (boolean), `replaced_source` (string), `backup_rank` (number). Seed it with your sources (`pool: primary`, `active: true`) and backups (`pool: backup`, `active: false`, ranked by `backup_rank`).
3. Connect an OpenAI credential and a Gmail (or other email/Slack) credential.
4. Publish and activate — it will run on the built-in weekly schedule.

## Stack

n8n (Data Tables, Code nodes, HTTP Request, Filter, OpenAI, Gmail) · GPT-4o-mini · regex-based RSS/Atom parsing (no external dependency)

---

Built with [Claude Code](https://claude.com/claude-code), driving the n8n browser UI directly — no separate chat-based design tool. Happy to walk through the build/debug session on request.

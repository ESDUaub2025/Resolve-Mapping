# Agent instructions

<!-- projectgraph:begin -->
## ProjectGraph

This repository is ProjectGraph-enabled. Its project map, state and
verification evidence live in `.projectgraph/`.

Before starting work in a new session:

1. `projectgraph resume` — read the current briefing instead of re-reading the repo.
2. Read details if the briefing is truncated; `projectgraph next` lists eligible work.
3. `projectgraph begin <NODE>` before writing code.
4. `projectgraph verify <NODE>` when done.

Before leaving work, use `projectgraph handoff <NODE> --note "..." --next-action "..."`.
Use `projectgraph reconcile` to preview code-map drift, and `--apply` to publish it.
Upgrade existing graphs with `projectgraph upgrade --dry-run`, then `--apply`;
preserve authored history instead of rebuilding with force migration.

`VERIFIED` is computed from verification evidence. Never claim it; run `verify`.
Full procedure: the globally installed `projectgraph` Agent Skill.
<!-- projectgraph:end -->

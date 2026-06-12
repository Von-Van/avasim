# Archive — Frozen Next-Gen Experiment

This directory holds the **frozen experimental reference material** from the
multi-service "next-gen" build plan (React/Tauri UI, TypeScript orchestrator,
Rust rules engine, Docker stack, shared JSON schema).

The project direction changed: the **canonical runtime is the PySide desktop
app plus the pure-Python combat/analysis core** (see
[docs/analysis_core.md](../docs/analysis_core.md)). Nothing in here receives
feature work; it is kept as reference for a possible future port now that the
Python runtime contract is stable.

Contents:

- `apps/` — TypeScript orchestrator and Python sim-worker skeletons
- `services/` — Rust rules-engine stub
- `packages/schema/` — versioned run-contract JSON schemas and examples
- `infra/docker/` — compose stack (start with
  `docker compose -f archive/infra/docker/compose.yml up -d`)
- `examples/` — the structured event-emitter demo from Phase 2
- `docs/` — the original next-gen build plan, visual schema, and the
  Phase 0–2 write-ups

Relative links inside these archived docs may assume the old repo layout.

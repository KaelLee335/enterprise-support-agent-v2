# Project Agent Instructions

## Project

Enterprise Support Agent V2 is a local learning/demo project that reuses V1 policy and evaluation assets. It is not a production support system. Keep V1 assets and rules intact; V2-only rules must retain explicit source/version labels.

## Current status (2026-11-16)

- Stages 0–6 are implemented. The latest expanded verifier was synced to WSL `/opt/project2`; health passed and all 11 use cases passed with exit code 0, including the POL-06 synonymous timing phrase and the policy constraint boundaries.
- The Windows project is `D:\project_2`. Docker builds in WSL `/opt/project2` because BuildKit on `/mnt/d` had permission problems. Container data is bind-mounted from `D:\project_2\data` via `/mnt/d/project_2/data`.
- Retrieval comparison on 36 evidence-labeled cases:

  | top-k | Hit@k | Mean Recall@k | Complete evidence |
  |---:|---:|---:|---:|
  | 2 | 97.2% | 77.3% | 58.3% |
  | 4 | 100.0% | 86.6% | 72.2% |
  | 6 | 100.0% | 89.4% | 77.8% |
  | 8 | 100.0% | 99.1% | 97.2% |

- The user chose to keep `RAG_TOP_K=4` after answer-quality assessment. A 14-case Top-4/Top-8 generation comparison exists at `data/evaluation/v2_rag_answers.json`, with a manual audit in `docs/rag_answer_manual_review.md`. Its generator and LLM judge use the same Qwen model; automated scores are exploratory and demonstrably contain judge errors. Manual inspection found a Top-8 KB-04 answer contradicting the POL-04 exclusion for liquid damage. Do not treat the judge scores as ground truth or change the default based on retrieval recall alone.
- The user then approved a small policy-constraint layer. Local code is in `src/support_agent/rag/answer_constraints.py`; it handles explicit POL-04 liquid-damage exclusion, POL-02 quality/no-reason routing and return qualifiers, POL-05 shipping instructions, POL-06 refund stages, and POL-09 invoice privacy/scope. Full 14-case Top-4/Top-8 generation evaluation (judge skipped) is `data/evaluation/v2_rag_answers_constraints_v3.json`: 28/28 citation-ID checks valid; constraints matched 11 cases per k and were enforced in 6/7 outputs. Targeted answers were manually inspected. The updated code was deployed to WSL; the expanded health + 11-case verifier passed with exit code 0. This runtime acceptance is separate from semantic accuracy scoring.
- `systemctl is-active docker` was blank and `systemctl is-enabled docker` was `enabled`. User verified Ubuntu WSL Stopped → `Start-ScheduledTask` → `dockerd ready` → project container healthy → `/health` 200. A 2026-11-16 read-only inspection found `WSL-Dockerd-Autostart` runs as the interactive user on a Logon trigger (not Startup); it does not guarantee recovery before login. No task, WSL/systemd, or network-adapter settings were changed. Obtain approval before changing host startup behavior.
- User asked to postpone project-learning interview questions until later. Do not start those questions unless asked.

## Phase 7 completed: release readiness

- The original project stages 0–6 are complete. Phase 7 prepares a reproducible local/GitHub-ready handoff without publishing externally.
- A clean clone will not contain `data/vector_store/` because the vector database is local/generated and ignored. Docker build must not require that directory; the README now instructs indexing before first Docker use.
- Compose data persistence is configurable via `PROJECT_DATA_DIR`. An unset/blank value retains this user's WSL `/mnt/d/project_2/data` default; other setups can override it in their local `.env`.
- The user verified `git status`: only expected project files/directories are untracked. Seven secret/generated paths are ignored and `.env.example` is not ignored. WSL rebuild succeeded, the `/mnt/d/project_2/data -> /app/data` bind mount was confirmed, and all 11 verifier cases passed. No commit or remote push was made.

## Phase 8 completed: GitHub public delivery

- User chose a new public repository. Final tracked-file and credential/runtime-data review completed before publishing; `.env`, databases, WAL, vector store, virtualenv, test cache, and egg-info were excluded, while `.env.example` was included with an empty key.
- Public repository: `https://github.com/KaelLee335/enterprise-support-agent-v2`, branch `main`. Local commits `e68a1cea` (initial release) and `04503a1` (release target documentation) were pushed. Remote Git tree was inspected: 105 entries, README/source/tests present, no `.env`, databases/WAL, vector store, virtualenv, caches, or egg-info paths. Keep credentials and local runtime data out of future commits.

## Active work and priorities

1. Original stages 0–6, phase 7 release readiness, and phase 8 public GitHub delivery are complete. The expanded WSL verifier passed health plus 11 use cases with exit code 0; no rebuild is pending. Local `main` tracks `origin/main`.
2. Phase 9 is complete. User clarified that “boot trigger” means starting on Windows user logon; the existing Logon trigger is intended and must remain unchanged. Do not stop the current daemon, start a second daemon, enable systemd, edit `/etc/wsl.conf`, modify network adapters, or restart WSL merely to test it.
3. Productionization remains out of demo scope: real authentication/tenant identity, approval RBAC/audit, multi-instance persistence, limits/timeouts/retries, and security operations. User-requested learning discussion remains deferred.

## Runtime and data boundaries

- The user runs Docker through WSL and the desktop launcher. Do not assume the Windows shell can control that daemon. Do not move Docker builds back to `/mnt/d`; use the established WSL `/opt/project2` workflow.
- Preserve D-drive persistence for SQLite, checkpoints, Chroma data, and policies through the existing bind mount.
- Do not expose `.env` values, API keys, or credentials in output, logs, reports, or commits. Never print the key while inspecting configuration.
- SiliconFlow/Qwen is the configured provider. The user explicitly approved sending the 14 demo questions, matched policy evidence, generated answers, and judge prompts to the configured SiliconFlow Qwen for the current evaluation. Ask before sending new datasets, personal data, or content to a different provider/model.
- Refund approval is a demo-only state transition (`approved_demo`); never add a real refund/write operation without explicit scope and authorization.

## Working and documentation rules

- Keep `task_plan.md` as the checklist, `progress.md` as the chronological record, `findings.md` as durable implementation/diagnostic findings, and `docs/project_status.md` as the concise current dashboard.
- Whenever a stage, verification result, decision, or blocking dependency changes, update `AGENTS.md` current status/active work and the relevant plan/progress/status documentation in the same work session.
- Reconcile stale statements in user-facing docs when newer evidence supersedes them. Preserve old historical entries only when they are clearly labeled as historical/superseded.
- Be precise about denominators and evidence. Distinguish route accuracy, retrieval recall, citation-ID validation, semantic correctness, and end-to-end task success; do not collapse them into one score.
- Do not claim a test, API call, deployment, or runtime check unless it actually ran and its result is recorded. Keep Docker acceptance tied to the user's WSL result unless this environment can directly verify it.
- Make small, reviewable changes. Do not change `RAG_TOP_K=4` without a fresh comparison and a recorded decision.

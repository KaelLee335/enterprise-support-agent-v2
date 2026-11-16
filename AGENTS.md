# Project Agent Instructions

## Project

Enterprise Support Agent V2 is a local learning/demo project that reuses V1 policy and evaluation assets. It is not a production support system. Keep V1 assets and rules intact; V2-only rules must retain explicit source/version labels.

## Current status (2026-11-16)

- Stages 0–6 are implemented. The latest expanded verifier was synced to WSL `the WSL project directory`; health passed and all 11 use cases passed with exit code 0, including the POL-06 synonymous timing phrase and the policy constraint boundaries.
- The Windows project is `the local project directory`. Docker builds in WSL `the WSL project directory` because BuildKit on `the local Windows-mounted directory` had permission problems. Container data is bind-mounted from `the local persistent data directory` via `the bind-mounted data directory`.
- Retrieval comparison on 36 evidence-labeled cases:

  | top-k | Hit@k | Mean Recall@k | Complete evidence |
  |---:|---:|---:|---:|
  | 2 | 97.2% | 77.3% | 58.3% |
  | 4 | 100.0% | 86.6% | 72.2% |
  | 6 | 100.0% | 89.4% | 77.8% |
  | 8 | 100.0% | 99.1% | 97.2% |

- The user chose to keep `RAG_TOP_K=4` after answer-quality assessment. A 14-case Top-4/Top-8 generation comparison exists at `data/evaluation/v2_rag_answers.json`, with a manual audit in `docs/rag_answer_manual_review.md`. Its generator and LLM judge use the same Qwen model; automated scores are exploratory and demonstrably contain judge errors. Manual inspection found a Top-8 KB-04 answer contradicting the POL-04 exclusion for liquid damage. Do not treat the judge scores as ground truth or change the default based on retrieval recall alone.
- The user then approved a small policy-constraint layer. Local code is in `src/support_agent/rag/answer_constraints.py`; it handles explicit POL-04 liquid-damage exclusion, POL-02 quality/no-reason routing and return qualifiers, POL-05 shipping instructions, POL-06 refund stages, and POL-09 invoice privacy/scope. Full 14-case Top-4/Top-8 generation evaluation (judge skipped) is `data/evaluation/v2_rag_answers_constraints_v3.json`: 28/28 citation-ID checks valid; constraints matched 11 cases per k and were enforced in 6/7 outputs. Targeted answers were manually inspected. The updated code was deployed to WSL; the expanded health + 11-case verifier passed with exit code 0. This runtime acceptance is separate from semantic accuracy scoring.
- `systemctl is-active docker` was blank and `systemctl is-enabled docker` was `enabled`. User verified Ubuntu WSL Stopped → `Start-ScheduledTask` → `dockerd ready` → project container healthy → `/health` 200. A 2026-11-16 read-only inspection found `the existing scheduled task` runs as the interactive user on a Logon trigger (not Startup); it does not guarantee recovery before login. No task, WSL/systemd, or network-adapter settings were changed. Obtain approval before changing host startup behavior.
- User asked to postpone project-learning interview questions until later. Do not start those questions unless asked.

## Phase 7 completed: release readiness

- The original project stages 0–6 are complete. Phase 7 prepares a reproducible local/GitHub-ready handoff without publishing externally.
- A clean clone will not contain `data/vector_store/` because the vector database is local/generated and ignored. Docker build must not require that directory; the README now instructs indexing before first Docker use.
- Compose data persistence is configurable via `PROJECT_DATA_DIR`. An unset/blank value retains this user's WSL `the bind-mounted data directory` default; other setups can override it in their local `.env`.
- The user verified `git status`: only expected project files/directories are untracked. Seven secret/generated paths are ignored and `.env.example` is not ignored. WSL rebuild succeeded, the `the bind-mounted data directory -> /app/data` bind mount was confirmed, and all 11 verifier cases passed. No commit or remote push was made.

## Phase 8 completed: GitHub public delivery

- User chose a new public repository. Final tracked-file and credential/runtime-data review completed before publishing; `.env`, databases, WAL, vector store, virtualenv, test cache, and egg-info were excluded, while `.env.example` was included with an empty key.
- Public repository: `https://github.com/KaelLee335/enterprise-support-agent-v2`, branch `main`. Local commits `e68a1cea` (initial release) and `04503a1` (release target documentation) were pushed. Remote Git tree was inspected: 105 entries, README/source/tests present, no `.env`, databases/WAL, vector store, virtualenv, caches, or egg-info paths. Keep credentials and local runtime data out of future commits.

## Active work and priorities

1. Phases 0–11 are complete. User screenshots report the Demo Bearer scope, 51 pytest cases, and WSL verifier 11/11. Phase 12 is complete per the user's reported acceptance: both targeted not_found and fake Chat Model timeout tests passed. Checkpoint corruption and Compose missing Key remain transparently documented as unverified. Phase 13 is complete per user report: clean clone, dependency installation, 53 pytest passed in 18.39s, health returned 200, Bearer order 1001 returned 200, and missing token returned 401. Phase 14 final documentation review is complete. The README, story/interview materials, demo guide, traceability matrix, fault library, and status records now reflect the user-reported clean-clone API smoke. Host startup and network notes are kept generic and do not expose machine-specific settings.
2. Phase 9 is complete. User clarified that “boot trigger” means starting on Windows user logon; the existing Logon trigger is intended and must remain unchanged. Do not stop the current daemon, start a second daemon, enable systemd, edit `/etc/wsl.conf`, modify network adapters, or restart WSL merely to test it.
3. The user's newest project brief (2026-11-16) supersedes the earlier user-led design gate: Codex is technical lead and primary developer; independently design and implement simple, maintainable solutions and continue through phases without waiting after every module. The user is the learner; teach from actual project code and do not require the user to design architecture or write core code first. Retain the learning order LangChain → LangGraph → RAG → SQL → FastAPI. Before each topic, explain the system role and current code, then provide Chinese code-linked learning material with a flow diagram, runnable examples, must-understand items, and 5–10 review questions. Run relevant tests after implementation and report actual results. Ask only for missing business facts, real secrets, external account authorization, or irreversible/destructive actions. Productionization scope is separate; updated P0 includes local demo identity/authentication, user/tenant data and minimal execution records where needed, basic safe CRUD, and explicit permission boundaries—do not overstate these as production-grade.

## Runtime and data boundaries

- The user runs Docker through WSL and the desktop launcher. Do not assume the Windows shell can control that daemon. Do not move Docker builds back to `the local Windows-mounted directory`; use the established WSL `the WSL project directory` workflow.
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

## Latest handoff status (2026-11-16)

- User-provided screenshots report full pytest 51 passed (267 seconds), the Bearer identity/tenant boundary review passed, and WSL rebuild acceptance passed: health 200 and all 11 verifier cases. These are recorded as user-reported runtime results; do not imply this session reran them.
- The user reports WSL restart exposed overlapping NAT ranges; they backed up daemon configuration, assigned Docker bridge CIDR `a separate private Docker bridge range`, added a startup wait, rebuilt the container, and re-ran 11/11 checks. Do not change WSL, dockerd, scheduled tasks, or network adapters without explicit approval.
- GitHub screenshots report the LangChain chapter was source-checked and all four additional learning chapters plus the index were pushed. The current public tree contains LangChain, LangGraph, RAG, SQL, and FastAPI chapters.
- The five learning chapters are published. Phase 14 is complete: project story, interview kit, demo runbook, requirements matrix, fault library, WSL lifecycle note, and status align with the latest user-reported evidence. The fault library lists 12 cases and clearly marks partial/unverified coverage. The user reports the two targeted regressions pass (2 passed in 4.61s); the prior 51-test suite and WSL 11/11 acceptance remain separate results. No current WSL database, checkpoint, vector store, or daemon may be damaged for fault injection.
- Phase 13: user reports clean clone, dependency install, 53 pytest passed in 18.39s, health 200, Bearer order 1001 200, and missing token 401. Do not claim this session reran those checks. Keep generated Chroma data and API keys out of the repository.
- Phase 14 is complete. User-reported WSL network recovery is recorded only in generic terms: the user adjusted daemon networking and startup readiness, rebuilt the container, and reported health 200 plus verifier 11/11. This session did not independently verify or change host settings.
- User reports the global TUNA pip simple endpoint returned 403 to pip's User-Agent; one-off Aliyun mirror override succeeded and README documents it. Do not change Dockerfile's TUNA URL until a future Dockerfile update; record an Aliyun or fallback source then.
- Do not wait for the user between routine stages. Productionization remains out of scope.

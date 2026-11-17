# Project Agent Instructions

## Project

Enterprise Support Agent V2 is a local learning/demo project that reuses V1 policy and evaluation assets. It is not a production support system. Keep V1 assets and rules intact; V2-only rules must retain explicit source/version labels.

## Current status (2026-11-17)

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
- V2.1 local demo reinforcement is implemented: Python lockfile and expanded CI; fictional requester/approver roles with self-approval denial; LangGraph logistics branch via typed HTTP client to local static mock service; Vue and handoff docs updated. User reports the WSL copy was synced, both containers are healthy, and the expanded phase 6 + V2.1 verifier passed.
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

- Phase 15 reliability hardening is complete. Phase 17 Vue demo UI is present; user reports install and live `/api/chat` flow succeeded, and local `npm run build` passed. UI changes do not require rebuilding the backend container. Keep provider API keys out of frontend; demo token is a local demo credential only. Defer productionization.

- User priority: finish the main business chain before hardening. The accepted chain is demo identity/tenant scope → FastAPI → LangGraph routing → read-only order SQL, policy RAG, or demo refund approval → safe response and run record. The main chain is complete. Phase 15 hardening is complete: GitHub Actions 55 tests in Python 3.12; Compose config, Aliyun image build, and no-key container smoke pass; corrupt checkpoint fails safely without altering the file; the user reports WSL health 200 and verifier 12/12; local four-case offline regression set passes 4/4 in 3.35s. On 2026-11-17, isolated Compose v2.39.1 checks confirmed missing `.env` fails clearly; `create_host_path: false` prevents an erroneous data path being silently created. A temporary runtime Compose probe failed with the expected `bind source path does not exist`, left the host path absent, and was cleaned up; the existing project container remained healthy. No WSL settings or project container were changed. Defer live-provider tests and productionization; continue only with V2.1 simulated demo work.
- Earlier Phase 16 productionization notes are superseded. The user explicitly requested no productionization; keep that phase paused while following the V2.1 demo-only plan.
- User's latest scope is V2.1 demo reinforcement, not productionization. Local implementation and WSL integration acceptance are complete per user report. Follow `docs/v2_1_demo_reinforcement_plan.md`. Keep all identities, orders, and logistics events fictional. Do not contact commercial courier APIs, real identity providers, or send these records to a model. Public demo tokens remain demo selectors, never credentials for real data. Build/deploy only through the established WSL `/opt/project2` workflow; never run Compose against the Windows checkout because it conflicts on host port 8000.

## V2.1 implementation handoff (2026-11-17)

- Local implementation and docs are complete. The full suite reports 65 passed; Vue build, lockfile check, Compose static config, and Python compile pass. V2.1 was committed as `c8879bf` and pushed to `origin/main`.
- GitHub Actions run 19 for `46d089a` completed successfully: locked install, full Python suite, Vue build, Compose config without secrets, Docker image build, and no-key container smoke.
- User reports the external `update_wsl_and_verify.sh` run synced `uv.lock` and source to `/opt/project2`, both containers became healthy, and the expanded phase 6 + V2.1 verifier passed. The live demo is therefore on V2.1 per user report.
- A prior local Docker image build attempt ended with daemon `unexpected EOF` during image pull; the later WSL result supersedes that attempt. Do not retry from the Windows-mounted project directory.
- User changed both Dockerfile sync commands from `--locked` to `--frozen`: the container uses the committed resolution without re-resolving against Aliyun metadata; CI retains `--locked` to detect a stale lockfile. Preserve this distinction.

1. Phases 0–11 are complete. User screenshots report the Demo Bearer scope, 51 pytest cases, and WSL verifier 11/11. Phase 12 is complete per the user's reported acceptance: both targeted not_found and fake Chat Model timeout tests passed. Phase 15 later added isolated checkpoint-corruption fail-fast coverage; Compose empty-key behavior is covered in an isolated container smoke. Missing `.env` configuration failure and erroneous bind path startup failure are now isolated and clear; real provider 429/timeout remain unverified. Phase 13 is complete per user report: clean clone, dependency installation, 53 pytest passed in 18.39s, health returned 200, Bearer order 1001 returned 200, and missing token returned 401. Phase 14 final documentation review is complete. The README, story/interview materials, demo guide, traceability matrix, fault library, and status records now reflect the user-reported clean-clone API smoke. Host startup and network notes are kept generic and do not expose machine-specific settings.
2. Phase 9 is complete. User clarified that “boot trigger” means starting on Windows user logon; the existing Logon trigger is intended and must remain unchanged. Do not stop the current daemon, start a second daemon, enable systemd, edit `/etc/wsl.conf`, modify network adapters, or restart WSL merely to test it.
3. The user's newest project brief (2026-11-16) supersedes the earlier user-led design gate: Codex is technical lead and primary developer; independently design and implement simple, maintainable solutions and continue through phases without waiting after every module. The user is the learner; teach from actual project code and do not require the user to design architecture or write core code first. Retain the learning order LangChain → LangGraph → RAG → SQL → FastAPI. Before each topic, explain the system role and current code, then provide Chinese code-linked learning material with a flow diagram, runnable examples, must-understand items, and 5–10 review questions. Run relevant tests after implementation and report actual results. Ask only for missing business facts, real secrets, external account authorization, or irreversible/destructive actions. Productionization scope is separate; updated P0 includes local demo identity/authentication, user/tenant data and minimal execution records where needed, basic safe CRUD, and explicit permission boundaries—do not overstate these as production-grade.

## Runtime and data boundaries

- Docker CLI is now available on the Windows side through a bridge (see "Docker CLI bridge" below); the daemon itself still lives inside WSL Ubuntu. Do not move Docker builds back to `the local Windows-mounted directory`; use the established WSL `the WSL project directory` workflow.
- Preserve D-drive persistence for SQLite, checkpoints, Chroma data, and policies through the existing bind mount.
- Do not expose `.env` values, API keys, or credentials in output, logs, reports, or commits. Never print the key while inspecting configuration.
- SiliconFlow/Qwen is the configured provider. The user explicitly approved sending the 14 demo questions, matched policy evidence, generated answers, and judge prompts to the configured SiliconFlow Qwen for the current evaluation. Ask before sending new datasets, personal data, or content to a different provider/model.
- Refund approval is a demo-only state transition (`approved_demo`); never add a real refund/write operation without explicit scope and authorization.
- The user plans to configure a real API for a future demo. Before the first real credential setup or API request, proactively remind the user of provider, data sent, cost/quota implications, and local `.env` setup. Never request or expose API keys in chat; do not send data to a new provider/model without approval.

## Working and documentation rules

- Keep `task_plan.md` as the checklist, `progress.md` as the chronological record, `findings.md` as durable implementation/diagnostic findings, and `docs/project_status.md` as the concise current dashboard.
- Whenever a stage, verification result, decision, or blocking dependency changes, update `AGENTS.md` current status/active work and the relevant plan/progress/status documentation in the same work session.
- Reconcile stale statements in user-facing docs when newer evidence supersedes them. Preserve old historical entries only when they are clearly labeled as historical/superseded.
- Be precise about denominators and evidence. Distinguish route accuracy, retrieval recall, citation-ID validation, semantic correctness, and end-to-end task success; do not collapse them into one score.
- Do not claim a test, API call, deployment, or runtime check unless it actually ran and its result is recorded. Keep Docker acceptance tied to the user's WSL result unless this environment can directly verify it.
- Make small, reviewable changes. Do not change `RAG_TOP_K=4` without a fresh comparison and a recorded decision.

## Docker CLI bridge (2026-11-16)

- Windows has no Docker engine, but `docker` now works from the Windows shell. Two hard facts discovered on 2026-11-16: `wsl.exe` cannot be launched from inside the Codex sandbox (exits `0xFFFFFFFF`, no output), and the sandbox **blocks non-loopback sockets** (direct TCP to the WSL IP:2375 was refused by socket policy; plain local execution and loopback are fine). Therefore the bridge is:

  `docker` → `C:\Users\17488\.local\bin\docker.cmd` → `D:\AI-Tools\docker-cli\docker.exe -H tcp://127.0.0.1:2375` → a loopback relay (`D:\AI-Tools\docker-cli\tcp_relay.py`, scheduled task `WSL-Docker-Relay`, logon trigger) → dockerd inside WSL at `<wsl-eth0-ip>:2375`.

  - dockerd listens on `tcp://0.0.0.0:2375` (added to `/etc/docker/daemon.json`, backup `daemon.json.bak-20261116`; unix socket kept).
  - The relay re-reads the current WSL eth0 IP from `D:\WSL\wsl_eth0_ip.txt` (rewritten by `/usr/local/bin/start-dockerd.sh` at every logon) **on every connection**, so reboots need no manual action. Relay log: `D:\WSL\docker_relay.log`.
  - `127.0.0.1:2375` is served ONLY by this relay; the inbox-WSL `wslhost` service does not forward dockerd's own listener (it only forwards container-published ports like 8000).
  - If a sandboxed Python subprocess cannot find `docker` on PATH, call the wrapper by full path: `C:\Users\17488\.local\bin\docker.cmd`.
  - Verified 2026-11-16 22:03 from a plain Windows shell: `docker ps` shows the healthy container, `docker compose version` = v2.39.1. Compose resolves `compose.yaml`/`.env` from the caller's cwd, so run compose commands from the project directory.
- If docker reports "Cannot connect to the Docker daemon", the daemon is not up: it is normally started at Windows logon by the existing `WSL-Dockerd-Autostart` scheduled task. Report the fact and ask before restarting WSL or starting a second daemon; do not treat it as a code failure.
- Two compose project copies exist: the WSL deployment copy at `/opt/project2` (its running container is what `docker ps` shows, port 8000) and the Windows checkout at `/mnt/d/project_2`. Compose run from the Windows checkout creates a separate compose project that will conflict with the running container on port 8000. Before `up`/`build` against either copy, state which copy is targeted and stop the other project's container first if the port is taken.

## Latest handoff status (2026-11-16)

- User-provided screenshots report full pytest 51 passed (267 seconds), the Bearer identity/tenant boundary review passed, and WSL rebuild acceptance passed: health 200 and all 11 verifier cases. These are recorded as user-reported runtime results; do not imply this session reran them.
- The user reports WSL restart exposed overlapping NAT ranges; they backed up daemon configuration, assigned Docker bridge CIDR `a separate private Docker bridge range`, added a startup wait, rebuilt the container, and re-ran 11/11 checks. Do not change WSL, dockerd, scheduled tasks, or network adapters without explicit approval.
- GitHub screenshots report the LangChain chapter was source-checked and all four additional learning chapters plus the index were pushed. The current public tree contains LangChain, LangGraph, RAG, SQL, and FastAPI chapters.
- The five learning chapters are published. Phase 14 is complete: project story, interview kit, demo runbook, requirements matrix, fault library, WSL lifecycle note, and status align with the latest user-reported evidence. The fault library lists 12 cases and clearly marks partial/unverified coverage. The user reports the two targeted regressions pass (2 passed in 4.61s); the prior 51-test suite and WSL 11/11 was the earlier verifier result; latest user report is 12/12 after synchronization. No current WSL database, checkpoint, vector store, or daemon may be damaged for fault injection.
- Phase 13: user reports clean clone, dependency install, 53 pytest passed in 18.39s, health 200, Bearer order 1001 200, and missing token 401. Do not claim this session reran those checks. Keep generated Chroma data and API keys out of the repository.
- Phase 14 is complete. User-reported WSL network recovery is recorded only in generic terms: the user adjusted daemon networking and startup readiness, rebuilt the container, and reported health 200 plus verifier 11/11. This session did not independently verify or change host settings.
- User reports the global TUNA pip simple endpoint returned 403 to pip's User-Agent; one-off Aliyun mirror override succeeded and README documents it. Do not change Dockerfile's TUNA URL until a future Dockerfile update; record an Aliyun or fallback source then.
- Do not wait for the user between routine mock-only stages. Do not add real production service integrations under the current scope.

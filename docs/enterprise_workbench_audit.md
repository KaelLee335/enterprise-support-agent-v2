# Enterprise Workbench and Langfuse Audit

Audit date: 2026-11-25. This is a code-level audit; it does not claim a new WSL deployment or a configured Langfuse account.

## Current architecture

```text
Vue 3 + Vite (single App.vue)
  -> FastAPI (Bearer demo identity)
      -> LangGraph state graph (checkpointed in SQLite)
          -> deterministic routing / order SQL / MockShop & logistics adapters
          -> Chroma retrieval -> LangChain chat model (SiliconFlow)
      -> SQLite business state, run metadata, approval tasks, webhook inbox
```

Existing integration points are FastAPI `POST /chat`, `GET /orders/{order_id}`, `GET /agent-runs/{run_id}`, approval endpoints, and the ecommerce integration endpoints. The browser already renders citations/evidence, order and logistics cards, pending approval controls, and separate role conversation buffers.

## API-to-workbench map

| Workbench area | Existing source | Audit finding |
|---|---|---|
| Chat | `POST /chat` | Real graph invocation; response has run/thread/trace IDs and evidence, but no node event timeline or streaming. |
| Approvals | `GET /approvals`, `GET /approvals/{thread_id}`, `POST /approvals/{thread_id}/decision` | Real; list is assigned-pending only and authorization is enforced server-side. |
| Order detail | `GET /orders/{order_id}`, ecommerce order endpoints | Real permission-checked detail; no scoped order list/search endpoint. |
| RAG knowledge | `rag/retrieval.py` and policy files | Real retrieval internally; no read-only knowledge/catalog or retrieval-test endpoint. |
| Dashboard | `agent_runs`, `approval_tasks` SQLite tables | No summary API; persisted runs do not contain latency, model/token usage, or node-level events. |
| Evaluation | existing JSON datasets and Markdown/JSON reports | Artifacts exist, but no authenticated evaluation API or durable evaluation-run history. OOS-v2 is observed/regression data, not blind holdout. |
| Langfuse | none | No SDK, configuration, callback, feedback API, trace export, or credentials configured. |

## Compatibility and privacy

The locked stack uses Python 3.12, `langchain-core` 1.x and LangGraph 1.x. Current official Langfuse guidance documents Python SDK v5 and the `langfuse.langchain.CallbackHandler`; v5 requires Python 3.11+, LangChain Core 1+, and Langfuse Cloud or self-hosted server v4.59+. The project satisfies Python and LangChain requirements, but the user's Langfuse server/version is unknown. Keep SDK integration opt-in and do not transmit data until the endpoint and data policy are confirmed. References: [Langfuse compatibility](https://langfuse.com/docs/compatibility), [LangChain integration](https://langfuse.com/integrations/frameworks/langchain), [v4→v5 upgrade requirements](https://langfuse.com/docs/observability/sdk/upgrade-path/python-v4-to-v5).

No evaluation request or customer data was sent to Langfuse. Telemetry must omit Bearer tokens, raw order/customer identifiers, email/phone, and full message contents by default. The public demo identities and records are fictional, but the integration must remain safe if future data changes.

## Risks and implementation choices

1. A UI-only timeline would be fabricated. Add request-scoped graph update events to the response; do not add a database migration just for events.
2. Order lists must filter in SQL by tenant plus customer ownership/service grant/assigned task. Admin must not gain implicit access to every order.
3. No latency or token usage is persisted today; display as unavailable until measured from a real source.
4. Evaluation artifacts must retain dataset labels and report provenance; never combine development and OOS metrics.
5. Knowledge upload/re-index mutates the vector store. Start with read-only catalog/preview and retrieval tests; leave write operations disabled.
6. Langfuse callbacks should attach to the existing graph invocation, remain disabled by default, and fail open. Thread ID and trace ID stay distinct; approval resume creates a linked execution rather than reusing an authorization decision from old state.

## Baseline

- Full existing pytest suite: **145 passed in 22.26s** on 2026-11-25.
- Frontend has Vue 3/Vite only; no router, component library, or chart dependency.
- No Langfuse package was installed in the project environment at audit time.
- No user-provided Langfuse server version, keys, or approval to transmit real conversations.

## Scope order

1. Design system, responsive shell, route navigation, and truthful dashboard.
2. Real chat timeline/evidence and scoped orders/approvals/knowledge pages.
3. Opt-in Langfuse trace integration and feedback API with privacy filtering.
4. Evaluation artifact center with explicit data-set provenance and no synthetic runs.
5. Local verification and README/runbook update. WSL deployment and any external Langfuse call remain separate user confirmation gates.

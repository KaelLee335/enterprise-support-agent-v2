# Enterprise Workbench and Langfuse Guide

## Local workbench

The Vue 3/Vite application uses Vue Router and a shared light SaaS layout. Run the existing FastAPI services as described in the README, then from `frontend/` run `npm ci` and `npm run dev`; open `http://127.0.0.1:5173`.

The sidebar links to Dashboard, Chat, Orders, Approvals, RAG Knowledge, Evaluation, and Observability. The identity switch changes only the existing public demo persona token; it is not real authentication. Each page calls the FastAPI API with the current Bearer selector.

| Page | Backing data | Deliberate boundary |
|---|---|---|
| Dashboard | Current caller's `agent_runs`; pending tasks assigned to current approver | Average latency and token usage are null because SQLite does not store them. |
| Chat | Existing `/chat`; real node events, evidence, answer, order/shipment details | Events arrive with the completed response; token-by-token streaming is not implemented. |
| Orders | `/orders` SQL query | SQL scopes by tenant and customer ownership/service grant/assigned approver task. Admin has no implicit all-order access. |
| Approvals | Assigned-pending and assigned-history endpoints plus checkpoint snapshot | Current approver only; decisions re-check identity and assignment on the server. The “request more information” action is not implemented. |
| RAG Knowledge | Current policy Markdown and configured Chroma retriever | Read-only. Search uses the existing Embedding service; upload/re-index is intentionally absent. |
| Evaluation | Local JSON/Markdown artifacts | No online run history table, automatic execution, or dataset mutation. Development and observed OOS results stay separate. |
| Observability | Caller-scoped local `agent_runs`; Langfuse config state | No fabricated token usage or “connected” claim. Direct trace search/linking needs a project URL/ID and has not been verified. |

The graph event list is populated by the actual `traced_node` wrapper and returned in `ChatResponse.events`; it contains node name, real status, duration, error class, and evidence IDs only. The model input, tool arguments, customer identifiers, and order payload are not copied into this UI timeline.

## Langfuse integration

The integration uses the official LangChain callback handler and one parent request observation around the existing graph invocation. The local HTTP request Trace ID and LangGraph `thread_id` remain separate; `run_id` and `thread_id` are added as trace metadata, and the thread ID is the Langfuse session ID. A resumed approval is a separate HTTP action that operates on the persisted thread/checkpoint after current assignment checks.

The dependency is locked as `langfuse` Python SDK v5. Official compatibility guidance requires Python 3.11+, `langchain-core` 1+, and Langfuse Cloud or self-hosted server v4.59+. The app is Python 3.12 and already uses LangChain Core 1.x. See [official compatibility](https://langfuse.com/docs/compatibility) and [LangChain integration](https://langfuse.com/integrations/frameworks/langchain). On 2026-11-25, the configured Langfuse Cloud project was externally verified by the user and a synthetic policy request produced a real trace containing the root request span, graph node spans, and a `ChatOpenAI` GENERATION observation. This validates connectivity and trace structure; it does not constitute deployment acceptance.

By default the feature is off. To enable it later, keep these values in the local backend `.env` only:

```dotenv
LANGFUSE_ENABLED=true
LANGFUSE_PUBLIC_KEY=...
LANGFUSE_SECRET_KEY=...
LANGFUSE_BASE_URL=https://cloud.langfuse.com
```

Do not put credentials in `frontend/.env`, Vue source, browser storage, screenshots, or Git. Compose already passes the backend `.env` using its existing `env_file` setting. Langfuse credentials belong only in the backend `.env`; the user authorized one synthetic trace validation on 2026-11-25. Keep trace export opt-in and never send real customer data in this demo.

The export masking hook replaces input/output/prompt/completion/content/message attributes and redacts common Bearer tokens, API keys, email addresses, and Chinese mobile numbers before export. It retains structural event information and model metadata. No free-text user comment is accepted in feedback; only a fixed category is sent as a categorical score after the API confirms the `run_id` belongs to the current user and tenant. Feedback fails closed when Langfuse is disabled; core chat remains independent.

The callback's model observations come from LangChain's callback path. LangGraph node-level timing remains the local graph event source; graph nodes that do not call LangChain do not become LLM observations. Token usage will appear only if the provider callback reports it; the local Dashboard does not invent a number.

## API additions

- `GET /dashboard`
- `GET /orders?q=&status=&limit=`
- `GET /agent-runs?limit=`
- `GET /approvals/history` (approver only)
- `GET /knowledge/policies`
- `POST /knowledge/search`
- `GET /evaluation/catalog`
- `GET /evaluation/artifacts/{path}` (read-only, confined to the evaluation directory)
- `GET /langfuse/status`
- `POST /feedback` (enum-only and ownership-checked)

No database migration was added. The existing SQLite schema does not persist node events, feedback, evaluation-run history, duration, or token usage. These limitations stay visible instead of being filled with mock metrics.

## Verification

The workbench API tests use isolated temporary SQLite databases. The frontend production build and full pytest suite are run locally. This guide does not claim WSL/Compose runtime acceptance; that deployment has a separate port-8000 and persistent-data boundary and needs an explicit user handoff.

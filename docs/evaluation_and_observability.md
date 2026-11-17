# 阶段 5：评估、轨迹与 Bad Case

## 执行方式与结果

- `python scripts/evaluate_agent_safety.py` 对 V1 的确定性安全标签做路由检查，结果写入 `data/evaluation/v2_agent_safety.json`。本轮 4/4 通过。
- `python scripts/evaluate_agent_routes.py` 对可映射的 V1 路由标签运行确定性路由与模拟 SQLite 工具评估，结果写入 `data/evaluation/v2_agent_routes.json`：路由 35/35、标注订单参数 8/8、工具调用 9/9、带预期结果的工具 outcome 6/6、结构化订单字段 5/5；查询前后独立临时 SQLite 订单数据不变。修复前保存在 `data/evaluation/v2_agent_routes_before_fixes.json`，当时路由为 30/35。
- 同一 RAG 标注集的 top-k 对照，每档均为 36/45 有证据标签的案例参与计分：

| top-k | Hit@k | 平均 Recall@k | 完整证据率 | 报告 |
|---:|---:|---:|---:|---|
| 2 | 97.2% | 77.3% | 58.3% | `data/evaluation/v2_retrieval_top2.json` |
| 4 | 100.0% | 86.6% | 72.2% | `data/evaluation/v2_retrieval_20261114T092303Z.json` |
| 6 | 100.0% | 89.4% | 77.8% | `data/evaluation/v2_retrieval_top6.json` |
| 8 | 100.0% | 99.1% | 97.2% | `data/evaluation/v2_retrieval_top8.json` |
- 14 条带明确答案要点的政策问答生成对照见 `data/evaluation/v2_rag_answers.json`。同一 Qwen/Qwen2.5-7B-Instruct 负责生成与 LLM-as-judge 评分，Top-4/Top-8 答案引用编号校验均为 100%；judge 要点覆盖率分别为 76.9%/71.8%、grounded 与 judge 引用支持率均为 92.9%。这些自动评分只作筛查：同模型自评出现可确认误判（例如 KB-04 Top-4 正确回答了“进液不在免费保修范围”却被判未覆盖），并在 KB-04 Top-8 回答中发现与原政策相反的事实表述。故不可将 judge 汇总数当作准确率，也不据此把默认参数改为 Top-8。
- 已逐例人工复核上述 28 个答案；结果和具体遗漏见 `docs/rag_answer_manual_review.md`。Top-8 对 KB-04 有严重政策冲突；Top-4 虽相对安全，仍漏答若干明确限制和处理阶段。人工复核未汇总成未经校准的单一百分比。
- 用户选择实现政策约束层后，完成 Top-4/Top-8 14 条用例重新生成评估，结果为 `data/evaluation/v2_rag_answers_constraints_v3.json`。28/28 引用编号校验有效；Top-4/Top-8 分别匹配 11 条约束、6/7 条执行补充或确定性兜底。为避免同模型 judge 的误判和请求停滞，本轮不跑 judge，已对输出逐条人工审阅；不报告语义准确率。之后约束层已同步到 WSL Docker，扩充版阶段 6 验收健康检查通过、11 个业务用例全部 PASS、EXIT=0；验收通过表示边界断言符合预期，不等同于 14 题语义准确率。
- 约束层按规则 ID 记录匹配/执行情况：`POL04_LIQUID_EXCLUSION` 与 `POL02_QUALITY_ROUTE` 命中时输出政策兜底；`POL02_RETURN_CONDITIONS`、`POL05_SHIPPING_AND_GUIDANCE`、`POL06_REFUND_STAGES`、`POL09_INVOICE_PRIVACY_AND_SCOPE` 在必要时补充证据明文中的关键条件。`rag_answer_constraints` 节点日志只记录约束 ID。
- 早期本机版本曾报告 47 项 pytest，后续干净克隆 53 项通过（均为历史版本，不代表当前 HEAD）。V2.1 requester/approver 和 mock logistics 改动后，本机全量回归为 65 passed；WSL 两容器集成验收由用户报告已通过，详见项目状态文档。

## 追踪和隐私

每个 HTTP 请求返回 `X-Trace-ID`，`POST /chat` 同时返回 `trace_id`。日志以 JSON 输出到标准输出，记录 HTTP 和 LangGraph 节点开始/结束、耗时、租户、路由、订单查询参数及结果摘要、检索政策编号/距离、引用检查、审批状态和错误类型。输入只以最长 500 字符预览记录，并脱敏常见 API Key/Bearer token、邮箱和中国手机号；模型完整回答与凭据不写入日志。异常只向客户端返回异常类型和安全提示；服务端日志保留异常栈供本地排障。预期的审批中断记为 `node_pause`，不作为错误。

## Bad Case 与处理

| 案例 | 观察 | 处理/剩余项 |
|---|---|---|
| SEC-01：声称管理员并把订单直接改成已退款 | 初版规则未将“改成已退款”识别为写操作 | 增加明确的状态伪造写操作拒绝规则；回归断言通过，安全路由评估 4/4 |
| KB-09、NA-02：专票时限保证 | Top-4 召回 POL-09，但遗漏人工协助边界 POL-10；Top-8 对照已缓解 | Top-8 可召回更多必要证据；rerank 不能找回候选集之外的文件 |
| NA-03：未来新品上市时间与价格 | Top-4 未召回所需 POL-01；Top-8 对照已缓解 | 候选数增大改善该评估集的召回，但仍需核对答案质量和上下文成本 |

### 可复现的修复前后证据

- **SEC-01 写操作边界（V1/Dify 历史案例）**：初版将“把订单直接改成已退款”路由错误；补充状态伪造识别后，当前安全路由集为 4/4。逐例记录见 `data/evaluation/v2_agent_safety.json`，脚本为 `scripts/evaluate_agent_safety.py`。这说明该标注集覆盖到的规则回归通过，不代表对任意自然语言写操作均安全。
- **订单/意图路由（确定性 V2 路由）**：修复前报告 `data/evaluation/v2_agent_routes_before_fixes.json` 为 30/35，修复后 `data/evaluation/v2_agent_routes.json` 为 35/35；调用参数与工具结果是不同分母，分别报告，不合并成总成功率。
- **政策回答 Bad Case**：约束层 Top-4/Top-8 逐例数据在 `data/evaluation/v2_rag_answers_constraints_v3.json`，人工审阅在 `docs/rag_answer_manual_review.md`。引用 ID 校验不代表语义正确；阶段 1 保留已有人审案例，不重新调用模型生成前后对比。

Top-8 对照显著降低了上述多证据漏召回；相较 Top-4，平均 Recall 提升 12.5 个百分点、完整证据率提升 25.0 个百分点。但本轮生成对照没有证明 Top-8 最终答案更好，且发现一条明显的证据冲突回答；更大的上下文也会带来更多输入 token 和生成开销。应用默认保持 `RAG_TOP_K=4`。后续若调整，应先修复和复核生成提示，并使用独立人工标注/可靠裁判做语义质量与成本权衡。

路由报告只为 35 条有可映射路由标签的用例计分；订单参数只统计有明确 `tool_args` 的 8 条，工具结果与结构字段也只对有对应标注的样例计分。空路由标签的 10 条未臆造标准。上述模拟 SQLite 结果不是模型回答语义评分，也不等于完整 Agent 任务成功率。`approval_required` 仅代表演示审批暂停，不代表退款执行。当前记录了单次节点耗时，但未形成稳定的 P50/P95 延迟基准。检索结果与 LLM 回答质量仍需结合来源和人工复核。多/非法订单号、隐私索取和提示注入规则已通过本机回归及用户在 WSL 容器运行的阶段 6 断言脚本。

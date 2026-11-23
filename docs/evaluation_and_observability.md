# 阶段 5：评估、轨迹与 Bad Case

## 执行方式与结果

### 独立样本外 RAG 检查（2026-11-21）

- 新增约 15 条的独立集 `data/evaluation/oos/rag_oos_v1.json`，包含口语同义表达、组合条件、多意图、无答案/范围边界和模糊澄清。问题没有从原 45 条开发集复制；原集文件未修改。
- 使用命令 `python -m tests.oos.run_oos` 独立执行，沿用当前 Chroma collection、`BAAI/bge-large-zh-v1.5`、`Qwen/Qwen2.5-7B-Instruct`、现有回答 Prompt/约束和 Top-K=4。生成时实际使用的 evidence 用于检索计分，不另建索引或改变业务 API。
- 初版规则初筛为 **66.7%（10/15）**、拒答边界 **75.0%（3/4）**、引用标签匹配 **93.3%（14/15）**；报告列出 5 个 Bad Case。复核发现，模型会把内部约束 ID 当作引用输出，运费规则还会把无理由退货责任附加到质量故障回答。
- 最新真实报告（2026-11-21 11:42 UTC）为 Hit@4 **100.0%**、Macro Recall@4 **95.6%**、答案规则项 **93.3%（14/15）**、拒答/范围边界 **100%（4/4）**、引用标签与召回来源匹配 **100%（15/15）**。只剩 OOS-05：Top-4 未召回 RET-01/QUA-01，因而答复不能完整说明定制商品的无理由退货例外。
- 前后报告保存在 `data/evaluation/oos/rag_oos_v1_report_before_style.md` 和当前报告。检查规则已补充同义表达，OOS-11 的相关来源标注也更正为澄清所需的 POL-02；所以前后比例仅作方向参考，并非严格同口径准确率比较。
- 代码改进包括：Prompt 指导先回答核心、避免复述和无关追问；约束 ID 不再进入模型上下文；模糊退货资格先询问签收时间、问题类型和商品状态；运费/退款/发货约束按用户问题补充；明确的维修时效、超出服务范围、订单完成后售后资格使用短而有据的答复。约束补充与原答复顺接并避免重复引用；直接问“明天能否到”时明确说明不能保证明天送达。规则检查忽略中文数字间空格，避免把“3 至 5”误判为内容缺失。Top-K 保持 4，原 45 条和业务 API 未修改。
- 不使用 LLM-as-a-Judge。来源 ID 与答案规则项检查不等于事实蕴含正确；需要人工审阅剩余 OOS-05。OOS 结果与原开发集分开。
- 单元测试覆盖检索计分、空标签、Mock 执行/报告、澄清、约束边界和引用标签；全量 pytest **105 passed / 15.00s**。Mock 测试不计入真实 OOS 指标。
- **部署验收（历史用户报告）**：较早版本已同步到 WSL，三容器 healthy，阶段 6 与 V2.1 验收全 PASS（EXIT=0）。该历史版本不含 2026-11-22 新增的复合查询扩展；当前代码是否部署以用户后续同步和验收为准。

### 2026-11-22 OOS-v1 回归与复合问题检索修复

- 在 OOS-05 暴露的问题上加入窄范围查询扩展：当问题同时含定制商品、质量问题、寄回/运费三个条件时，给检索器补充对应业务规则词项；回答仍使用用户原问题，Top-K 保持 4。它不改变政策库、向量库或业务 API。
- 使用当前 Chroma、`BAAI/bge-large-zh-v1.5`、Qwen 和 Top-K=4 重跑 OOS-v1。报告 `data/evaluation/oos/rag_oos_v1_report.md`：Hit@4 **100% (15/15)**、Macro Recall@4 **100%**、答案规则初筛 **100%**、拒答/范围初筛 **100%**、引用标签匹配 **100%**；规则筛查 Bad Case 0。OOS-05 已参与修复设计，因此这些数字是回归结果，不是 blind holdout，也不是语义准确率。
- 额外人工查看 OOS-05 的 Qwen 答复时，发现它追问“照片或视频”作为凭证形式；现有政策只要求提供质量问题凭证，没有限定照片/视频形式。引用标签和当前规则筛查未捕获此细节，需人工决定是否加一道禁止擅自指定凭证格式的答复约束。
- 新的 15 条 OOS-v2 案例已由用户于 2026-11-23 审核通过，位于 `data/evaluation/oos/rag_oos_v2_holdout.json`。HOLDOUT-04 刻意针对此前已观察到的无依据凭证格式追问，因此不能把整套说成完全盲测。独立运行命令为 `python -m tests.oos.run_oos --dataset data/evaluation/oos/rag_oos_v2_holdout.json`；在额外的外部数据发送授权前不调用模型。运行后这批数据整体成为已观察集。
- 用户随后明确授权向已配置的 SiliconFlow/Qwen 发送这 15 个问题、检索证据和模型答复。真实运行完成于 2026-11-23 04:25 UTC，独立报告和 ledger 分别写入 `data/evaluation/oos/rag_oos_v2_holdout_report.md` 与 `data/evaluation/oos/rag_oos_v2_holdout_bad_cases.json`。
- 结果：Hit@4 **100%（15/15）**、Macro Recall@4 **93.3%**、答案规则要点初筛 **20.0%（3/15）**、拒答/范围词面初筛 **0%（0/6）**、引用标签与召回来源匹配 **100%（15/15）**；筛出 12 个候选 Bad Case，其中 GENERATION 10、RETRIEVAL 2。
- **解释限制：**规则词面检查很严格，0% 的拒答初筛不等于 6 个回答全都不安全；例如部分答复表达了不能执行或需要人工核验，但没有命中预设短语。相反，HOLDOUT-04 确有模型编造“必须上传视频/购买凭证”的迹象。12 个案例要逐一人工审查，区分真实业务错误、规则检查误报和证据标注是否过宽；目前不据这批自动标签改 Prompt 或政策约束。
- Codex 初步逐例分诊已记录在 `data/evaluation/oos/rag_oos_v2_manual_triage.md`，其中 3 项为明确回答问题候选、2 项为无依据附加内容候选、4 项为词面检查误报、2 项为来源标注可能过宽、1 项为回答不完整候选。此为初步判断，ledger 中最终人工根因字段仍为 pending。
- 用户报告早前冲突处理版本的容器 smoke、Phase 6 和 V2.1 verifier 全通过。用户要求当前部署保持不变，待本机改动提交后再同步；本轮未操作 WSL/Compose。

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

OOS runner 同时生成 `rag_oos_v1_bad_cases.json`，用于把“自动初筛”和“人工定因”分开记录。每条记录保留原始问题、预期与实际回答、召回来源及距离、未匹配引用、初筛原因与建议；`root_cause_review` 初始为 pending，`remediation` 初始为 not_started。自动分类只表示现象线索，不是已确认根因。人工复核类别限定为 DATA、CHUNK、RETRIEVAL、GENERATION、BUSINESS、ABSTENTION，并记录复核者、结论、修复引用和回归测试证据。运行器不会自动填入根因或修改业务规则。

`tests/test_rag_boundaries.py` 是离线特征测试：证明“合法引用编号”检查不会单独识别无关证据、矛盾证据或假模型对指令样式证据的错误承诺。它们不访问 SiliconFlow，不代表真实模型安全结论，也不把这些行为判为验收通过。改变低相关拒答或冲突回答策略前，需要校准当前 Chroma 的真实距离并确认业务边界。

### 距离校准（探索性）

`python scripts/calibrate_rag_distance.py` 使用当前 Chroma 与配置的 Embedding API 计算 24 条虚构/合成探针的全库排序距离，只调用 Embedding，不调用聊天模型、不写入 Chroma/SQLite，也不更改回答行为。2026-11-22 报告 `data/evaluation/oos/embedding_distance_calibration_v1.md` 显示 12/12 可回答目标进入 Top-4；可回答目标距离 0.6516–1.1380 与无答案最近距离 0.9072–1.1817 重叠明显。该样本不能支撑安全的统一阈值；距离不是概率，也不能证明答案由证据蕴含。任何行为变更须另行验收。

经用户确认，当前只增加了保守的显式冲突处理：若检索证据中的句子在删除“不/没/未”后完全一致、仅一条含否定标记，并与问题共享明确主题词，则跳过模型生成，返回带冲突来源编号的人工核验提示。不同范围、例外条款、不同退款阶段及无关主题不会仅因主题相近而标为冲突。该规则不识别语义改写、数字变化或隐含矛盾；不能视为通用矛盾/蕴含检测。测试覆盖直接极性反转和已知非冲突对照。

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

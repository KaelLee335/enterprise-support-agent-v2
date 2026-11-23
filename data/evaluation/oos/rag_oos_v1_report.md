# RAG 样本外测试报告

- 数据集：`rag_oos_v1`（与45条开发集分开）
- 运行时间：2026-11-22T14:57:51.604416+00:00
- 案例：15；分类：{'colloquial_synonym': 5, 'combined_conditions': 4, 'multi_intent': 2, 'no_answer': 2, 'ambiguous_clarification': 1, 'out_of_scope': 1}
- 独立性说明：OOS-05 已用于定制商品复合问题的检索查询扩展迭代；本次是回归复测，不应视为完全未见盲测结果。
- Embedding：BAAI/bge-large-zh-v1.5；LLM：Qwen/Qwen2.5-7B-Instruct；Top-K：4
- 语义正确性由规则要点初筛并需人工审核；无 LLM judge。

## 指标

- Hit@4：100.0%（15条有相关文档标注案例；只要命中一个来源即算命中）
- Macro Recall@4：100.0%（仅在有相关来源标注案例上逐题算召回再宏平均）
- 答案规则要点通过率：100.0%（15条；只是规则初筛，不等于语义正确率）
- 无答案拒答规则通过率：100.0%（4条；人工仍需确认是否合理）
- 引用标签与本次检索来源匹配率：100.0%（只检查方括号编号是否属于召回来源，不代表事实蕴含已验证）
- 原开发集历史指标：Hit@4 100%、Recall@4 86.6%（36条有标签案例）；与本报告不合并。

## Bad Case 分类

本节是自动规则初筛，标签和原因均为待复核假设，不代表已确认根因。
案例数：0；初筛分类计数：{}

## 失败案例

本次规则初筛未发现 Bad Case；答案仍需人工审核。
## 解释与后续

自动初筛只描述观测到的失败表现。DATA、CHUNK、RETRIEVAL、GENERATION、BUSINESS、ABSTENTION 中的最终根因需人工对照知识库、权限和业务规则确认。
每条失败的结构化记录写入 `rag_oos_v1_bad_cases.json`；请在其中填写 `root_cause_review`，并记录 `remediation` 与回归证据。

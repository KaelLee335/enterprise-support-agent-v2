# 故障案例库（阶段 12）

本库区分已有覆盖、部分覆盖和待验证。待验证项不得在演示材料中说成通过。

## 状态总览

| # | 故障 | 主要层 | 当前状态 |
|---:|---|---|---|
| 1 | 缺少订单号 | API/路由 | 已覆盖：澄清，不创建审批 |
| 2 | 格式错误或多个订单号 | 路由 | 已覆盖：澄清 |
| 3 | 伪造租户 Header / 跨租户访问 | 身份/SQL/API | 已覆盖：租户由 token 映射，越权 404 |
| 4 | 当前租户下订单不存在 | 订单节点/SQL | 随机 not_found API 测试由用户报告通过（1/1） |
| 5 | RAG 无证据 | 检索/生成 | 已覆盖：不调用模型，说明无法确认 |
| 6 | 检索排序或回答违反政策 | RAG 生成 | 部分覆盖：人工审阅及约束规则；独立语义验证不完整 |
| 7 | 隐私请求、提示注入、伪造引用 | 路由/安全 | 已覆盖：拒答与 WSL 验收 |
| 8 | SQLite 不可用 | 数据层/API | 已覆盖：安全错误测试 |
| 9 | Embedding/检索服务失败 | RAG 外部依赖 | 注入式检索异常有测试；真实超时/限流未验证 |
| 10 | Chat Model 超时、限流或不可用 | 生成层 | 假 timeout 单测由用户报告通过（1/1）；真实供应商限流未测试 |
| 11 | Checkpoint 缺失、损坏或恢复冲突 | LangGraph 持久化 | 隔离损坏文件测试通过：启动 fail-fast、原文件字节不变、业务 DB 未初始化；真实备份恢复仍未验证 |
| 12 | Compose 缺少 Key 或路径错误 | 配置/容器 | 缺少 `.env` 的隔离 `compose config` 明确报文件不存在；无 Key 降级测试通过；错误 bind 路径临时运行态验收返回明确错误且未创建宿主目录 |

## 统一定位流程

1. 用响应的 trace ID 找到同一请求的 HTTP 与节点日志。
2. 判断层次：路由、身份/租户、SQL、检索、生成、checkpoint 或容器配置。
3. 先核对可观察事实：intent、run 状态、错误类型、证据 ID、checkpoint thread、容器挂载；不要先推断模型“理解错了”。
4. 用临时数据库、假模型、临时 checkpoint 或隔离 Compose 配置重现。不要在用户当前 WSL 数据库、checkpoint、向量库或运行容器上注入损坏。
5. 修复后补精确断言，注明测试范围；区分代码单测、真实外部服务和 WSL 验收。

## 重点案例

### 1–3. 输入与授权边界
- **症状：**缺订单号、格式错误/多个订单号、客户端伪造 X-Tenant-ID 或尝试访问其他租户数据。
- **根因：**参数缺失/歧义，或把客户端声称的租户误当身份。
- **定位：**检查 intent/clarify_reason、Bearer 令牌映射、最终 SQL 的 tenant 条件。
- **处理：**缺参/歧义返回澄清；tenant 只由令牌映射；数据查询始终限定 tenant。
- **证据：**tests/test_api.py 的路由、伪造 Header、越权 run 测试；用户截图报告 51 项 pytest 和 WSL 11/11 通过。

### 4. 当前租户下订单不存在
- **症状：**随机订单号没有记录，系统不能编造商品或状态。
- **根因：**SQL 查询返回 None。
- **定位：**区分当前租户随机 ID 与另一个租户的真实 ID，检查响应是否只泄露必要信息。
- **处理：**保持租户限定查询，补当前租户随机订单 ID 的明确 API 断言。
- **状态：**当前租户随机 not_found API 测试由用户报告通过。

### 5–6. RAG 无证据或答案违反政策
- **症状：**空召回仍生成，或召回/生成遗漏关键规则、和政策矛盾。
- **根因：**知识库没有证据、排序不佳、上下文干扰或模型没有遵循证据。
- **定位：**分别检查 retrieved source IDs、约束匹配/执行记录、引用 ID 和答案语义。
- **处理：**空证据不调用模型；高影响边界用版本化 V2 约束；结合人工 Bad Case 复核，不能把引用合法当语义正确。
- **证据：**tests/test_rag.py 空召回测试；docs/rag_answer_manual_review.md；data/evaluation/v2_rag_answers_constraints_v3.json。独立语义蕴含自动验证仍不完整。

### 7–8. 隐私/注入与数据库不可用
- **症状：**用户索取私人联系信息、要求忽略规则/伪造引用，或 SQL 连接异常。
- **根因：**不可信输入试图覆盖规则；数据库文件/权限/连接异常。
- **定位：**用 trace ID 查请求与异常类型；输出不能包含原问题、Key、SQL 或本机敏感路径。
- **处理：**确定性拒答与安全错误映射；在临时目录注入故障。
- **证据：**tests/test_api.py 的 adversarial 路由与 order database failure 测试；WSL 11 项验收。

### 9–10. Embedding 与 Chat Model 失败
- **症状：**检索无法完成，或模型超时/429/5xx。
- **根因：**网络、服务商限流、凭据或模型配置异常。
- **定位：**区分 Embedding 与 Chat Model 调用；记录安全的错误类型，不记录 API Key 和响应体。
- **处理：**Embedding 使用 fake 注入测试；下一步用假 Chat Model 抛 TimeoutError/429，断言安全答复、run 状态 failed、无敏感细节。真实云端超时不作为单测。
- **状态：**检索异常有注入测试；假 Chat Model timeout 单测用户报告已通过（全量 53 项），真实服务故障未演练。

### 11. Checkpoint 恢复失败
- **症状：**审批 thread 不存在、状态不是 pending、checkpoint 文件损坏，或重复提交决定。
- **根因：**thread_id 丢失、SQLite 文件/状态异常或请求重复。
- **定位：**检查 thread_id、snapshot.next、approval_status 及 SQLite 错误类型。
- **处理：**重复审批用 409；损坏文件只在临时 checkpoint 上注入；不触碰现有 WSL checkpoint。
- **状态：**正常恢复与重复冲突已有覆盖；新增临时损坏文件测试确认启动时拒绝并保留文件，GitHub Actions 54 项通过。未模拟真实运行数据库损坏或备份恢复。

### 12. Compose 缺 Key 或路径错误
- **症状：**健康检查正常但 RAG 不工作，或 `.env` 缺失导致 Compose 配置失败；数据目录路径错误会让容器因 bind mount 源不存在而启动失败。
- **根因：**本机未从模板创建 .env、Key 缺失、PROJECT_DATA_DIR 错、向量库未建或 bind mount 不对。
- **定位：**分别检查 Compose 配置、`PROJECT_DATA_DIR`、容器 health、Embedding 配置和 `docker inspect` 的 data mount；health 200 不等于 RAG 正常。
- **处理：**仅在本机 .env 配置 Key；向量索引在首次部署前建立；用隔离目录验证配置错误路径。
- **证据/状态：**缺 Key 的 Embedding 构造路径有单测；隔离 `compose config` 已验证缺 `.env` 会以非零状态明确报错，错误数据路径不会在配置解析时创建目录。Compose 已设置 `bind.create_host_path: false`。唯一临时项目的运行态演练返回 `bind source path does not exist`、没有创建宿主路径；清理后原项目容器仍 healthy。

## 阶段状态

- 用户报告：新增的随机 not_found API 与假 Chat Model timeout 回归均通过，2 passed in 4.61s。未重跑完整 51 项套件，也未操作 WSL/Docker。
- 阶段 12 按用户确认的验收条件完成。阶段 15 隔离 checkpoint 损坏用例已通过；Compose 缺 `.env` 配置失败、缺失 bind 路径防误建与运行态启动错误均已覆盖。真实供应商限流仍未验证。
- 阶段 13 已由用户验收：干净克隆的依赖安装、全量 53 项测试及 health/order/auth API smoke 均报告通过；这些结果来自不同验收步骤，未由本会话复跑。


## 阶段 15 自动验证记录

- `.github/workflows/tests.yml` 对代码/配置变更运行 Python 3.12 全量 pytest、Compose 配置、Docker 镜像构建和无 API Key 临时容器 smoke。
- 用户代码 `b797bda` 对应的 GitHub Actions 运行成功：55 passed in 3.99s，Compose 配置、镜像构建和容器 smoke 均通过。临时容器只用空 Key 与模拟数据；没有调用真实模型或操作 WSL。

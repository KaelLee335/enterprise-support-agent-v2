# V2.1 电商集成评估记录

更新时间：2026-11-18。评估按规则/API/Agent 路由/前端构建分别报告，不将不同指标合并成一个“准确率”。

## 当前实测

| 范围 | 数据/方法 | 结果 | 解释 |
|---|---|---:|---|
| pytest 全量 | 项目 `.venv`，独立 basetemp，关闭 pytest cache provider | 93 passed / 12.26 秒 | 覆盖历史功能与当前 MockShop/Adapter/权限/幂等/Webhook 回归 |
| Vue production build | `frontend` 下 Vite 构建 | 通过 | 只验证前端静态编译，不代表浏览器/API 端到端验收 |
| 原 Agent 路由集 | 35 条明确路由标签 | 35/35 (100%) | 扩展实现后重新运行；评估产物 `data/evaluation/v2_agent_routes.json` |
| 订单参数评估 | 8 条已标注订单参数 | 8/8 (100%) | 同轮实测；route errors 0，DB unchanged |
| 工具 outcome / 业务订单案例 | 原标注子集 | 6/6、5/5 | 由路由评估脚本报告；不代表 MockShop 新申请流程语义准确率 |
| MockShop API / Adapter | pytest 固定 fixture、Fake transport | 通过（计入 93 项） | 覆盖状态映射、响应校验、错误归一、资格和申请 API |
| Webhook | pytest 签名、payload、重复/冲突 ID、租户归属、旧事件 | 通过（计入 93 项） | 覆盖本地规则，不代表真实平台签名互通 |
| Compose/WSL runtime | 本轮未部署 | 未验证 | 需用户按 `/opt/project2` 既有流程同步、重建和实测 |

测试命令：

```powershell
.venv\Scripts\python.exe -m pytest -q --basetemp=.pytest-tmp-v21 -p no:cacheprovider
```

## 测试边界

- **规则与 API 测试**验证确定性输入、身份权限、状态映射、幂等和错误行为。
- **Agent 路由评估**比较意图标签与订单参数，不等同于回答质量或完整业务流程成功率。
- **RAG 检索指标**（Hit@4、Recall@4）只描述证据召回，不证明答案事实正确；答案还需人工审阅。
- **端到端容器演示**需要真实启动 API、mock-shop 与 Vue，并验证请求流；本机 Vue build 和 FastAPI TestClient 都不能替代它。
- **未验证项**：真实电商服务兼容、真实 webhook 供应商签名格式、真实外部平台延迟/重试和真实退款。项目范围明确不接这些服务。

## 后续验收

1. 用户运行既有 WSL 同步脚本，部署到 `/opt/project2`，确认两个 Compose 服务 healthy。
2. 经 Swagger/UI 验证店铺 A、店铺 B 各自能读自有虚构订单，不能读取对方订单。
3. 验证请求人先检查资格、明确提交后看到 `pending_demo`；审批/平台退款不会被声称完成。
4. 发送合法、重复、伪造签名和旧时间模拟 webhook，观察事件幂等与状态保护。
5. 将实际容器结果补记在本页，不把计划中的检查提前标为通过。

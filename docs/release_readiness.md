# 阶段 7：发布就绪与可复现交接

## 目标

让新环境从受版本控制的源码、安全的本机配置和 README 步骤启动项目。此阶段只准备本地仓库和部署说明，不代表已经发布到 GitHub，也不改变当前 WSL 服务，直到用户执行重建。

## 已处理

- Docker 构建不再要求本机生成、且不会随 Git 发布的 `data/vector_store/`。首次部署前通过 `scripts/index_policies.py` 生成索引；Docker runtime 从持久化的数据目录读取。
- Compose 使用 `PROJECT_DATA_DIR` 选择持久化目录。空值保持当前 `/mnt/d/project_2/data` 默认；其他环境可在忽略的本机 `.env` 设置路径。
- `.gitignore` / `.dockerignore` 排除密钥、本机数据库、向量库、评估运行副产物、虚拟环境、测试缓存和构建产物。
- README 已说明首次生成向量索引和覆盖数据目录的方法。
- 本地 Git 仓库已初始化；当前不创建提交，也不推送到远端。

## 验收清单

- [x] 核实 `.env`、数据库/WAL、向量库、虚拟环境、pytest 临时目录和 egg-info 均命中 `.gitignore`；`.env.example` 未被忽略。
- [x] 新克隆不含向量库时 Dockerfile 构建输入仍完整；用户 WSL 实际构建成功。
- [x] 用户 WSL Compose 重建成功；`docker inspect` 确认 `/mnt/d/project_2/data -> /app/data`，验证数据路径配置生效。
- [x] WSL 容器 healthy，11 个阶段 6 用例全部 PASS，EXIT=0。
- [x] 审阅 `git status` 待跟踪列表，均为预期项目源文件/文档/政策与评估目录；未提交或发布。

## 边界

- WSL Docker 构建由用户环境执行；当前 Windows 会话不能直接控制已运行的 WSL daemon。
- 不对远端 GitHub 创建仓库或推送代码。
- 向量索引和订单/checkpoint 数据是运行时资产，不提交版本库；新环境依 README 重建索引。

## 阶段 8：GitHub 公开交付（已规划，等待连接）

- 用户已选择新建公开仓库。
- 建议仓库名：`enterprise-support-agent-v2`；说明：`Code-first enterprise after-sales support agent demo with FastAPI, LangGraph, and RAG.`
- 发布前仍需再次检查将提交的文件，尤其扫描误放入源文件/评估报告的 Key、数据库和本机配置。
- 空白公开仓库已创建：[KaelLee335/enterprise-support-agent-v2](https://github.com/KaelLee335/enterprise-support-agent-v2)。本地文件忽略规则和令牌格式扫描已核查，初始本地提交已创建；作者使用 GitHub noreply 地址。下一步配置 origin、推送并核对远端。未写入凭据。

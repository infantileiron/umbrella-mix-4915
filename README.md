# 补雨修伞 · 跨网点工时差额拆解

补雨修伞的北埠、南桥两个街区网点用逐票工序和返修计时，判断平均每票多花的时间有多少来自接单构成，有多少来自拟合工时系数。演示中两个网点共有 8 位修伞师傅，运营方每周核对一次雨后返修。

## 工作场景

上游是各网点的台钳工票。值班人员原先分别登记有效作业分钟、换骨和布面修补，再由运营在周报 Excel 中手工合并。返修任务轻重不同，直接比较周均值容易误判。更换对照口径时，旧表中很难追溯曾用的日期和系数。超出对照网点常见工作量的工票也容易混在均值里。

分析员在工作台登记或修订单票、另存对照方案、提交计算。业务方依据守恒校验和外推提醒写改进草案。发布后，观察员可查看结果、草案和导出，供两点周会复盘。

| 角色 | 账号 | 演示口令 | 主要页面与权限 |
|---|---|---|---|
| 业务方 `owner` | `owner` | `RainOwner2026!` | 读台账、方案、所有运行和导出，保存改进草案并发布 |
| 分析员 `analyst` | `analyst` | `RainAnalyst2026!` | 录入与修订工票、创建比较方案并另存版本、运行、读取和导出，查看草案 |
| 观察员 `observer` | `observer` | `RainView2026!` | 读台账和方案，只读已发布的运行、草案与导出 |

## 一天的工作剧本

1. 08:40，程砚把 `BE-W46-01` 与 `NQ-W46-01` 在台账中分别核为 15 和 28 分钟，查看截至 11 月 15 日两点各 32 张返修工票。
2. 08:50，录入 11 月 16 日的 `NQ-W47-01`，换骨 2 根、布损 1 处、有效作业 27 分钟。它进入台账，等下一周比较窗口纳入。
3. 09:05，选 `RAIN-W46` 的 v1，日期为 2026 年 11 月 9 至 15 日，比较方向为南桥减北埠，每点至少 12 张，用北埠系数计算构成差。
4. 09:10，提交运行。计算正常结束后，结果中应看到南桥 41.00、北埠 24.50 分钟/票，实际差 16.50，构成差 5.00、系数差 11.50 分钟/票。
5. 09:25，另存 v2，将构成差系数改为来自南桥。复算实际差仍是 16.50，构成差变为 7.00、系数差变为 9.50 分钟/票。v1 仍可单独运行。
6. 09:40，查看 v1 的外推提醒。南桥有 14/32 张工票至少一项超出北埠逐项观测范围，换骨和布损分别有 8 张越界。下载相应的 `umbrella-<运行ID>.csv` 和 `umbrella-<运行ID>-snapshot.json`。
7. 10:00，陆缃复核后把「先复核越界工票的伞骨与布面记录，再做同类工序对照，周五复盘」保存为草案并发布。
8. 10:15，季禾登录查阅刚发布的差额和草案，用导出准备两点周会材料。

启动时的模拟数据是北埠 `BE-W46-01` 至 `BE-W46-32`、南桥 `NQ-W46-01` 至 `NQ-W46-32`，各覆盖 4 档换骨、4 档布损和 2 种开合机构状态的全组合。seed 还包含三账号与 `RAIN-W46` v1。按自然键幂等插入，重复运行保留工票修订值和已存在版本。

## 核算口径

- 一行是一张返修工票，`minutes` 是有效作业分钟。等待干燥、等件、排队和开门时长均不计入。布面损伤以独立修补点数录入，开合机构按照是否需修记为 1 或 0。日期范围两端都包含。
- 对比较网点 A 和对照网点 B 分别做含截距的 OLS。`x = [1, 换骨根数, 布损处数, 开合机构需修]`，系数分别为 `βA`、`βB`。各票在本组拟合和均值中等权。
- 默认基准是 B。构成差为 `(x̄A − x̄B)·βB`，系数差为 `x̄A·(βA − βB)`，反事实均值为 `x̄A·βB`。选择 A 基准时，构成差为 `(x̄A − x̄B)·βA`，系数差为 `x̄B·(βA − βB)`，反事实均值为 `x̄B·βA`。逐项相乘给出表内贡献，截距的构成差恒为零。两项之和与 `ȳA − ȳB` 的绝对误差须不超过 `1e-8` 分钟/票。
- 外推按使用该系数网点的逐工序最小值和最大值核对。每一项分别计数，总越界率按至少一项越界的反事实网点工票去重。结果同时保留样本数、回归秩、条件数、R² 和残差 RMSE。
- 样本低于方案阈值、设计矩阵不满秩和快照校验失败进入待补正状态。样本达标且总差为 0 时照常输出有符号的两个贡献，避免用零总差作百分比分母。
- 运行提交时封存了方案版本、按自然键排序的工票、每条修订号和方法版本。快照 JSON 的原始字节 SHA-256 可与运行详情对照。CSV 保留完整精度、逐项系数、诊断、版本及当前复核状态。JSON 与 CSV 通过页面下载。

方法出处为 Ben Jann, *The Blinder–Oaxaca Decomposition for Linear Regression Models*, The Stata Journal 8(4), 2008, doi:10.1177/1536867X0800800401。

## 启动与开发

```bash
cp .env.example .env
docker compose up --build --wait
docker compose exec -T backend python -m scripts.seed_demo
```

浏览器 `http://127.0.0.1:18279`，直连 API `http://127.0.0.1:19279`，健康检查 `/health`，API 文档 `/docs`。MySQL 从 `127.0.0.1:17779` 接入。Redis 保持在 Compose 网络内。数据、Redis 和快照文件分别存命名卷。常规停止用 `docker compose down` 保留卷。

| 部分 | 技术与位置 |
|---|---|
| 前端 | 原生 HTML、CSS、JavaScript ES modules，`frontend/src`。Nginx 代理 `/api/`，支持 SPA 路由 |
| API | Python 3.11、FastAPI、PyMySQL、JWT，`backend/src` |
| 计算 | NumPy SVD 最小二乘，`backend/src/services/decomposition.py`，由 `src.worker` 调度 |
| 持久化 | MySQL 8.0 工票、方案、队列、草案与审计，`backend/migrations/001_initial.sql` |
| 唤醒和导出 | Redis 7 唤醒，MySQL 任务队列为事实来源。worker 用共享卷原子落盘快照 |
| 演示数据 | `backend/scripts/seed_demo.py` 和 `backend/scripts/seed_cases.py` |

本地开发可用 `python3.11 -m venv .venv` 后在 `backend/` 安装 `requirements.txt`，将 `DB_HOST`、`DB_PORT`、`REDIS_URL` 设为开发 MySQL 和 Redis，先执行初始 SQL，再执行 `python -m scripts.seed_demo`、`uvicorn src.main:app --reload --port 8000` 和 `python -m src.worker`。前端需要支持 `/api/` 代理的静态服务器。批次验收统一从批次目录执行 `bash scripts/verify-project.sh gb-5210`。

`.env` 管理 `COMPOSE_PROJECT_NAME`、三端口、`NETWORK_SUBNET`、四项 MySQL 配置、`JWT_SECRET` 和 `SEED_DEMO`。默认数据库/Redis 主机名为 `db`/`redis`，也可用 `DB_HOST`、`DB_PORT`、`REDIS_URL` 覆盖本地开发连接。`EXPORT_DIR` 默认为 `/app/artifacts`，API 与 worker 共用。完整 `.env` 由 `.env.example` 生成。

后端共享枚举位于 `backend/src/constants/domain.py`，对应 SQL 枚举位于迁移文件。`Role` 用在登录授权、草案读写和运行可阅范围。`Branch` 用在工票和方案入参、结果拟合与外推诊断。`Basis` 用在方案入参和分解分支。`RunStatus` 用在运行路由、导出、worker 与草案前置状态。`DraftStatus` 用在草案发布和可阅控制。前端镜像枚举与工序名称在 `frontend/src/constants/domain.js`，分别用于侧栏身份、台账筛选、方案与运行表，以及结果和草案状态。

## 局限

演示是描述性点估计，系数差可能包含未纳入模型的工具、人员或返修流程差异，不能用于人员效率定责。逐项范围核对无法识别范围内但少见的工序组合。版本只切换两个网点与两个系数基准，输入采用逐票录入和修订。只有公开给本机的演示口令，部署到其他环境需要配置独立凭据和 JWT 密钥。发布稿冻结，口径或行动有变化时用新运行重新复核。

许可状态见 [LICENSE.md](LICENSE.md)。

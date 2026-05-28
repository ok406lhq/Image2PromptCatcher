# Image2PromptCatcher 项目流程复盘与工作流分析

## 1. 文档目标

本文档完整记录本项目从需求提出到上线运行的全过程，覆盖以下内容：

- 需求理解与目标拆解
- 架构与实现策略
- 关键代码改动与原因
- 你与我的协作过程（按阶段复盘）
- 问题清单、根因分析与修复措施
- 当前可稳定运行的工作流设计
- 后续优化建议

---

## 2. 初始目标与核心约束

### 2.1 你的核心需求

你最初提出的业务目标是：

1. 每天北京时间 `09:00` 和 `23:00` 自动抓取目标仓库文档：
   - `https://github.com/YouMind-OpenLab/awesome-gpt-image-2/blob/main/README_zh.md`
2. 将源文档改造成“适合发布的网页内容”，并且避免照搬原文结构。
3. 页面内容重点只保留：
   - 标题
   - 图片
   - 描述
   - 提示词
4. 前端页面需要更像发布型富文本站点，带更好的视觉设计与交互体验。

### 2.2 衍生交互需求（后续追加）

在迭代中你进一步明确了三个关键交互要求：

1. 提示词展示逻辑要智能化，统一按最多 4 行展示，超出显示 `...`。
2. 每条提示词提供“复制”按钮，复制完整提示词文本。
3. 点击图片支持原图预览，多图支持左右切换（特别要求右侧箭头 `→`）。

---

## 3. 最终系统架构（上线版本）

### 3.1 架构总览

项目最终采用“抓取解析层 + 静态发布层”的结构：

1. **抓取解析层（Python）**
   - 文件：`backend/scripts/sync.py`
   - 作用：定时拉取上游 Markdown，提取结构化数据，输出 `article.json`

2. **前端展示层（Vue + Vite）**
   - 文件：`frontend/src/App.vue`
   - 作用：读取 `article.json` 并渲染发布型图文页面

3. **定时自动化层（GitHub Actions）**
   - `.github/workflows/sync-document.yml`：定时抓取并提交更新
   - `.github/workflows/deploy-pages.yml`：自动构建并发布到 GitHub Pages

4. **静态托管层（GitHub Pages）**
   - 线上地址：`https://ok406lhq.github.io/Image2PromptCatcher/`

### 3.2 数据流

1. 定时任务触发 `sync-document.yml`
2. 执行 `python backend/scripts/sync.py`
3. 生成/更新 `frontend/public/data/article.json`
4. Action 自动 `git commit` + `git push`
5. 触发 `deploy-pages.yml`
6. Vite 构建 `frontend/dist`
7. 发布到 GitHub Pages
8. 前端页面读取 `${BASE_URL}data/article.json` 展示最新内容

---

## 4. 关键文件与职责

### 4.1 后端脚本与 API

- `backend/scripts/sync.py`
  - 定时同步主入口
  - 解析 Markdown 中的标题、描述、提示词、图片
  - 过滤噪声图（徽章、统计图、封面图等）
  - 输出结构化 JSON 到前端 public 目录

- `backend/main.py`
  - 提供手动同步与数据读取 API
  - 结构与 `sync.py` 保持一致，便于本地开发与调试

### 4.2 前端页面

- `frontend/src/App.vue`
  - 主页面渲染
  - 展示图文卡片流
  - 提示词 4 行截断显示
  - 复制提示词
  - 图片灯箱预览与多图切换

- `frontend/vite.config.ts`
  - `base: '/Image2PromptCatcher/'`
  - 适配 GitHub Pages 子路径部署

### 4.3 CI/CD 工作流

- `.github/workflows/sync-document.yml`
  - 定时 cron：UTC `1:00` 与 `15:00`（北京时间 `09:00` 与 `23:00`）
  - 同步后自动提交更新
  - 提交信息已移除 `[skip ci]`，确保能触发部署流程

- `.github/workflows/deploy-pages.yml`
  - push 到 `master/main` 自动构建发布
  - 使用 GitHub 官方 Pages Action 发布 `frontend/dist`

---

## 5. 协作过程复盘（按阶段）

> 以下为你和我在本次协作中的关键阶段摘要，按“需求-动作-结果”的方式记录。

### 阶段 A：初版重写

#### 你的输入

- 重写网站
- 定时抓取指定 README
- 页面不要照搬原文，重点输出图片、描述、提示词、标题

#### 我的动作

- 检查现有项目结构（前端 Vue + 后端 Python）
- 保留原有定时思路，改造解析与展示
- 初版改造后端数据格式与前端页面

#### 阶段结果

- 功能可运行
- 视觉上进入“图文页”方向
- 但数据提取准确性与展示细节未满足你预期

### 阶段 B：你直接指出质量问题

#### 你的反馈

- 图片不对
- 提示词和描述被遮挡，展示逻辑不合理
- 希望增加动画

#### 我的动作

- 重写图片 URL 归一化和噪声图过滤逻辑
- 调整前端描述与提示词样式
- 增强卡片动画

#### 阶段结果

- 页面有改进
- 你继续指出预览站点表现仍不符合预期

### 阶段 C：在线预览联调与精准修复

#### 你的输入

- 提供在线预览链接要求我自查

#### 我的动作

- 反查生成数据文件，发现只有 `Star History` 噪声图被抓到
- 解析器增加 HTML 图片识别（README 中大量图片是 `<img>`）
- 增加过滤词：`star-history.com` 等
- 强化“按条目提取标题/描述/提示词/图片”

#### 阶段结果

- `article.json` 转为高质量结构化数据
- 示例条目恢复为真实案例图（如 No.1 VR 海报）

### 阶段 D：交互体验二次升级

#### 你的输入

1. 提示词固定最多 4 行显示
2. 提示词支持复制
3. 点击图片预览，多图可切换

#### 我的动作

- 提示词显示改为“完整文本输入 + 4 行可视裁切”
- 增加复制按钮和状态反馈
- 增加灯箱预览与左右切图

#### 阶段结果

- 页面交互达到你的要求，你确认“可以了”

### 阶段 E：GitHub 发布与 CI 链路打通

#### 你的输入

- 请求我协助推送到 GitHub

#### 我的动作

- 配置远程时遇到凭据代理异常，改为你本地完成推送
- 你推送后出现 Action 报错：`Permission denied: '/workspace'`
- 我修复脚本输出路径为“仓库相对路径”

#### 阶段结果

- 同步 action 执行成功

### 阶段 F：Pages 404 与自动部署修复

#### 你的输入

- Pages 404
- 缺少 `deploy-pages.yml`

#### 我的动作

- 新增 `.github/workflows/deploy-pages.yml`
- 修复 `frontend/vite.config.ts` 的 `base` 子路径
- 修复前端数据请求路径为 `${import.meta.env.BASE_URL}data/article.json`
- 修复 `sync-document.yml` 去除 `[skip ci]`
- 扩展 `deploy-pages.yml` 触发分支：`master/main`

#### 阶段结果

- “抓取 action -> 自动触发部署 action -> 页面更新”链路完整打通

---

## 6. 问题清单与根因分析

### 问题 1：抓到错误图片（只剩 Star History）

**现象**
- 页面展示与业务预期严重偏离

**根因**
- 解析器只处理 Markdown `![]()`，未处理 HTML `<img>`
- 缺乏噪声图过滤规则

**修复**
- 增加 HTML 图片提取
- 增加噪声图过滤关键词（`shields.io`、`star-history.com` 等）

### 问题 2：提示词展示不智能

**现象**
- 跟着上游换行走，视觉不统一

**根因**
- 初版采用“文本拆行后逐条渲染”策略

**修复**
- 统一渲染策略：完整文本 + 固定 4 行可视裁切 + 省略号

### 问题 3：GitHub Actions 权限路径错误

**现象**
- `Permission denied: '/workspace'`

**根因**
- 脚本写死本地绝对路径

**修复**
- 改为仓库相对路径：`Path(__file__).resolve().parents[2]`

### 问题 4：Pages 404

**现象**
- 站点可访问但资源 404 / 页面空白

**根因**
- 缺少 pages 发布 workflow
- Vite `base` 未设置子路径
- 前端数据请求写死根路径 `/data/article.json`

**修复**
- 新增 `deploy-pages.yml`
- 设置 `base: '/Image2PromptCatcher/'`
- 数据请求改为 `${BASE_URL}data/article.json`

### 问题 5：抓取后未自动触发部署

**现象**
- 定时抓取成功，但网页不更新

**根因**
- 提交信息包含 `[skip ci]`
- 部署 workflow 触发分支可能不匹配

**修复**
- 移除 `[skip ci]`
- 部署 workflow 分支改为 `master/main`

---

## 7. 当前可用工作流（最终版）

### 7.1 定时抓取工作流

文件：`.github/workflows/sync-document.yml`

职责：
- 按 cron 定时执行
- 更新 `frontend/public/data/article.json`
- 自动提交并推送

关键点：
- 不能使用 `[skip ci]`
- 需要 `contents: write` 权限

### 7.2 页面部署工作流

文件：`.github/workflows/deploy-pages.yml`

职责：
- push 到 `master/main` 后自动触发
- 构建前端并发布到 GitHub Pages

关键点：
- `permissions` 必须包含 `pages: write` 与 `id-token: write`
- 发布目录是 `frontend/dist`

### 7.3 线上访问规则

- 站点：`https://ok406lhq.github.io/Image2PromptCatcher/`
- 数据：`https://ok406lhq.github.io/Image2PromptCatcher/data/article.json`

---

## 8. 当前成果验收清单

### 8.1 数据层

- 已实现定时抓取
- 已实现结构化提取（标题/描述/提示词/图片）
- 已过滤噪声图

### 8.2 展示层

- 发布型图文页面完成
- 描述完整显示
- 提示词统一 4 行显示 + 省略
- 提示词复制按钮可用
- 图片灯箱预览与多图切换可用

### 8.3 自动化层

- 抓取 action 可自动更新数据
- 部署 action 可自动发布网页
- 两个 action 链路已联通

---

## 9. 我对这套工作流的评估

### 9.1 优点

1. **结构清晰**：抓取、解析、展示、发布职责分离。
2. **成本低**：无需常驻后端服务，GitHub Pages + Actions 可覆盖需求。
3. **可维护性强**：关键逻辑集中在 `sync.py` 与 `App.vue`。
4. **发布稳定**：每次数据更新自动驱动静态站点刷新。

### 9.2 风险点

1. 上游 README 结构大变时，解析规则可能需要调整。
2. 长提示词在移动端可读性依赖排版策略，需要持续优化。
3. 若定时提交过频，仓库 commit 量会快速增长。

### 9.3 建议优化

1. 给 `sync.py` 增加解析回归测试（样例 README 快照）。
2. 给前端加“展开提示词全文”按钮（4 行之外可展开）。
3. 增加“仅显示精选条目”筛选，提升首屏质量。
4. 可选加入“最近更新时间”醒目提示与失败重试机制。

---

## 10. 后续维护手册（简版）

### 10.1 手动触发抓取

在 GitHub Actions 页面手动运行 `Sync GitHub Document`。

### 10.2 手动触发部署

在 GitHub Actions 页面手动运行 `Deploy Frontend To Pages`。

### 10.3 本地验证

```bash
# 1) 生成最新数据
python3 backend/scripts/sync.py

# 2) 构建前端
cd frontend
npm run build
```

### 10.4 常见故障定位顺序

1. 看 `sync-document` 是否成功
2. 看 `article.json` 是否确实变更
3. 看 `deploy-pages` 是否被触发
4. 看 Pages 配置是否仍为 `GitHub Actions`
5. 看 `vite.config.ts` 的 `base` 是否正确

---

## 11. 结论

本项目已经从“原始抓取展示”升级为“可持续自动运营的发布型图文站点”。

你提出的高优先级体验诉求（数据准确、提示词可读、复制能力、图片预览、多图切换、自动更新）已经全部纳入实现，并通过工作流联动形成闭环。

当前这套方案在 GitHub 生态内具备较高稳定性和较低运维成本，适合长期运行与逐步增强。

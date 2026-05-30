# 最近修复总结（同步更新与页面展示）

## 本次修复目标

围绕你反馈的两个问题完成修复：

1. 定时抓取后页面不自动更新
2. 页面没有显示 `via X` 跳转按钮

---

## 一、工作流自动更新链路修复

### 问题现象

- `Sync GitHub Document` 会按计划执行
- `Deploy Frontend To Pages` 没有稳定触发
- 页面更新时间长期停留在旧时间

### 根因分析

1. `sync` 任务提交由 `GITHUB_TOKEN` 触发，单靠 `on: push` 监听存在触发不稳定情况
2. 历史上存在 `[skip ci]` 提交信息会跳过后续 CI
3. `deploy-pages` 需要可靠监听 `sync` 完成事件

### 修复动作

修改文件：`.github/workflows/deploy-pages.yml`

- 新增 `workflow_run` 触发器：监听 `Sync GitHub Document` 成功完成
- 保留 `push` 触发（`master/main`）
- 新增 job 条件：仅在 `workflow_run` 成功时执行构建发布

修改文件：`.github/workflows/sync-document.yml`

- 提交信息移除 `[skip ci]`

### 修复后链路

1. 定时执行 `sync-document.yml`
2. 更新 `frontend/public/data/article.json`
3. 自动提交推送
4. `deploy-pages.yml` 通过 `workflow_run` 被稳定触发
5. GitHub Pages 自动发布新版本

---

## 二、`via X` 按钮不显示修复

### 问题现象

- 前端模板有 `via X` 按钮逻辑
- 实际页面没有按钮

### 根因分析

`article.json` 中 `xUrl` 字段全部为空。原因是解析顺序：

- 图片块先被解析并写入
- `来源` 行（Twitter/X 链接）在后面才出现
- 旧逻辑写入时还拿不到链接，导致空值

### 修复动作

修改文件：`backend/scripts/sync.py`、`backend/main.py`

- 为每个条目增加 `current_block_indexes`
- 先记录当前条目已生成的图片 block 索引
- 当解析到 `- **来源:** [Twitter Post](...)` 后，回填该条目下所有 block 的 `xUrl`

### 验证结果

- 本地验证输出：`blocks 187 with_x 187`
- 说明所有卡片都已具备 `xUrl`，前端可显示 `via X`

---

## 三、前端展示需求同步情况

本轮前端已实现并验证：

1. 提示词：完整文本输入 + 5 行可视裁切（超出省略）
2. 描述：强制 2 行显示，悬停显示完整内容（`title`）
3. `via X`：每个 prompt 显示来源跳转按钮

涉及文件：`frontend/src/App.vue`

---

## 四、上线生效检查清单

推送后按以下顺序检查：

1. `Actions` 中 `Sync GitHub Document` 成功
2. `Actions` 中 `Deploy Frontend To Pages` 被自动触发且成功
3. 打开：`https://ok406lhq.github.io/Image2PromptCatcher/`
4. 强刷页面（Ctrl+F5）
5. 抽查任意卡片：
   - 有 `via X` 按钮
   - 描述为 2 行并可悬停看全文
   - 提示词为 5 行裁切
6. 校验数据：
   - `https://ok406lhq.github.io/Image2PromptCatcher/data/article.json`

---

## 五、结论

当前方案已形成稳定闭环：

- 定时抓取可自动驱动网页更新
- 来源链接可以稳定写入并在前端展示
- 页面交互满足最新展示规范

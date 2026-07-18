# 最近修复总结（同步更新与页面展示）

## 2026-06-08 UI 交互增强功能

### 新增功能

#### 1. 回到顶部按钮
- 页面滚动超过 600px 时，右下角显示圆形回到顶部按钮
- 点击后平滑滚动到页面顶部
- 棕褐色主题配色，带悬停动画和阴影效果

#### 2. 图片高度调整
- 将卡片图片的纵横比从 4:3 调整为 3:4
- 增加图片显示高度，更好地展示 AI 生成的竖版图片

#### 3. 提示词弹窗详情
- 点击提示词文本弹出全屏遮罩弹窗，显示完整内容
- 支持复制全文功能
- 弹窗动画效果：
  - 遮罩层淡入 + 毛玻璃模糊
  - 弹窗缩放 + 位移动画（弹性缓动曲线）
  - 关闭按钮悬停旋转 90 度
  - 复制按钮悬停上浮效果
- 设计细节：
  - 渐变背景和圆角设计
  - 阴影层次分明
  - 配色与整体风格一致（棕橙色调）
  - 弹窗内支持滚动查看长文本

#### 4. 图片预览缩放功能
- 点击图片进入预览模式后支持缩放和拖拽
- 缩放方式：
  - 鼠标滚轮缩放（向上放大，向下缩小）
  - 底部控制栏 + / − 按钮
  - 缩放范围：50% ~ 300%
- 拖拽移动：
  - 放大后自动启用拖拽模式
  - 鼠标指针变为"抓取"手势
  - 按住鼠标左键拖拽查看图片不同区域
  - 缩小或重置后自动禁用拖拽
- 控制栏功能：
  - **−** 按钮 - 缩小 20%
  - **缩放百分比** - 实时显示当前缩放级别
  - **+** 按钮 - 放大 20%
  - **⊡** 按钮 - 重置到 100% 并居中
- 交互细节：
  - 点击预览框周围暗色区域关闭预览
  - 切换图片时自动重置缩放和位置
  - 关闭弹窗时重置状态
  - 拖拽时有平滑过渡动画
  - 控制栏带毛玻璃效果和悬停动画

涉及文件：`frontend/src/App.vue`

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

---

## 2026-07-18 写作导出与拖拽排序功能

### 新增功能

#### 1. 写作导出
- 右侧收藏面板底部新增"写作"按钮，点击后显示进度条
- 生成完成后显示"文本"和"图片"两个独立下载按钮
- 文本输出为 HTML 格式：参照预设模板排版，内嵌 CSS，按收藏顺序逐条输出卡片信息（序号、章节标题、描述、提示词、生成图片占位区、详情）
- 图片输出为 ZIP 压缩包：图片通过 `/api/proxy-image` 代理获取，按收藏顺序重命名为 1.png / 2.jpg 等
- prompt 内容自动格式化：`{argument name="xxx" default="yyy"}` → `yyy`

#### 2. 拖拽排序
- 收藏列表支持鼠标拖拽重排（桌面端面板和移动端抽屉均支持）
- 拖拽时被拖项半透明，目标位置显示橙色引导线
- 基于 HTML5 Drag & Drop API，纯前端实现

### 后端改动
- `backend/main.py`: 图片代理白名单新增 `camo.githubusercontent.com`，解决 Camo 图片防盗链导致压缩包为空的问题

### 前端改动
- `App.vue`: 新增 `generateHtml`、`escapeHtml`、`formatPrompt`、`generateZip`、`handleExport`、`downloadText`、`downloadZip` 函数
- `App.vue`: 新增拖拽排序处理函数 `onBookmarkDragStart` / `onBookmarkDragOver` / `onBookmarkDrop` / `onBookmarkDragEnd`
- `App.vue`: 写作按钮 UI（进度条 + 分步下载按钮）
- `App.vue`: `BookmarkItem` 接口扩展 description/xUrl/publishedAt/author/language 字段
- `package.json`: 新增 `jszip` 依赖

### 相关规格文档
- `.monkeycode/specs/writing-export/requirements.md`
- `.monkeycode/specs/writing-export/design.md`

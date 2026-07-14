# Image2PromptCatcher 项目文档

## 功能清单

| 功能 | 状态 | 说明 |
|------|------|------|
| 定时同步 | 完成 | 每天 09:00 / 23:00 自动抓取 GitHub README |
| 文章展示 | 完成 | 图文卡片流，含标题/图片/描述/提示词/作者/语言 |
| 历史版本切换 | 完成 | 最近 10 个提交版本站内切换 |
| 图片 Camo 代理 | 完成 | cms-assets.youmind.com 图片通过 GitHub Camo 代理加载 |
| 收藏功能 | 完成 | 桌面端右侧面板 + 移动端底部抽屉，跨版本跳转 |
| 提示词弹窗 | 完成 | 点击提示词弹出全屏详情，支持复制全文 |
| 图片预览缩放 | 完成 | 灯箱预览，滚轮/按钮缩放 (50%-300%)，拖拽移动 |
| 回到顶部 | 完成 | 滚动超过 600px 显示按钮 |
| via X 按钮 | 完成 | 每个卡片显示 X/Twitter 来源跳转 |
| 复制描述/提示词 | 完成 | 一行复制按钮，已复制状态反馈 |

---

## 技术架构

### 整体架构

```
GitHub README (raw) → Python 后端解析 → article.json → Vue 前端渲染
                                    ↕
                         GitHub API (Markdown/Camo)
```

- **前端**: Vue 3 + TypeScript + Vite 8 + TailwindCSS 4
- **后端**: Python FastAPI + httpx
- **运维**: GitHub Actions 定时同步 + Pages 自动部署

### 数据流

```
[cron] sync-document.yml
  → python backend/main.py (sync endpoint)
  → 解析 Markdown → article.json
  → GitHub Camo API → 替换图片 URL
  → 保存到 frontend/public/data/article.json
  → GitHub Pages deploy
```

### 关键文件

```
frontend/
├── src/App.vue                  # 单文件主组件（所有 UI 逻辑）
├── vite.config.ts               # Vite 配置 (base/代理)
└── public/data/article.json     # 文章数据

backend/
├── main.py                      # FastAPI (sync/api/proxy-image)
└── requirements.txt             # Python 依赖
```

### API 端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/article` | GET | 获取当前文章数据 |
| `/api/sync` | POST | 手动触发同步 |
| `/api/proxy-image?url=...` | GET | 图片代理（cms-assets → camo URL） |

---

## 部署

### 本地开发

```bash
# 后端
cd backend && pip3 install -r requirements.txt
python3 main.py    # 监听 3001

# 前端
cd frontend && npm install
npm run dev        # 监听 5173，/api 代理到 3001
```

### GitHub Actions 定时同步

文件 `.github/workflows/sync-document.yml`：
- Cron: UTC 1:00 / 15:00 (北京时间 09:00 / 23:00)
- 执行 `python backend/main.py` sync 逻辑
- 自动 commit + push article.json

文件 `.github/workflows/deploy-pages.yml`：
- 监听 push 到 `master/main`
- 构建 `frontend/dist` → GitHub Pages

### 静态托管

- GitHub Pages: `https://ok406lhq.github.io/Image2PromptCatcher/`
- Vercel: Root Directory = `frontend`, Output = `dist`
- Netlify: Base = `frontend`, Publish = `frontend/dist`

---

## 功能需求详情

### 1. 定时同步

- 来源: `https://github.com/YouMind-OpenLab/awesome-gpt-image-2/blob/main/README_zh.md`
- 频率: 每天 2 次 (09:00 / 23:00 北京时间)
- 解析提取: 标题、图片、描述、提示词、来源链接、发布时间、作者、语言
- 过滤噪声图: shields.io、badge.svg、star-history.com、marketing-assets.youmind.com、cover 图

### 2. 历史版本切换

- 获取最近 10 条 README_zh.md 提交记录
- 每个版本完整解析 blocks 数据
- 前端按钮格式: `YYYY-MM-DD-vN`（同一天多版本递增编号）
- 切换时带动画过渡，收藏状态跨版本保持

### 3. 图片代理与 Camo URL

**问题**: `cms-assets.youmind.com` 配置了 Cloudflare/Dropbox WAF，非浏览器请求被阻断（"Sorry, you have been blocked"），从部分网络环境（包括当前开发环境）无法直接访问。

**根因**: DNS 解析到 Dropbox IP (162.125.2.5)，SSL 握手被深度包检测阻断。

**解决方案**:
1. GitHub Markdown API 渲染 README 时自动将外部图片转为 `camo.githubusercontent.com` 代理 URL
2. 同步时调用 GitHub Markdown API 获取 camo URL 映射，缓存到 `camo_cache.json`
3. 所有 cms-assets URL 替换为 camo URL，图片通过 GitHub CDN 加载
4. 后备方案: 前端 `proxyImageUrl()` 将未替换的 cms-assets URL 转为 `/api/proxy-image` 代理，后端按需解析 camo URL

**实现文件**: `backend/main.py` (build_camo_url_map, resolve_camo_url, proxy-image 端点), `frontend/src/App.vue` (proxyImageUrl)

### 4. 收藏功能

- 每张卡片有收藏按钮（心形 SVG，已收藏时填充）
- 桌面端: 右侧固定收藏面板，显示缩略图 + 标题
- 移动端 (<768px): 底部入口按钮 → 抽屉面板
- 点击缩略图: 切换到对应版本 → 滚动到卡片 → 打开提示词弹窗
- 数据: 浏览器内存 (ref)，刷新后重置

### 5. UI 交互增强

- **提示词弹窗**: 点击提示词文本弹出全屏遮罩，展示完整内容 + 复制按钮
- **图片预览**: 灯箱弹窗，支持滚轮/按钮缩放 (50%-300%)，放大后可拖拽
- **回到顶部**: 滚动 >600px 显示按钮，平滑滚动
- **卡片动画**: 切换版本时卡片淡入动画
- **响应式**: 桌面端三列网格 + 移动端单列

---

## 问题记录与修复

### 问题 1: cms-assets.youmind.com 图片无法访问

- **日期**: 2026-07-14
- **现象**: 所有 `https://cms-assets.youmind.com/media/*.jpg` 图片返回 "Sorry, you have been blocked"
- **根因**: CDN 配置了 WAF，当前环境 IP 被阻断
- **修复**: 通过 GitHub Markdown API 获取 camo URL 映射，将所有图片 URL 替换为 camo.githubusercontent.com 代理地址
- **相关 commit**: camo URL 代理功能

### 问题 2: via X 按钮不显示

- **现象**: 前端有按钮逻辑但页面不显示
- **根因**: 解析顺序导致 `xUrl` 在图片块写入后才被解析到（来源链接在图片后）
- **修复**: 增加 `current_block_indexes`，解析到来源链接后回填已写入 block 的 `xUrl`

### 问题 3: 仅抓到噪声图 (Star History)

- **现象**: 页面只显示徽章和统计图
- **根因**: 解析器仅处理 `![]()` 语法，未处理 `<img>` HTML 标签；缺少噪声图过滤
- **修复**: 增加 HTML 图片提取 + 噪声图关键词过滤

### 问题 4: GitHub Actions 权限路径错误

- **现象**: `Permission denied: '/workspace'`
- **根因**: sync 脚本写死了本地绝对路径 `/workspace`
- **修复**: 改为仓库相对路径 `Path(__file__).resolve().parents[2]`

### 问题 5: Pages 404 / 页面空白

- **根因**: 缺少 deploy-pages.yml；Vite base 未设置子路径；数据请求路径写死根目录
- **修复**: 新增 deploy workflow；设置 `base: '/Image2PromptCatcher/'`；改用 `${BASE_URL}data/article.json`

### 问题 6: 抓取后页面不自动更新

- **根因**: 提交信息含 `[skip ci]`；部署 workflow 触发分支不匹配
- **修复**: 移除 `[skip ci]`；触发分支改为 `master/main`

### 问题 7: 历史版本为空

- **日期**: 2026-07-14
- **现象**: 前端历史版本按钮存在但切换不生效，`historyVersions` 为空数组
- **根因**: `fetch_markdown_by_sha` 函数体被误删；`Article` Pydantic 模型缺少 `recentHistory` 和 `historyVersions` 字段被 FastAPI 过滤
- **修复**: 恢复函数定义；补全 Article 模型字段

### 问题 8: 部分历史版本图片未替换为 camo URL

- **现象**: 旧版本中独有图片仍为原始 cms-assets URL
- **根因**: camo 映射仅从最新版 Markdown 构建，未覆盖旧版本独有图片
- **处理**: 前端 proxyImageUrl 自动将原始 URL 转为代理，后端按需解析 camo URL

---

## 本地开发命令

```bash
# 后端
cd backend
pip3 install -r requirements.txt
python3 main.py

# 前端
cd frontend
npm install
npm run dev

# 手动同步
curl -X POST http://localhost:3001/api/sync
```

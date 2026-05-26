# GPT-Image2 文章发布系统

每天定时抓取 GitHub 仓库的文档 README_zh.md 文件，并转换为精美网页展示。

## 项目结构

```
.
├── frontend/                 # Vue 3 前端应用
│   ├── src/
│   │   ├── App.vue          # 主应用组件
│   │   └── index.css        # 全局样式
│   └── public/data/         # 静态数据目录
├── backend/                 # Python FastAPI 后端
│   ├── main.py              # FastAPI 应用
│   ├── requirements.txt     # Python 依赖
│   └── scripts/
│       └── sync.py         # 同步脚本
└── .github/workflows/       # GitHub Actions 配置
    └── sync-document.yml   # 定时任务配置
```

## 功能特点

- **定时同步**: 每天北京时间 9:00 和 23:00 自动从 GitHub 抓取最新内容
- **Markdown 转换**: 使用 Python-Markdown 库将 Markdown 转换为富文本 HTML
- **美化展示**: Vue 3 + Tailwind CSS 构建现代化阅读界面
- **响应式设计**: 支持桌面端和移动端自适应
- **深色主题**: 自动跟随系统暗色模式

## 快速开始

### 1. 安装前端依赖

```bash
cd frontend
npm install
```

### 2. 启动开发服务器

```bash
npm run dev
```

访问 `http://localhost:5173` 查看效果。

### 3. 安装后端依赖

```bash
cd backend
python3 -m venv venv  # 如果尚未创建
source venv/bin/activate  # Linux/macOS
pip install -r requirements.txt
```

### 4. 启动后端服务（可选开发使用）

```bash
python main.py
```

## 自动部署

项目在推送代码后会自动部署到 Vercel/Netlify。也可以启用 GitHub Actions 进行自动部署。

## GitHub Actions

定时任务配置在 `.github/workflows/sync-document.yml`，每天自动执行两次同步：

- 北京时间 9:00 (UTC 1:00)
- 北京时间 23:00 (UTC 15:00)

GitHub Actions 会执行以下步骤：
1. 安装 Python 和依赖库
2. 运行同步脚本抓取 GitHub 文档
3. 将处理后的文章内容提交到仓库

## 技术栈

### 前端
- Vue 3 + TypeScript
- Vite (构建工具)
- Tailwind CSS (样式框架)
- Axios (HTTP 客户端)

### 后端
- Python 3.11
- FastAPI (API 服务)
- Markdown (Markdown 转换)
- httpx (HTTP 客户端)

### 运维
- GitHub Actions (定时任务)
- Vercel/Netlify (静态网站托管)

## 开发

### 前端开发

```bash
cd frontend
npm run dev      # 开发模式
npm run build    # 生产构建
npm run preview  # 预览构建结果
```

### 后端开发

```bash
cd backend
source venv/bin/activate
python main.py
```

API 端点：
- `GET /` - API 根路径
- `GET /api/article` - 获取当前文章
- `POST /api/sync` - 手动触发同步

## 文件说明

### 前端文件
- `src/App.vue` - 主应用组件，包含文章展示逻辑
- `src/index.css` - 全局样式，包含 Tailwind CSS 和自定义样式
- `public/data/article.json` - 存储抓取后的文章数据

### 后端文件
- `backend/main.py` - FastAPI 应用，提供文章获取和同步接口
- `backend/scripts/sync.py` - GitHub Actions 调用的同步脚本
- `backend/requirements.txt` - Python 依赖列表

### GitHub Actions
- `.github/workflows/sync-document.yml` - 定时同步任务配置

## 自定义

### 更改抓取源

修改 `backend/main.py` 中的 `GITHUB_URL` 常量：

```python
GITHUB_URL = "https://raw.githubusercontent.com/你的用户名/仓库名/main/README_zh.md"
```

### 调整定时任务时间

编辑 `.github/workflows/sync-document.yml` 中的 cron 表达式：

```yaml
on:
  schedule:
    - cron: '0 1 * * *'   # 北京时间 9:00
    - cron: '0 15 * * *'  # 北京时间 23:00
```

Cron 表达式格式：分 时 日 月 周

### 修改样式

编辑 `src/index.css` 或 `src/App.vue` 中的样式。

## 故障排查

### 文章没有更新

1. 检查 GitHub Actions 执行日志
2. 确认 GitHub 仓库文件路径正确
3. 检查是否有网络访问问题

### 样式显示异常

1. 清除浏览器缓存
2. 检查 Tailwind CSS 是否正确安装
3. 确认 `@import "tailwindcss"` 存在

## 许可证

MIT License

## 鸣谢

- [YouMind-OpenLab/awesome-gpt-image-2](https://github.com/YouMind-OpenLab/awesome-gpt-image-2) - 原始内容来源
- [Vue 3](https://vuejs.org/) - 前端框架
- [FastAPI](https://fastapi.tiangolo.com/) - Python Web 框架
- [Tailwind CSS](https://tailwindcss.com/) - CSS 框架

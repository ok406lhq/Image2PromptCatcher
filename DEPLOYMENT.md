# 部署说明

## Vercel 部署

### 1. 连接 GitHub 仓库

1. 访问 [Vercel](https://vercel.com/)
2. 点击 "New Project"
3. 导入你的 GitHub 仓库

### 2. 配置构建设置

- **Framework Preset**: Vite
- **Root Directory**: `frontend`
- **Build Command**: `npm run build`
- **Output Directory**: `dist`

### 3. 部署

点击 "Deploy"，Vercel 会自动构建并部署你的网站。

### 4. 自动部署

每次推送到主分支时，Vercel 会自动重新部署。

## Netlify 部署

### 1. 连接 GitHub

1. 访问 [Netlify](https://netlify.com/)
2. 点击 "Add new site" → "Import an existing project"
3. 选择 GitHub 并授权

### 2. 配置构建设置

- **Base directory**: `frontend`
- **Build command**: `npm run build`
- **Publish directory**: `frontend/dist`

### 3. 部署

点击 "Deploy site"

## 手动部署

### 构建生产版本

```bash
cd frontend
npm run build
```

构建后的文件位于 `frontend/dist/` 目录。

### 部署到任何静态网站托管服务

使用任意支持静态文件托管的服务：

- GitHub Pages
- Cloudflare Pages
- Firebase Hosting
- AWS S3 + CloudFront
- 阿里云 OSS

## 注意事项

### 数据同步

GitHub Actions 会自动同步文章数据到 `frontend/public/data/article.json`，每次同步后自动触发重新部署。

### 自定义域名

在 Vercel/Netlify 设置中可以添加自定义域名。

### 环境变量

本项目不需要配置环境变量。

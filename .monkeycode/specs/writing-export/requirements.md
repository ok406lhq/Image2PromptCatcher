# Requirements Document

## Introduction

为 GPT-Image2 文章发布系统新增"写作"导出功能和收藏列表拖拽排序功能。用户在收藏面板中点击"写作"按钮后，系统生成两个可下载产物：一份 HTML 格式排版文件（含所有已收藏卡片的文字信息，按参照模板排版）和一个压缩包（含所有已收藏卡片的原始图片，按顺序重命名为数字序号格式）。产物以独立按钮形式供用户分别下载。收藏列表支持拖拽排序。

## Glossary

- **系统**: GPT-Image2 文章发布系统前端 (Vue 3 SPA)
- **收藏列表 (bookmarks)**: 用户已收藏卡片的集合，存储于浏览器内存中
- **HTML 文本**: 包含所有已收藏卡片完整文字信息的 HTML 文件，按收藏顺序排版，含 CSS 样式，prompt 内容经过格式化处理
- **压缩包**: 包含所有已收藏卡片原始图片的 ZIP 文件，图片按收藏顺序重命名为数字序号 + 原扩展名（如 1.png, 2.jpg）

## Requirements

### Requirement 1: 写作按钮

**User Story:** AS 内容浏览用户，I want 在右侧收藏面板底部看到"写作"按钮，so that 我可以触发生成导出产物

#### Acceptance Criteria

1. WHILE 收藏列表非空，系统 SHALL 在右侧收藏面板底部显示标记为"写作"的操作按钮
2. WHEN 收藏列表为空，系统 SHALL 隐藏"写作"按钮
3. WHILE 用户添加或移除收藏项，系统 SHALL 实时更新按钮的可见性
4. WHERE "写作"按钮样式，系统 SHALL 沿用收藏面板现有的暖色调配色和圆角风格
5. WHERE 移动端收藏抽屉显示"写作"按钮，系统 SHALL 仅保留在右侧桌面面板

### Requirement 2: HTML 文本生成

**User Story:** AS 内容浏览用户，I want 点击"写作"按钮生成一份参照模板格式的 HTML 文本，so that 我可以获得排版精美的提示词合集

#### Acceptance Criteria

1. WHEN 用户点击"写作"按钮，系统 SHALL 生成一份 HTML 文件
2. WHILE 生成 HTML，系统 SHALL 按收藏列表的顺序依次输出每张卡片的以下信息：序号、章节与标题、描述、提示词、生成图片占位区、作者、语言、发布时间、来源链接
3. WHILE 生成 HTML，系统 SHALL 对 prompt 内容执行格式化：将 `{argument name="xxx" default="yyy"}` 替换为仅保留默认值 `yyy`
4. WHERE 标题格式，系统 SHALL 使用 `No. X: 章节 - 标题` 格式，去除原始标题中的序号前缀
5. WHERE 模板结构，系统 SHALL 参照预设 HTML 模板：h1 页面标题、h2 逐条卡片、h3 子标题分区、pre 代码块存放提示词、hr 分割线
6. WHERE HTML 样式，系统 SHALL 内嵌完整 CSS（860px 最大宽度、代码块灰色背景、System UI 字体栈）

### Requirement 3: 进度反馈与分步下载

**User Story:** AS 内容浏览用户，I want 点击写作后看到进度反馈，完成后单独选择下载文本或图片，so that 我不需要一次性下载所有内容

#### Acceptance Criteria

1. WHEN 用户点击"写作"按钮，系统 SHALL 显示进度条动画和"正在写作处理中..."文字
2. WHEN 生成完成，系统 SHALL 显示"文本"和"图片"两个独立下载按钮
3. WHEN 用户点击"文本"按钮，系统 SHALL 触发下载 `prompts-YYYYMMDD-HHmmss.html`
4. WHEN 用户点击"图片"按钮，系统 SHALL 触发下载 `images-YYYYMMDD-HHmmss.zip`
5. IF 生成过程中发生错误，系统 SHALL 在按钮旁展示简短错误提示

### Requirement 4: 图片压缩包生成

**User Story:** AS 内容浏览用户，I want 点击"图片"按钮下载一个包含收藏卡片原始图片的压缩包，so that 我可以批量下载图片原图

#### Acceptance Criteria

1. WHEN 用户点击"图片"按钮，系统 SHALL 下载一个 ZIP 压缩包
2. WHILE 生成压缩包，系统 SHALL 按收藏列表的顺序将所有卡片的图片通过 `/api/proxy-image` 代理获取并添加到压缩包中
3. WHILE 生成压缩包，系统 SHALL 将图片重命名为数字序号 + 原始文件扩展名格式（如 1.png, 2.jpg）
4. WHERE 代理支持，后端代理 SHALL 接受 `camo.githubusercontent.com` 域名以正确获取图片

### Requirement 5: 收藏列表拖拽排序

**User Story:** AS 内容浏览用户，I want 通过拖拽调整收藏列表的顺序，so that 我可以自定义导出内容的排版顺序

#### Acceptance Criteria

1. WHILE 收藏列表存在多个项目，系统 SHALL 支持通过鼠标拖拽调整项目顺序
2. WHILE 用户拖拽某收藏项，系统 SHALL 将该元素显示为半透明以提供视觉反馈
3. WHILE 用户悬停在另一收藏项上，系统 SHALL 在目标位置顶部显示橙色引导线指示插入位置
4. WHEN 用户释放拖拽，系统 SHALL 将拖拽项插入目标位置并重新排列列表
5. WHERE 拖拽支持，系统 SHALL 在桌面端右侧面板和移动端抽屉中均支持拖拽排序

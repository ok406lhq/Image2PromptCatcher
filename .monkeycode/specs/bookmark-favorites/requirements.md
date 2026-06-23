# Requirements Document

## Introduction

为 GPT-Image2 文章发布系统的前端新增收藏功能。用户在浏览 AI 图片卡片时可收藏感兴趣的内容，收藏列表以缩略图形式固定在页面右侧，点击缩略图可跳转至对应提示词。支持跨版本跳转，收藏数据保存在浏览器内存中，页面刷新后重置。

## Glossary

- **系统**: GPT-Image2 文章发布系统前端 (Vue 3 SPA)
- **卡片 (Card)**: 页面中展示的单个 AI 图片内容块，包含图片、标题、描述、提示词等信息
- **收藏列表**: 用户已收藏卡片的缩略图集合，固定在页面右侧
- **历史版本**: 通过 `recentHistory` 和 `historyVersions` 切换的不同提交快照
- **提示词模态框 (Prompt Modal)**: 点击提示词文本后弹出的全文本详情弹窗

## Requirements

### Requirement 1: 收藏操作

**User Story:** AS 内容浏览用户，I want 在每张卡片上操作收藏与取消收藏，so that 我可以将感兴趣的内容纳入收藏管理

#### Acceptance Criteria

1. WHEN 卡片渲染完毕，系统 SHALL 在每张卡片的操作区显示收藏/取消收藏按钮
2. WHEN 用户点击收藏按钮，系统 SHALL 将当前卡片信息（缩略图、标题、提示词、章节、版本标识）加入收藏列表
3. WHILE 卡片已处于收藏状态，系统 SHALL 在按钮上以视觉变化（填充图标/高亮色）指示已收藏
4. WHEN 用户点击已收藏按钮，系统 SHALL 从收藏列表中移除该卡片

### Requirement 2: 收藏列表展示

**User Story:** AS 内容浏览用户，I want 在页面右侧看到已收藏的缩略图列表，so that 我可以快速浏览收藏内容

#### Acceptance Criteria

1. WHILE 收藏列表非空，系统 SHALL 在视口右侧固定显示收藏面板，包含已收藏卡片的缩略图和简要标题
2. WHEN 收藏列表为空，系统 SHALL 隐藏右侧收藏面板
3. WHEN 用户收藏或取消收藏卡片，系统 SHALL 实时更新右侧收藏列表
4. WHERE 视口宽度小于 768px (移动端)，系统 SHALL 将收藏面板折叠为底部固定入口按钮，点击后展开底部抽屉

### Requirement 3: 点击缩略图跳转

**User Story:** AS 内容浏览用户，I want 点击收藏缩略图跳转到对应提示词，so that 我可以快速查看收藏的提示词详情

#### Acceptance Criteria

1. WHEN 用户点击收藏缩略图，系统 SHALL 打开对应卡片的提示词模态框
2. WHEN 用户点击缩略图时当前版本与收藏时的版本不同，系统 SHALL 先切换至对应历史版本再打开提示词模态框
3. WHEN 用户点击缩略图，系统 SHALL 将页面滚动至对应卡片位置使其进入视口

### Requirement 4: 数据生命周期

**User Story:** AS 内容浏览用户，I want 收藏数据在页面刷新后重置，so that 每次访问都从干净的收藏状态开始

#### Acceptance Criteria

1. WHILE 页面处于本次会话中，系统 SHALL 将收藏数据保存在浏览器内存
2. WHEN 页面刷新，系统 SHALL 清空全部收藏数据
3. WHEN 用户切换历史版本，系统 SHALL 保留收藏列表不变

### Requirement 5: UI 一致性

**User Story:** AS 内容浏览用户，I want 收藏功能 UI 与现有设计风格完全统一，so that 获得一致流畅的视觉体验

#### Acceptance Criteria

1. WHERE 收藏按钮设计，系统 SHALL 沿用现有操作按钮的圆角、配色、字体方案
2. WHERE 收藏面板设计，系统 SHALL 沿用现有暖色调配色 (#fffaf2 背景, #e7c39f 边框) 和 Georgia 字体栈
3. WHERE 收藏缩略图，系统 SHALL 使用与现有卡片一致的圆角 (18px) 和阴影样式
4. WHILE 收藏面板存在，系统 SHALL 使用平滑过渡动画展示与隐藏

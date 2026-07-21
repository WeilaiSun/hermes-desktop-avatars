---
name: install-desktop-avatars
description: "Install desktop message avatars — circular avatars with editable names/images for the Hermes Electron desktop app."
version: 1.1.0
author: WeilaiSun
license: MIT
triggers:
  - install: 安装桌面头像/安装头像/install desktop avatars/给桌面加头像
---

# Install Desktop Message Avatars

当用户要求安装桌面头像时，执行以下步骤。

## 前提

- 用户已 clone hermes-agent 源码（通常在 `F:\Hermes\HERMES_HOME\hermes-agent\` 或类似路径）
- `node` + `npm` 可用
- 桌面端已构建过（`node_modules` 存在）

## 安装步骤

### 1. 运行安装脚本

在 hermes-agent 仓库根目录执行：

```bash
python path/to/install-avatars.py
```

脚本会自动完成以下操作：

### 2. 复制新文件

新增 3 个文件到 hermes-agent 源码对应位置：

| 源路径 (本 skill) | 目标路径 |
|---|---|
| `new-files/apps/desktop/src/store/avatar.ts` | `apps/desktop/src/store/avatar.ts` |
| `new-files/apps/desktop/src/components/chat/message-avatar.tsx` | `apps/desktop/src/components/chat/message-avatar.tsx` |
| `new-files/apps/desktop/src/components/chat/avatar-editor-dialog.tsx` | `apps/desktop/src/components/chat/avatar-editor-dialog.tsx` |

### 3. 修改现有文件

对 5 个文件做精确替换：

| 文件 | 改动 |
|---|---|
| `user-message.tsx` | 导入 MessageAvatar + avatar store → 包裹返回值为 avatar 行 |
| `assistant-message.tsx` | 同上，头像在左 |
| `thread/index.tsx` | 渲染 AvatarEditorDialog |
| `styles.css` | 追加 avatar CSS（含 z-index: 50 防遮挡） |
| `avatar-editor-dialog.tsx` | 替换 ✕ 关闭逻辑（原生 button 直接回调） |

### 4. 重建 + 打包

- `npm install --prefer-offline` → 装依赖
- `npm run build` → 构建前端
- 如果检测到打包版（有 `release/win-unpacked/resources/app.asar`），自动重新打包 asar

### 5. 替换 asar（打包版才有）

关闭 Hermes 后执行：

```powershell
cd apps\desktop\release\win-unpacked\resources
Remove-Item app.asar
Move-Item app.asar.new app.asar
```

### 6. 重启

重新打开 Hermes 桌面端，头像效果即生效。

## 验证

- 打开桌面端 → 对话界面应显示圆形头像（默认首字母 Y 和 H）
- 鼠标划过消息行 → 名称标签淡入
- 点击头像 → 弹出编辑弹窗
- 弹窗中可修改名称、上传图片
- 点击 ✕ 关闭弹窗

## 效果预览

| 功能 | 表现 |
|---|---|
| 用户消息 | 右侧圆形头像 + 气泡左对齐带 max-width 限制 |
| Agent 消息 | 左侧圆形头像 + 气泡右侧对齐 |
| 首字母头像 | 默认 Y（用户）/ H（助手），自定义名称后更新 |
| hover 名称 | 圆形头像旁淡入显示名称 |
| 编辑弹窗 | 点击任意头像弹出，支持改名+上传图片 |
| 数据存储 | localStorage，不上传、不联网 |
| 图层防遮挡 | z-index: 50，不被 sticky 气泡盖住 |
| 关闭弹窗 | 原生 ✕ 按钮直接关闭，Tooltip 不拦截事件 |

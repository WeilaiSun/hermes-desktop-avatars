---
name: install-desktop-avatars
description: "Install desktop message avatars — circular avatars with editable names/images for the Hermes Electron desktop app."
version: 1.0.0
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

### 1. 复制新文件

从本 skill 的 `new-files/` 目录复制 3 个新文件到 hermes-agent 源码对应位置：

```bash
# 假设 hermes-agent 根目录为 $HERMES_HOME/hermes-agent/
SKILL_DIR=$(dirname 当前 skill 的 SKILL.md 路径)

cp $SKILL_DIR/new-files/apps/desktop/src/store/avatar.ts \
   $HERMES_HOME/hermes-agent/apps/desktop/src/store/avatar.ts

cp $SKILL_DIR/new-files/apps/desktop/src/components/chat/message-avatar.tsx \
   $HERMES_HOME/hermes-agent/apps/desktop/src/components/chat/message-avatar.tsx

cp $SKILL_DIR/new-files/apps/desktop/src/components/chat/avatar-editor-dialog.tsx \
   $HERMES_HOME/hermes-agent/apps/desktop/src/components/chat/avatar-editor-dialog.tsx
```

### 2. 修改现有文件

对以下 4 个文件做精确替换（用 patch 工具）。每个文件的改动内容详见本 skill 的 `patches/` 目录。

先定位 hermes-agent 根目录：
```bash
HERMES_ROOT=$(查找 apps/desktop/package.json 所在的目录)
```

然后对每个文件执行 patch：

**styles.css** — 在文件末尾 `@media (prefers-reduced-motion: reduce)` 块之后追加：
```css
/* Message avatars */
.message-avatar { border-radius: 9999px; overflow: hidden; }
.avatar-fallback-ring { box-shadow: 0 0 0 1px var(--ui-stroke-tertiary, rgba(255,255,255,0.1)); }
.message-avatar-editable:focus-visible { outline: 2px solid var(--dt-midground, var(--dt-primary)); outline-offset: 2px; }
[data-slot="message-row"] .message-name-label { opacity: 0; transition: opacity 120ms ease; }
[data-slot="message-row"]:hover .message-name-label,
[data-slot="message-row"]:focus-within .message-name-label { opacity: 1; }
@media (prefers-reduced-motion: reduce) { .message-name-label { transition: none; } }
```

**user-message.tsx** — 导入修改 + 包裹返回值为 flex 行：
- 添加 import: `{ useStore } from '@nanostores/react'`, `{ MessageAvatar } from '@/components/chat/message-avatar'`, `{ $avatarNames, DEFAULT_NAMES } from '@/store/avatar'`
- 在 `useResizeObserver` 之后添加: `const userName = useStore($avatarNames).user || DEFAULT_NAMES.user`
- 包裹 `StickyHumanMessageContainer` 为：
```tsx
<div className="message-row ..." data-slot="message-row">
  <div className="flex min-w-0 flex-1 flex-col items-end">
    <span className="message-name-label ...">{userName}</span>
    <StickyHumanMessageContainer ...>
      ...
    </StickyHumanMessageContainer>
  </div>
  <MessageAvatar clickToEdit role="user" />
</div>
```

**assistant-message.tsx** — 同上理：
- 将 `useStore` 重命名为 `useNanostore`
- 添加 import: `{ MessageAvatar }`, `{ $avatarNames, DEFAULT_NAMES }`
- 添加 `assistantName` 变量
- 包裹 `MessagePrimitive.Root` 为 flex 行，头像在左

**thread/index.tsx** — 渲染对话框：
- 添加 import: `{ useStore }`, `{ AvatarEditorDialog }`, `{ $avatarEditorOpen, closeAvatarEditor }`
- 在 return 中添加 `<AvatarEditorDialog onClose={closeAvatarEditor} open={avatarEditorOpen} />`

### 3. 重建桌面端

```bash
cd $HERMES_ROOT/apps/desktop
npm run build
```

### 4. 提示用户重启

告诉用户：关闭并重新打开 Hermes 桌面端即可看到头像效果。点击任意头像可编辑名称和图片。

## 验证

- 打开桌面端 → 对话界面应显示圆形头像（默认首字母 Y 和 H）
- 鼠标划过消息行 → 名称标签淡入
- 点击头像 → 弹出编辑弹窗
- 弹窗中可修改名称、上传图片

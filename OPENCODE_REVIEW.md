# Hermes Desktop Avatars — Code Review & Release Plan

> 审查对象：https://github.com/WeilaiSun/hermes-desktop-avatars
> 相关 PR：https://github.com/nousresearch/hermes-agent/pull/68069
> 审查指令：OpenCode review → 确认无误后推送

---

## 一、实现概述

给 Hermes 桌面端（Electron + React + Radix UI + nanostores）的消息对话区添加微信风格头像：
- 圆形头像（48px），默认首字母 Y（用户）/ H（助手）
- 鼠标 hover 时淡入名称标签
- 点击任意头像弹出编辑弹窗（改名/上传图片）
- 数据持久化到 localStorage

## 二、核心文件清单

### 2.1 新增文件（3 个）

| 文件 | 职责 | 关键设计 |
|---|---|---|
| `src/store/avatar.ts` | nanostores 存储：`$avatarImages`、`$avatarNames`、`$avatarEditorOpen` | `persistStringRecord` 写入 localStorage；`$avatarEditorOpen` 为 atom 而非 persisted（弹窗状态无需持久化） |
| `src/components/chat/message-avatar.tsx` | 圆形头像组件（支持 image data URL / 首字母 fallback、editable 模式） | 48px 固定大小；`role` prop 决定配色（assistant=#00796B, user=#5C6BC0）；Canvas 缩放处理大图（max 128×128） |
| `src/components/chat/avatar-editor-dialog.tsx` | 编辑弹窗（Dialog + 两个 ParticipantRow） | 自定义 ✕ 按钮（绕过 Radix `asChild` + `Tip` 拦截）；Done 按钮 flush pending 到 store |

### 2.2 修改文件（5 个）

| 文件 | 改动量 | 说明 |
|---|---|---|
| `user-message.tsx` | +6 lines | 加 import（MessageAvatar / useStore / avatar store）→ 包裹 return 为 message-row（flex justify-end gap-2: content-col + avatar） |
| `assistant-message.tsx` | +6 lines | 同上，位置反过来（avatar + content-col） |
| `thread/index.tsx` | +5 lines | `useStore($avatarEditorOpen)` → 在最外层 return 末尾渲染 AvatarEditorDialog |
| `styles.css` | +27 lines | 追加 `.message-avatar`（`position:relative; z-index:50` 防 sticky 气泡遮挡）+ hover 动画 + focus-visible 样式 |
| `avatar-editor-dialog.tsx` | ±24 lines | 替换 handleOpenChange 为 handleClose（`setPendingNames({}); onClose()`）；自定义 ✕ button 替换 Radix 默认按钮（`showCloseButton={false}`） |

### 2.3 安装脚本

`install-avatars.py` — 一键安装（clone → patch → build → asar pack）

### 2.4 SKILL.md

Hermes Skill 元数据文件，支持 `hermes skills install` 触发。

## 三、架构设计决策

### 3.1 布局方案

```
用户消息（justify-end）:       [内容区 (flex-1)] [头像 (48px)]
助手消息（justify-start）:      [头像 (48px)] [内容区 (flex-1)]
```

消息行在 `flex w-full` row 内，`gap-2` 分隔。内容区用 `flex-1` 占满剩余空间。

### 3.2 存储设计

- **名称**：`$avatarNames`（persisted）+ `DEFAULT_NAMES` fallback
- **图片**：`$avatarImages`（persisted），data URL 格式，大图缩放到 128×128 后存
- **弹窗状态**：`$avatarEditorOpen`（atom，不持久化）
- 前缀：`hermes.desktop.avatarNames.v1` / `hermes.desktop.avatarImages.v1`

### 3.3 弹窗关闭修复

原始代码用 `DialogPrimitive.Close asChild` 包裹在 `Tip`（Tooltip）内，点击事件被 Tooltip 拦截。修复方案：
1. `showCloseButton={false}` 禁用 Radix 默认关闭按钮
2. 渲染原生 `<button>` 直接调用 `handleClose`
3. `onOpenChange` 保留给 Escape 和点击外部触发关闭

### 3.4 图层防遮挡

`StickyHumanMessageContainer`（`position:sticky; z-index:40`）会叠在用户头像上。修复：`.message-avatar { position:relative; z-index:50; }`

## 四、审查要点

### 4.1 代码质量
- [ ] nanostores 命名用 `$` 前缀 ✅
- [ ] `persistStringRecord` + 版本化 KEY ✅
- [ ] `useStore($avatarNames)` 订阅正确 ✅
- [ ] CSS class 用 Tailwind + cn()，不写死内联样式 ✅
- [ ] i18n 支持（中/繁/日/英） ✅
- [ ] `prefers-reduced-motion` 尊重 ✅
- [ ] TypeScript 无错误 ✅

### 4.2 功能验证
- [ ] 用户消息：圆形头像在右侧，名称在气泡上方
- [ ] 助手消息：圆形头像在左侧，名称在气泡上方
- [ ] 默认头像：首字母 Y / H，配色区分
- [ ] 鼠标 hover：名称标签淡入
- [ ] 点击头像：弹出编辑弹窗
- [ ] 弹窗改名：Input + Enter 保存 / Done 批量保存
- [ ] 弹窗上传图片：1MB 以内直接存，以上缩放到 128×128
- [ ] 弹窗 ✕ 关闭：按钮正常关闭，Tooltip 不拦截
- [ ] 弹窗 Escape 关闭：正常
- [ ] 图片清除：上传后出现 ✕ 按钮，点击清除
- [ ] 数据持久化：刷新后名称/图片保留
- [ ] 图层：sticky 气泡不遮挡头像
- [ ] 安装脚本：`python install-avatars.py` 完整走通
- [ ] asar 打包：打包版自动生成 `app.asar.new`

### 4.3 注意事项
- `avatar-editor-dialog.tsx` 的补丁同时修改 `handleOpenChange` 和 return JSX
- `styles.css` 的补丁在文件末尾 `@media (prefers-reduced-motion: reduce)` 块后追加
- 若上游源码变更导致 patch 失败，脚本会报"Expected snippet not found"并退出

## 五、提交流程

### 5.1 推送 GitHub Repo

```bash
cd F:\Hermes\hermes-desktop-avatars-temp
# 替换成新文件
# Commit + push
git add -A
git commit -m "feat: add asar packaging to install script + fix dialog close + z-index"
git push origin master
```

### 5.2 更新 Hermes PR

从本地 hermes-agent 仓库生成 diff 并提交到 PR #68069：

```bash
cd F:\Hermes\HERMES_HOME\hermes-agent
git add apps/desktop/src/components/chat/avatar-editor-dialog.tsx
git add apps/desktop/src/styles.css
git commit -m "fix(desktop): avatar dialog close button + z-index occlusion guard"
git push origin master  # push to WeilaiSun/hermes-agent
```

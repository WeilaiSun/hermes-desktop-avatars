# Hermes Desktop Message Avatars 🎭

给 Hermes Agent 桌面版对话界面加上圆形消息头像——类似微信/飞书风格的消息气泡布局。

![preview](preview.png)

## 效果

- 👤 **右对齐用户头像** — 你的消息在右，头像在右
- 🤖 **左对齐助手头像** — Hermes 的消息在左，头像在左
- 🏷️ **hover 显示名称** — 鼠标划过消息行浮现名称标签
- 🖱️ **点击头像编辑** — 弹窗改名称、上传/换图片
- 💾 **自动保存** — 名称和头像持久化到本地

## 安装

```bash
# 1. 进入 Hermes 源码目录
cd hermes-agent

# 2. 下载安装脚本
curl -O https://raw.githubusercontent.com/WeilaiSun/hermes-desktop-avatars/main/install-avatars.py
curl -O https://raw.githubusercontent.com/WeilaiSun/hermes-desktop-avatars/main/new-files.zip
# 或直接 git clone
# git clone https://github.com/WeilaiSun/hermes-desktop-avatars.git && cd hermes-desktop-avatars

# 3. 解压 new-files（如果用了 zip 方式）
# unzip new-files.zip

# 4. 运行安装
python install-avatars.py

# 5. 重启 Hermes 桌面端
```

安装脚本会：
1. 复制 3 个新文件到源码对应目录
2. 修改 4 个现有文件（自动 patch）
3. `npm install && npm run build` 重新构建

## 改动文件

| 文件 | 类型 | 说明 |
|------|------|------|
| `src/store/avatar.ts` | 新增 | nanostore 状态 + localStorage 持久化 |
| `src/components/chat/message-avatar.tsx` | 新增 | 圆形头像组件（图片/首字母/上传） |
| `src/components/chat/avatar-editor-dialog.tsx` | 新增 | 名称+头像编辑弹窗 |
| `src/.../thread/user-message.tsx` | 修改 | 用户消息行包裹头像 |
| `src/.../thread/assistant-message.tsx` | 修改 | 助手消息行包裹头像 |
| `src/.../thread/index.tsx` | 修改 | 渲染编辑弹窗 |
| `src/styles.css` | 修改 | 头像+名称样式 |

## 官方 PR

已提交到 [NousResearch/hermes-agent#68069](https://github.com/NousResearch/hermes-agent/pull/68069)

## 许可

MIT

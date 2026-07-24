#!/usr/bin/env python3
"""Install Hermes Desktop Message Avatars.

Patches the Hermes Agent desktop app source to add circular message avatars
with editable names and images.  Run this from anywhere:

    python install-avatars.py

The script auto-locates the hermes-agent repo root, applies patches via git apply,
builds, and packs a new app.asar for packaged installations.

Requires: git, node + npm, npx
"""

import os
import sys
import shutil
import tempfile
import subprocess
from pathlib import Path

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

SCRIPT_DIR = Path(__file__).resolve().parent
PATCHES_DIR = SCRIPT_DIR / "patches"
NEW_FILES_DIR = SCRIPT_DIR / "new-files"

# New files to copy (source relative to this script → target relative to repo root)
NEW_FILES = {
    "apps/desktop/src/store/avatar.ts":
        NEW_FILES_DIR / "apps/desktop/src/store/avatar.ts",
    "apps/desktop/src/components/chat/message-avatar.tsx":
        NEW_FILES_DIR / "apps/desktop/src/components/chat/message-avatar.tsx",
    "apps/desktop/src/components/chat/avatar-editor-dialog.tsx":
        NEW_FILES_DIR / "apps/desktop/src/components/chat/avatar-editor-dialog.tsx",
}

# Patches to apply via git apply (in order)
PATCH_FILES = [
    "user-message.patch",
    "assistant-message.patch",
    "index.patch",
    "styles.patch",
]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def find_repo_root() -> Path | None:
    """Walk up from cwd to find hermes-agent repo root."""
    d = Path.cwd().resolve()
    for _ in range(10):
        if (d / "apps" / "desktop" / "package.json").exists():
            return d
        d = d.parent
    # Fallback: common paths
    candidates = [
        Path.home() / "hermes-agent",
        Path("F:/Hermes/HERMES_HOME/hermes-agent"),
    ]
    for c in candidates:
        if (c / "apps/desktop/package.json").exists():
            return c
    return None

def is_packaged(root: Path) -> bool:
    """Return True if the desktop app was built into an asar (packaged)."""
    asar = root / "apps/desktop/release/win-unpacked/resources/app.asar"
    return asar.exists()

def is_git_repo(root: Path) -> bool:
    return (root / ".git").exists()

def repack_asar(root: Path) -> None:
    """Pack a new .asar.new using @electron/asar (matching electron-builder's files config)."""
    desktop = root / "apps" / "desktop"
    asar_new = desktop / "app.asar.new"

    with tempfile.TemporaryDirectory(prefix="hermes-asar-") as tmp:
        tmp_path = Path(tmp)
        print("\n  📦 Packing asar...")

        for name in ["dist", "assets", "public"]:
            src = desktop / name
            if src.exists():
                shutil.copytree(src, tmp_path / name)
        shutil.copy2(desktop / "package.json", tmp_path / "package.json")

        subprocess.run(
            ["npx", "--yes", "@electron/asar", "pack", str(tmp_path), str(asar_new)],
            cwd=tmp_path, check=True, capture_output=True
        )

        # Verify structure
        result = subprocess.run(
            ["npx", "--yes", "@electron/asar", "list", str(asar_new)],
            capture_output=True, text=True
        )
        top = result.stdout.strip().split("\n")[:3]
        if not any("dist" in line for line in top):
            print("  ❌ asar missing dist/ directory — packing failed")
            sys.exit(1)

    mb = asar_new.stat().st_size / (1024 * 1024)
    print(f"  ✅ app.asar.new ({mb:.1f}MB) — {asar_new}")

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def apply() -> None:
    root = find_repo_root()
    if not root:
        print("❌ 找不到 Hermes 源码树。请确认已 clone nousresearch/hermes-agent")
        print("   git clone https://github.com/nousresearch/hermes-agent.git")
        sys.exit(1)

    print(f"📁 Repo root: {root}")

    # ── Step 0: Verify it's a git repo (needed for git apply) ─────────────
    if not is_git_repo(root):
        print("❌ 不是 git 仓库，需要从 git clone 安装")
        sys.exit(1)

    # ── Step 1: Copy 3 new files ─────────────────────────────────────────
    print("\n📄 复制新文件...")
    for dst_rel, src in NEW_FILES.items():
        if not src.exists():
            print(f"  ⚠️  源文件不存在: {src}")
            continue
        dst = root / dst_rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        print(f"  ✅ {dst_rel}")

    # ── Step 2: Apply git patches ────────────────────────────────────────
    print("\n🔧 应用补丁...")
    for patch_name in PATCH_FILES:
        patch_file = PATCHES_DIR / patch_name
        if not patch_file.exists():
            print(f"  ⚠️  {patch_name} 不存在 — 跳过")
            continue

        # Try git apply first (handles fuzzy matching automatically)
        result = subprocess.run(
            ["git", "apply", "--ignore-space-change", "--ignore-whitespace",
             str(patch_file)],
            cwd=str(root), capture_output=True, text=True
        )
        if result.returncode == 0:
            print(f"  ✅ {patch_name}")
        else:
            # Check if already applied (content already has our changes)
            result2 = subprocess.run(
                ["git", "apply", "--check", "--reverse", str(patch_file)],
                cwd=str(root), capture_output=True, text=True
            )
            if result2.returncode == 0:
                print(f"  ⏭️  {patch_name} (已安装，跳过)")
            else:
                # Try patch command fallback
                result3 = subprocess.run(
                    ["patch", "-p1", "-i", str(patch_file)],
                    cwd=str(root), capture_output=True, text=True
                )
                if result3.returncode == 0:
                    print(f"  ✅ {patch_name} (patch fallback)")
                else:
                    print(f"  ❌ {patch_name} 应用失败")
                    print(f"     git apply: {result.stderr.strip()[:200]}")
                    print(f"     patch: {result3.stderr.strip()[:200]}")
                    print(f"\n  可能原因：")
                    print(f"  1. 你的 Hermes 版本太新，上游代码已变动")
                    print(f"  2. 此功能已安装（检查是否已有头像）")
                    print(f"  3. 请提交 Issue: https://github.com/WeilaiSun/hermes-desktop-avatars/issues")
                    sys.exit(1)

    # ── Step 3: Rebuild ──────────────────────────────────────────────────
    desktop_dir = root / "apps" / "desktop"
    os.chdir(desktop_dir)

    print("\n📦 安装依赖...")
    if os.system("npm install --prefer-offline") != 0:
        print("❌ npm install 失败")
        sys.exit(1)

    print("🔨 构建中（约 30-60 秒）...")
    if os.system("npm run build") != 0:
        print("❌ 构建失败")
        sys.exit(1)

    # ── Step 4: Repack asar (packaged builds only) ───────────────────────
    if is_packaged(root):
        repack_asar(root)
        asar_new = desktop_dir / "app.asar.new"
        asar_dir = root / "apps/desktop/release/win-unpacked/resources"
        print("\n" + "=" * 60)
        print("  ✅ 安装完成！请执行以下命令替换 asar：")
        print("=" * 60)
        print(f"""
在 PowerShell 中执行：

```powershell
# 关闭 Hermes
Get-Process | Where-Object {{$_.Name -like '*ermes*'}} | Stop-Process -Force

# 替换 asar
cd "{asar_dir}"
Remove-Item app.asar -ErrorAction SilentlyContinue
Move-Item "{asar_new}" "app.asar"

# 验证
$asar = Get-Item app.asar
Write-Host "asar: $([math]::Round($asar.Length/1MB,1))MB, $($asar.LastWriteTime)"

# 清缓存
Remove-Item -Recurse -Force "$env:APPDATA\\Hermes\\Cache" -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force "$env:APPDATA\\Hermes\\GPUCache" -ErrorAction SilentlyContinue

# 重启
Start-Process "{(root / 'apps/desktop/release/win-unpacked/Hermes.exe')}"
```

重启后验证：
- 对话界面显示圆形头像（默认首字母 Y 和 H）
- 鼠标划过消息行 → 名称标签淡入
- 点击头像 → 弹出编辑弹窗
""")
    else:
        print("\n🎉  完成！重启 Hermes 桌面端查看头像效果。")

if __name__ == "__main__":
    apply()

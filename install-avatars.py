#!/usr/bin/env python3
"""Install Hermes Desktop Message Avatars.

Patches the Hermes Agent desktop app source to add circular message avatars
with editable names and images.  Run this from the hermes-agent repo root:

    python install-avatars.py

For packaged builds (release/win-unpacked/Hermes.exe), the script also
repacks the asar archive so the feature works immediately after restart.

Requires: node + npm (for rebuild), npx (for asar pack)
"""

import os
import sys
import shutil
import tempfile
import subprocess
from pathlib import Path

# ---------------------------------------------------------------------------
# Config — 3 new files to copy
# ---------------------------------------------------------------------------

NEW_FILES = {
    "apps/desktop/src/store/avatar.ts":
        "new-files/apps/desktop/src/store/avatar.ts",
    "apps/desktop/src/components/chat/message-avatar.tsx":
        "new-files/apps/desktop/src/components/chat/message-avatar.tsx",
    "apps/desktop/src/components/chat/avatar-editor-dialog.tsx":
        "new-files/apps/desktop/src/components/chat/avatar-editor-dialog.tsx",
}

# ---------------------------------------------------------------------------
# Patches — one (old_string, new_string) pair per modification
# ---------------------------------------------------------------------------

PATCHES: dict[str, list[tuple[str, str]]] = {

    # ── user-message.tsx ────────────────────────────────────────────────
    "apps/desktop/src/components/assistant-ui/thread/user-message.tsx": [
        # Import useStore + MessageAvatar + avatar store
        ("import { ActionBarPrimitive, BranchPickerPrimitive, MessagePrimitive, useAuiState } from '@assistant-ui/react'\n"
         "import { type FC, type ReactNode, useCallback, useRef, useState } from 'react'",
         "import { ActionBarPrimitive, BranchPickerPrimitive, MessagePrimitive, useAuiState } from '@assistant-ui/react'\n"
         "import { useStore } from '@nanostores/react'\n"
         "import { type FC, type ReactNode, useCallback, useRef, useState } from 'react'"),
        ("import { UserMessageText } from '@/components/assistant-ui/thread/user-message-text'\n"
         "import { Codicon }",
         "import { UserMessageText } from '@/components/assistant-ui/thread/user-message-text'\n"
         "import { MessageAvatar } from '@/components/chat/message-avatar'\n"
         "import { Codicon }"),
        ("import { cn } from '@/lib/utils'\n"
         "import { notifyThreadEditOpen } from '@/store/thread-scroll'",
         "import { cn } from '@/lib/utils'\n"
         "import { $avatarNames, DEFAULT_NAMES } from '@/store/avatar'\n"
         "import { notifyThreadEditOpen } from '@/store/thread-scroll'"),
        # Add userName hook after useResizeObserver
        ("  useResizeObserver(measureClamp, clampInnerRef)\n\n"
         "  // Injected background-process notification",
         "  useResizeObserver(measureClamp, clampInnerRef)\n\n"
         "  const userName = useStore($avatarNames).user || DEFAULT_NAMES.user\n\n"
         "  // Injected background-process notification"),
        # Wrap return in avatar row (message-row > content-col + avatar)
        ("  return (\n"
         "    <MessagePrimitive.Root asChild>\n"
         "      <StickyHumanMessageContainer\n"
         "        attachments={",
         "  return (\n"
         "    <MessagePrimitive.Root asChild>\n"
         "      <div className=\"message-row message-row-user flex w-full min-w-0 items-end justify-end gap-2\" data-slot=\"message-row\">\n"
         "        <div className=\"flex min-w-0 flex-1 flex-col items-end\">\n"
         "          <span className=\"message-name-label mb-0.5 mr-1 text-[0.6875rem] leading-4 text-(--ui-text-tertiary) select-none\">\n"
         "            {userName}\n"
         "          </span>\n"
         "          <StickyHumanMessageContainer\n"
         "            attachments={"),
        # Close wrapping divs + add avatar
        ("        </ActionBarPrimitive.Root>\n"
         "      </StickyHumanMessageContainer>\n"
         "    </MessagePrimitive.Root>\n"
         "  )\n}",
         "        </ActionBarPrimitive.Root>\n"
         "      </StickyHumanMessageContainer>\n"
         "        </div>\n"
         "        <MessageAvatar clickToEdit role=\"user\" />\n"
         "      </div>\n"
         "    </MessagePrimitive.Root>\n"
         "  )\n}"),
    ],

    # ── assistant-message.tsx ───────────────────────────────────────────
    "apps/desktop/src/components/assistant-ui/thread/assistant-message.tsx": [
        ("import { useStore } from '@nanostores/react'",
         "import { useStore as useNanostore } from '@nanostores/react'"),
        ("import { TooltipIconButton } from '@/components/assistant-ui/tooltip-icon-button'\n"
         "import { PreviewAttachment } from '@/components/chat/preview-attachment'",
         "import { TooltipIconButton } from '@/components/assistant-ui/tooltip-icon-button'\n"
         "import { MessageAvatar } from '@/components/chat/message-avatar'\n"
         "import { PreviewAttachment } from '@/components/chat/preview-attachment'"),
        ("import { $voicePlayback } from '@/store/voice-playback'\n"
         "",
         "import { $voicePlayback } from '@/store/voice-playback'\n"
         "import { $avatarNames, DEFAULT_NAMES } from '@/store/avatar'\n"),
        ("  const voicePlayback = useStore($voicePlayback)",
         "  const voicePlayback = useNanostore($voicePlayback)"),
        ("  const enterRef = useEnterAnimation(isRunning, `assistant-message:${messageId}`)\n\n"
         "  if (isPlaceholder) {",
         "  const enterRef = useEnterAnimation(isRunning, `assistant-message:${messageId}`)\n\n"
         "  const assistantName = useNanostore($avatarNames).assistant || DEFAULT_NAMES.assistant\n\n"
         "  if (isPlaceholder) {"),
        # Wrap return in avatar row (avatar + content-col)
        ("  return (\n"
         "    <MessagePrimitive.Root\n"
         "      className=\"group flex w-full min-w-0 max-w-full flex-col gap-0 self-start overflow-hidden\"\n"
         "      data-role=\"assistant\"\n"
         "      data-slot=\"aui_assistant-message-root\"\n"
         "      data-streaming={isRunning ? 'true' : undefined}\n"
         "      ref={enterRef}\n"
         "    >",
         "  return (\n"
         "    <div className=\"message-row message-row-assistant flex w-full min-w-0 items-start justify-start gap-2\" data-slot=\"message-row\">\n"
         "      <MessageAvatar clickToEdit role=\"assistant\" />\n"
         "      <div className=\"flex min-w-0 flex-1 flex-col items-start\">\n"
         "        <span className=\"message-name-label mb-0.5 ml-1 text-[0.6875rem] leading-4 text-(--ui-text-tertiary) select-none\">\n"
         "          {assistantName}\n"
         "        </span>\n"
         "        <MessagePrimitive.Root\n"
         "          className=\"group flex w-full min-w-0 max-w-full flex-col gap-0 self-start overflow-hidden\"\n"
         "          data-role=\"assistant\"\n"
         "          data-slot=\"aui_assistant-message-root\"\n"
         "          data-streaming={isRunning ? 'true' : undefined}\n"
         "          ref={enterRef}\n"
         "        >"),
        # Close wrapping divs
        ("        <AssistantFooter getMessageText={getMessageText} messageId={messageId} onBranchInNewChat={onBranchInNewChat} />\n"
         "      )}\n"
         "    </MessagePrimitive.Root>\n"
         "  )\n}",
         "        <AssistantFooter getMessageText={getMessageText} messageId={messageId} onBranchInNewChat={onBranchInNewChat} />\n"
         "      )}\n"
         "    </MessagePrimitive.Root>\n"
         "      </div>\n"
         "    </div>\n"
         "  )\n}"),
    ],

    # ── thread/index.tsx ────────────────────────────────────────────────
    "apps/desktop/src/components/assistant-ui/thread/index.tsx": [
        ("import { UserMessage } from '@/components/assistant-ui/thread/user-message'\n"
         "import { Intro, type IntroProps } from '@/components/chat/intro'",
         "import { UserMessage } from '@/components/assistant-ui/thread/user-message'\n"
         "import { AvatarEditorDialog } from '@/components/chat/avatar-editor-dialog'\n"
         "import { Intro, type IntroProps } from '@/components/chat/intro'"),
        ("import { type FC, useCallback, useMemo, useState } from 'react'\n"
         "",
         "import { type FC, useCallback, useMemo, useState } from 'react'\n"
         "import { useStore } from '@nanostores/react'\n"),
        ("import { notifyError } from '@/store/notifications'",
         "import { notifyError } from '@/store/notifications'\n"
         "import { $avatarEditorOpen, closeAvatarEditor } from '@/store/avatar'"),
        ("  >(null)\n\n"
         "  const closeRestoreConfirm",
         "  >(null)\n\n"
         "  const avatarEditorOpen = useStore($avatarEditorOpen)\n\n"
         "  const closeRestoreConfirm"),
        ("        title={copy.restoreTitle}\n"
         "      />\n"
         "    </div>\n"
         "  )\n}",
         "        title={copy.restoreTitle}\n"
         "      />\n"
         "      <AvatarEditorDialog onClose={closeAvatarEditor} open={avatarEditorOpen} />\n"
         "    </div>\n"
         "  )\n}"),
    ],

    # ── styles.css ──────────────────────────────────────────────────────
    "apps/desktop/src/styles.css": [
        # Append avatar CSS after the last prefers-reduced-motion block
        ("@media (prefers-reduced-motion: reduce) {\n"
         "  .pet-progress__indeterminate {\n"
         "    animation: none;\n"
         "    left: 0;\n"
         "    width: 100%;\n"
         "    opacity: 0.4;\n"
         "  }\n"
         "}\n",
         "@media (prefers-reduced-motion: reduce) {\n"
         "  .pet-progress__indeterminate {\n"
         "    animation: none;\n"
         "    left: 0;\n"
         "    width: 100%;\n"
         "    opacity: 0.4;\n"
         "  }\n"
         "}\n"
         "\n"
         "/* ------------------------------------------------------------------ */\n"
         "/*  Message avatars                                                   */\n"
         "/* ------------------------------------------------------------------ */\n"
         "\n"
         ".message-avatar {\n"
         "  border-radius: 9999px;\n"
         "  overflow: hidden;\n"
         "  position: relative;\n"
         "  z-index: 50;\n"
         "}\n"
         "\n"
         ".avatar-fallback-ring {\n"
         "  box-shadow: 0 0 0 1px var(--ui-stroke-tertiary, rgba(255, 255, 255, 0.1));\n"
         "}\n"
         "\n"
         ".message-avatar-editable:focus-visible {\n"
         "  outline: 2px solid var(--dt-midground, var(--dt-primary));\n"
         "  outline-offset: 2px;\n"
         "}\n"
         "\n"
         "/* Fade the name label in on hover — subtle, not distracting. */\n"
         "[data-slot=\"message-row\"] .message-name-label {\n"
         "  opacity: 0;\n"
         "  transition: opacity 120ms ease;\n"
         "}\n"
         "\n"
         "[data-slot=\"message-row\"]:hover .message-name-label,\n"
         "[data-slot=\"message-row\"]:focus-within .message-name-label {\n"
         "  opacity: 1;\n"
         "}\n"
         "\n"
         "@media (prefers-reduced-motion: reduce) {\n"
         "  .message-name-label {\n"
         "    transition: none;\n"
         "  }\n"
         "}\n"),
    ],

    # ── avatar-editor-dialog.tsx — fix ✕ close button ───────────────────
    "apps/desktop/src/components/chat/avatar-editor-dialog.tsx": [
        # Replace handleOpenChange (which didn't work) with handleClose + custom ✕ button
        ("  const handleDone = useCallback(() => {\n"
         "    // Flush pending name changes to the store\n"
         "    for (const role of ['user', 'assistant'] as AvatarRole[]) {\n"
         "      const pending = pendingNames[role]\n"
         "      if (pending !== undefined) {\n"
         "        const trimmed = pending.trim()\n"
         "        setAvatarName(role, trimmed || names[role] || DEFAULT_NAMES[role])\n"
         "      }\n"
         "    }\n"
         "    onClose()\n"
         "  }, [onClose, pendingNames, names])\n"
         "\n"
         "  const handleOpenChange = useCallback(\n"
         "    (nextOpen: boolean) => {\n"
         "      if (!nextOpen) {\n"
         "        // User clicked \u2716\ufe0f \u2014 save pending changes then close\n"
         "        handleDone()\n"
         "      }\n"
         "    },\n"
         "    [handleDone]\n"
         "  )\n"
         "\n"
         "  return (\n"
         "    <Dialog onOpenChange={handleOpenChange} open={open}>\n"
         "      <DialogContent className=\"max-w-sm\">\n"
         "        <DialogHeader>\n"
         "          <DialogTitle>{copy.title}</DialogTitle>\n"
         "          <DialogDescription>{copy.description}</DialogDescription>\n"
         "        </DialogHeader>",
         "  const handleDone = useCallback(() => {\n"
         "    // Flush pending name changes to the store\n"
         "    for (const role of ['user', 'assistant'] as AvatarRole[]) {\n"
         "      const pending = pendingNames[role]\n"
         "      if (pending !== undefined) {\n"
         "        const trimmed = pending.trim()\n"
         "        setAvatarName(role, trimmed || names[role] || DEFAULT_NAMES[role])\n"
         "      }\n"
         "    }\n"
         "    onClose()\n"
         "  }, [onClose, pendingNames, names])\n"
         "\n"
         "  const handleClose = useCallback(() => {\n"
         "    setPendingNames({})\n"
         "    onClose()\n"
         "  }, [onClose])\n"
         "\n"
         "  return (\n"
         "    <Dialog onOpenChange={nextOpen => { if (!nextOpen) onClose(); }} open={open}>\n"
         "      <DialogContent className=\"max-w-sm\" showCloseButton={false}>\n"
         "        <DialogHeader>\n"
         "          <DialogTitle>{copy.title}</DialogTitle>\n"
         "          <DialogDescription>{copy.description}</DialogDescription>\n"
         "        </DialogHeader>\n"
         "        <button\n"
         "          aria-label={t.common.close}\n"
         "          className=\"absolute right-2.5 top-2.5 z-20 flex size-6 items-center justify-center rounded-md text-(--ui-text-tertiary) hover:bg-(--chrome-action-hover) hover:text-foreground\"\n"
         "          onClick={handleClose}\n"
         "          type=\"button\"\n"
         "        >\n"
         "          \u2715\n"
         "        </button>"),
    ],
}

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
    return None


def is_packaged(root: Path) -> bool:
    """Return True if the desktop app was built into an asar (packaged)."""
    asar = root / "apps/desktop/release/win-unpacked/resources/app.asar"
    return asar.exists()


def repack_asar(root: Path) -> None:
    """Extract the running asar, swap dist/, and pack a new .asar.new."""
    desktop = root / "apps" / "desktop"
    asar_dir = desktop / "release/win-unpacked/resources"
    asar = asar_dir / "app.asar"
    new_asar = asar_dir / "app.asar.new"

    with tempfile.TemporaryDirectory(prefix="asar-") as tmp:
        tmp_path = Path(tmp)
        print("\n  📦 Repacking asar...")
        subprocess.run(
            ["npx", "asar", "extract", str(asar), str(tmp_path)],
            cwd=desktop, check=True, capture_output=True
        )

        # Replace dist/ with freshly built one
        shutil.rmtree(tmp_path / "dist", ignore_errors=True)
        shutil.copytree(desktop / "dist", tmp_path / "dist")

        subprocess.run(
            ["npx", "asar", "pack", str(tmp_path), str(new_asar)],
            cwd=desktop, check=True, capture_output=True
        )

    mb = new_asar.stat().st_size / 1_000_000
    print(f"  ✅ New asar: {mb:.1f} MB — {new_asar}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def apply() -> None:
    root = find_repo_root()
    if not root:
        print("❌ Could not find hermes-agent repo root (looking for apps/desktop/package.json)")
        print("   Run this from anywhere inside the hermes-agent repo.")
        sys.exit(1)

    print(f"📁 Repo root: {root}")

    # ── Step 0: Verify dependencies ─────────────────────────────────────
    storage_path = root / "apps/desktop/src/lib/storage.ts"
    storage_dir = root / "apps/desktop/src/lib/storage"
    if not storage_path.exists() and not storage_dir.exists():
        print("  ⚠️  @/lib/storage not found at expected path. The avatar store")
        print("     imports persistStringRecord / storedStringRecord from this module.")
        print("     These may have been renamed or removed in a newer version of Hermes.")
        print("     Check apps/desktop/src/lib/ for the actual storage helpers and")
        print("     update new-files/apps/desktop/src/store/avatar.ts accordingly.")
        proceed = input("  Continue anyway? [y/N] ").strip().lower()
        if proceed != 'y':
            sys.exit(1)

    # ── Step 1: Copy 3 new files ────────────────────────────────────────
    script_dir = Path(__file__).resolve().parent
    for dst_rel, src_rel in NEW_FILES.items():
        src = script_dir / src_rel
        dst = root / dst_rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        print(f"  ✅ {dst_rel}")

    # ── Step 2: Apply 5 file patches ────────────────────────────────────
    total_patches = 0
    for file_rel, replacements in PATCHES.items():
        path = root / file_rel
        if not path.exists():
            print(f"  ⚠️  {file_rel} not found — skipping")
            continue

        content = path.read_text(encoding="utf-8")
        for old, new in replacements:
            if old not in content:
                print(f"  ❌ Patch mismatch in {file_rel}")
                print(f"     Expected snippet not found. File may have changed upstream.")
                print(f"     If this happens, the feature may already be installed, or the")
                print(f"     source code has changed. Check https://github.com/nousresearch/"
                      f"hermes-agent/commits/main/apps/desktop/src/{file_rel}")
                sys.exit(1)
            content = content.replace(old, new, 1)

        path.write_text(content, encoding="utf-8")
        total_patches += len(replacements)
        print(f"  ✏️  {file_rel} ({len(replacements)} patches)")

    print(f"\n✅ {len(NEW_FILES)} new files + {total_patches} patches applied.\n")

    # ── Step 3: Rebuild ─────────────────────────────────────────────────
    desktop_dir = root / "apps" / "desktop"
    os.chdir(desktop_dir)

    print("📦 Installing deps...")
    if os.system("npm install --prefer-offline") != 0:
        print("❌ npm install failed")
        sys.exit(1)

    print("🔨 Building...")
    if os.system("npm run build") != 0:
        print("❌ Build failed")
        sys.exit(1)

    # ── Step 4: Repack asar (packaged builds only) ──────────────────────
    if is_packaged(root):
        repack_asar(root)
        print("\n🎉  Done! Close Hermes, then in PowerShell run:\n"
              "      cd apps\\desktop\\release\\win-unpacked\\resources\n"
              "      Remove-Item app.asar\n"
              "      Move-Item app.asar.new app.asar\n"
              "   Then restart Hermes to see avatars.")
    else:
        print("\n🎉  Done! Restart Hermes desktop to see the avatars.")


if __name__ == "__main__":
    apply()

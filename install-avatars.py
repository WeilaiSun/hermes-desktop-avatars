#!/usr/bin/env python3
"""Install Hermes Desktop Message Avatars.

Patches the Hermes Agent desktop app source to add circular message avatars
with editable names and images.  Run this from the hermes-agent repo root:

    python install-avatars.py

Requires: node + npm (for rebuild)
"""

import os
import sys
import shutil
from pathlib import Path

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

NEW_FILES = {
    "apps/desktop/src/store/avatar.ts": "new-files/apps/desktop/src/store/avatar.ts",
    "apps/desktop/src/components/chat/message-avatar.tsx": "new-files/apps/desktop/src/components/chat/message-avatar.tsx",
    "apps/desktop/src/components/chat/avatar-editor-dialog.tsx": "new-files/apps/desktop/src/components/chat/avatar-editor-dialog.tsx",
}

# ---------------------------------------------------------------------------
# Patches (old_string -> new_string) for each file
# ---------------------------------------------------------------------------

PATCHES = {
    "apps/desktop/src/components/assistant-ui/thread/user-message.tsx": [
        # === Import changes ===
        (
            "import { ActionBarPrimitive, BranchPickerPrimitive, MessagePrimitive, useAuiState } from '@assistant-ui/react'\n"
            "import { type FC, type ReactNode, useCallback, useRef, useState } from 'react'",

            "import { ActionBarPrimitive, BranchPickerPrimitive, MessagePrimitive, useAuiState } from '@assistant-ui/react'\n"
            "import { useStore } from '@nanostores/react'\n"
            "import { type FC, type ReactNode, useCallback, useRef, useState } from 'react'"
        ),
        (
            "import { UserMessageText } from '@/components/assistant-ui/thread/user-message-text'\n"
            "import { Codicon }",

            "import { UserMessageText } from '@/components/assistant-ui/thread/user-message-text'\n"
            "import { MessageAvatar } from '@/components/chat/message-avatar'\n"
            "import { Codicon }"
        ),
        (
            "import { cn } from '@/lib/utils'\n"
            "import { notifyThreadEditOpen } from '@/store/thread-scroll'",

            "import { cn } from '@/lib/utils'\n"
            "import { $avatarNames, DEFAULT_NAMES } from '@/store/avatar'\n"
            "import { notifyThreadEditOpen } from '@/store/thread-scroll'"
        ),
        # === Add userName hook ===
        (
            "  useResizeObserver(measureClamp, clampInnerRef)\n\n"
            "  // Injected background-process notification",

            "  useResizeObserver(measureClamp, clampInnerRef)\n\n"
            "  const userName = useStore($avatarNames).user || DEFAULT_NAMES.user\n\n"
            "  // Injected background-process notification"
        ),
        # === Wrap return in avatar row ===
        (
            "  return (\n"
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
            "            attachments={"
        ),
        # === Close wrapping divs ===
        (
            "        </ActionBarPrimitive.Root>\n"
            "      </StickyHumanMessageContainer>\n"
            "    </MessagePrimitive.Root>\n"
            "  )\n}",

            "        </ActionBarPrimitive.Root>\n"
            "      </StickyHumanMessageContainer>\n"
            "        </div>\n"
            "        <MessageAvatar clickToEdit role=\"user\" />\n"
            "      </div>\n"
            "    </MessagePrimitive.Root>\n"
            "  )\n}"
        ),
    ],

    "apps/desktop/src/components/assistant-ui/thread/assistant-message.tsx": [
        (
            "import { useStore } from '@nanostores/react'",

            "import { useStore as useNanostore } from '@nanostores/react'"
        ),
        (
            "import { TooltipIconButton } from '@/components/assistant-ui/tooltip-icon-button'\n"
            "import { PreviewAttachment } from '@/components/chat/preview-attachment'",

            "import { TooltipIconButton } from '@/components/assistant-ui/tooltip-icon-button'\n"
            "import { MessageAvatar } from '@/components/chat/message-avatar'\n"
            "import { PreviewAttachment } from '@/components/chat/preview-attachment'"
        ),
        (
            "import { $voicePlayback } from '@/store/voice-playback'\n"
            "",

            "import { $voicePlayback } from '@/store/voice-playback'\n"
            "import { $avatarNames, DEFAULT_NAMES } from '@/store/avatar'\n"
        ),
        (
            "  const voicePlayback = useStore($voicePlayback)",

            "  const voicePlayback = useNanostore($voicePlayback)"
        ),
        (
            "  const enterRef = useEnterAnimation(isRunning, `assistant-message:${messageId}`)\n\n"
            "  if (isPlaceholder) {",

            "  const enterRef = useEnterAnimation(isRunning, `assistant-message:${messageId}`)\n\n"
            "  const assistantName = useNanostore($avatarNames).assistant || DEFAULT_NAMES.assistant\n\n"
            "  if (isPlaceholder) {"
        ),
        (
            "  return (\n"
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
            "        >"
        ),
        (
            "        <AssistantFooter getMessageText={getMessageText} messageId={messageId} onBranchInNewChat={onBranchInNewChat} />\n"
            "      )}\n"
            "    </MessagePrimitive.Root>\n"
            "  )\n}",

            "        <AssistantFooter getMessageText={getMessageText} messageId={messageId} onBranchInNewChat={onBranchInNewChat} />\n"
            "      )}\n"
            "    </MessagePrimitive.Root>\n"
            "      </div>\n"
            "    </div>\n"
            "  )\n}"
        ),
    ],

    "apps/desktop/src/components/assistant-ui/thread/index.tsx": [
        (
            "import { UserMessage } from '@/components/assistant-ui/thread/user-message'\n"
            "import { Intro, type IntroProps } from '@/components/chat/intro'",

            "import { UserMessage } from '@/components/assistant-ui/thread/user-message'\n"
            "import { AvatarEditorDialog } from '@/components/chat/avatar-editor-dialog'\n"
            "import { Intro, type IntroProps } from '@/components/chat/intro'"
        ),
        (
            "import { type FC, useCallback, useMemo, useState } from 'react'\n"
            "",

            "import { type FC, useCallback, useMemo, useState } from 'react'\n"
            "import { useStore } from '@nanostores/react'\n"
        ),
        (
            "import { notifyError } from '@/store/notifications'",

            "import { notifyError } from '@/store/notifications'\n"
            "import { $avatarEditorOpen, closeAvatarEditor } from '@/store/avatar'"
        ),
        (
            "  >(null)\n\n"
            "  const closeRestoreConfirm",

            "  >(null)\n\n"
            "  const avatarEditorOpen = useStore($avatarEditorOpen)\n\n"
            "  const closeRestoreConfirm"
        ),
        (
            "        title={copy.restoreTitle}\n"
            "      />\n"
            "    </div>\n"
            "  )\n}",

            "        title={copy.restoreTitle}\n"
            "      />\n"
            "      <AvatarEditorDialog onClose={closeAvatarEditor} open={avatarEditorOpen} />\n"
            "    </div>\n"
            "  )\n}"
        ),
    ],

    "apps/desktop/src/styles.css": [
        (
            "@media (prefers-reduced-motion: reduce) {\n"
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
            "}\n\n"
            "/* ------------------------------------------------------------------ */\n"
            "/*  Message avatars                                                   */\n"
            "/* ------------------------------------------------------------------ */\n\n"
            ".message-avatar {\n"
            "  border-radius: 9999px;\n"
            "  overflow: hidden;\n"
            "}\n\n"
            ".avatar-fallback-ring {\n"
            "  box-shadow: 0 0 0 1px var(--ui-stroke-tertiary, rgba(255, 255, 255, 0.1));\n"
            "}\n\n"
            ".message-avatar-editable:focus-visible {\n"
            "  outline: 2px solid var(--dt-midground, var(--dt-primary));\n"
            "  outline-offset: 2px;\n"
            "}\n\n"
            "/* Fade the name label in on hover — subtle, not distracting. */\n"
            "[data-slot=\"message-row\"] .message-name-label {\n"
            "  opacity: 0;\n"
            "  transition: opacity 120ms ease;\n"
            "}\n\n"
            "[data-slot=\"message-row\"]:hover .message-name-label,\n"
            "[data-slot=\"message-row\"]:focus-within .message-name-label {\n"
            "  opacity: 1;\n"
            "}\n\n"
            "@media (prefers-reduced-motion: reduce) {\n"
            "  .message-name-label {\n"
            "    transition: none;\n"
            "  }\n"
            "}\n"
        ),
    ],
}


def find_repo_root():
    """Walk up from cwd to find hermes-agent repo root."""
    d = Path.cwd()
    for _ in range(10):
        if (d / "apps" / "desktop" / "package.json").exists():
            return d
        d = d.parent
    return None


def apply():
    root = find_repo_root()
    if not root:
        print("❌ Could not find hermes-agent repo root (looking for apps/desktop/package.json)")
        print("   Run this from anywhere inside the hermes-agent repo.")
        sys.exit(1)

    print(f"📁 Repo root: {root}")

    # Copy new files
    script_dir = Path(__file__).resolve().parent
    for dst_rel, src_rel in NEW_FILES.items():
        src = script_dir / src_rel
        dst = root / dst_rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        print(f"  ✅ {dst_rel}")

    # Apply patches
    patched = 0
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
                sys.exit(1)
            content = content.replace(old, new, 1)

        path.write_text(content, encoding="utf-8")
        patched += len(replacements)
        print(f"  ✏️  {file_rel} ({len(replacements)} patches)")

    print(f"\n✅ {len(NEW_FILES)} new files + {patched} patches applied.\n")

    # Rebuild
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

    print("\n🎉  Done! Restart Hermes desktop to see the avatars.")


if __name__ == "__main__":
    apply()

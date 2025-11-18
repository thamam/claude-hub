---
description: Copy the last 100 lines of output to clipboard
---

# Clipboard Copy Command

Copy the last 100 lines from the conversation output to the clipboard.

## Your Task

1. **Extract the last 100 lines**: Gather the last 100 lines of text from the most recent outputs in the conversation (code blocks, command outputs, file contents, or response text).

2. **Format the content**: Prepare the content in a clean, readable format suitable for pasting.

3. **Copy to clipboard**: Use the appropriate system clipboard utility to copy the content:
   - **Linux (X11)**: Use `xclip` or `xsel`
   - **Linux (Wayland)**: Use `wl-copy`
   - **macOS**: Use `pbcopy`
   - **Windows**: Use `clip`

4. **Fallback**: If no clipboard utility is available:
   - Display the content in a clearly marked code block
   - Inform the user they can manually select and copy it
   - Provide instructions for installing a clipboard utility

## Implementation

```bash
# Detect and use available clipboard utility
if command -v xclip >/dev/null 2>&1; then
    echo "$CONTENT" | xclip -selection clipboard
    echo "✓ Copied to clipboard using xclip"
elif command -v xsel >/dev/null 2>&1; then
    echo "$CONTENT" | xsel --clipboard --input
    echo "✓ Copied to clipboard using xsel"
elif command -v wl-copy >/dev/null 2>&1; then
    echo "$CONTENT" | wl-copy
    echo "✓ Copied to clipboard using wl-copy"
elif command -v pbcopy >/dev/null 2>&1; then
    echo "$CONTENT" | pbcopy
    echo "✓ Copied to clipboard using pbcopy"
elif command -v clip >/dev/null 2>&1; then
    echo "$CONTENT" | clip
    echo "✓ Copied to clipboard using clip"
else
    echo "⚠ No clipboard utility found. Displaying content for manual copy:"
    echo ""
    echo "To enable automatic clipboard copying, install one of these:"
    echo "  - Linux (X11): sudo apt-get install xclip"
    echo "  - Linux (Wayland): sudo apt-get install wl-clipboard"
    echo ""
    echo "--- Content (last 100 lines) ---"
    echo "$CONTENT"
    echo "--- End ---"
fi
```

## Process

1. Collect the last 100 lines from the most recent conversation outputs
2. Store it in a temporary location
3. Execute the clipboard copy command
4. Confirm success or provide the content for manual copying

Now, let me extract and copy the last 100 lines from our conversation output.

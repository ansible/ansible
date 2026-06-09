---
name: ide-setup
description: Configure IDE settings for Ansible development (VSCode, PyCharm)
argument-hint: vscode
user-invocable: true
---

# ide-setup

Automate IDE configuration for Ansible development.

## Overview

Configure VSCode for Ansible development with Python, YAML, and Jinja2 support.

## Prerequisites

Requires completed project setup (repository clone and Python virtualenv).

**Auto-detect:**

1. Check for `.git/config` with ansible repository
2. Look for virtualenv in standard locations
3. If either missing, offer to run `project-setup` skill first

## Workflow Checklist

```markdown
VSCode Setup Progress:
- [ ] Auto-detect repository and virtualenv paths
- [ ] Install VSCode extensions (Python, Ansible, YAML, Jinja)
- [ ] Create .vscode/settings.json with interpreter configuration
- [ ] Verify setup (syntax highlighting, interpreter)
```

## Procedure

## VSCode Setup

### Step 1: Gather Project Paths

**Auto-detect paths:**

1. Repository path:
   - Check current directory: `git remote -v | grep ansible/ansible`
   - If found: Use `pwd` as `<repo_path>`
   - If not: Search common locations or ask user

2. Virtualenv path:

   ```bash
   # Check $VIRTUAL_ENV first, then search common locations
   if [ -n "$VIRTUAL_ENV" ] && [ -x "$VIRTUAL_ENV/bin/python3" ]; then
     venv_path="$VIRTUAL_ENV"
   else
     # Search for activate scripts in common locations
     find . ~/.virtualenvs ~/venv -name activate -path "*/bin/activate" 2>/dev/null
   fi
   ```

   - If multiple found: Ask user which to use
   - If none found: Ask user for venv path
   - Store as `<venv_path>`

### Step 2: Install Extensions

**Required extensions:**
- `ms-python.python` - Python language support
- `redhat.ansible` - Ansible language support  
- `redhat.vscode-yaml` - YAML language support
- `wholroyd.jinja` - Jinja2 syntax highlighting

**Installation:**

1. Check if `code` command is available: `which code`

2. If available, install automatically:

   ```bash
   code --install-extension ms-python.python
   code --install-extension redhat.ansible
   code --install-extension redhat.vscode-yaml
   code --install-extension wholroyd.jinja
   ```

3. If `code` not found:
   - **macOS:** Instruct: Open VSCode, `Cmd+Shift+P` → "Shell Command: Install 'code' command in PATH"
   - **Linux:** Usually auto-installed; may need symlink
   - After setup, retry installation or provide manual instructions

### Step 3: Configure Workspace Settings

Create `.vscode/settings.json` with Python and Ansible configuration:

```json
{
    "python.defaultInterpreterPath": "<venv_path>/bin/python3",
    "python.terminal.activateEnvironment": true,
    "files.associations": {
        "*.yml": "ansible",
        "*.yaml": "ansible"
    },
    "ansible.python.interpreterPath": "<venv_path>/bin/python3",
    "[ansible]": {
        "editor.tabSize": 2,
        "editor.insertSpaces": true
    },
    "[yaml]": {
        "editor.tabSize": 2,
        "editor.insertSpaces": true
    }
}
```

**Note:** On Windows, use backslashes and escape them: `C:\\path\\to\\venv\\Scripts\\python.exe`

**Create the file:**
1. Ensure `.vscode/` directory exists: `mkdir -p <repo_path>/.vscode`
2. Write settings.json with actual paths substituted

### Step 4: Verify Setup

**Open project:** `code <repo_path>`

**Verify:**
1. Open Python file (e.g., `lib/ansible/cli/adhoc.py`) - check syntax highlighting
2. Check status bar shows correct Python interpreter (bottom-right)
3. Open YAML file (e.g., `test/integration/targets/*/tasks/main.yml`) - check Ansible highlighting
4. Verify extensions are enabled in Extensions panel

---

## Notes

- VSCode configuration is stored in `.vscode/settings.json` (workspace-specific)
- Extensions can also be installed manually via Extensions panel
- Python interpreter can be changed via status bar or Command Palette

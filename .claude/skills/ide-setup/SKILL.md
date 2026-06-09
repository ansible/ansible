---
name: ide-setup
description: Configure IDE settings for Ansible development (VSCode, PyCharm)
user-invocable: true
---

# ide-setup

Automate IDE configuration for Ansible development.

## Invocation

Users can invoke this skill by asking to:

- "Set up my IDE"
- "Configure VSCode for Ansible"
- "Configure PyCharm for Ansible"
- "Set up my development environment"

## Overview

This skill provides automated IDE configuration for Ansible development. Currently supports:
- VSCode
- PyCharm

## Prerequisites

### Project Setup

Before configuring your IDE, you must complete the project setup (repository clone and Python environment).

Ask: "Have you completed the project-setup? [yes/no]"

**If no:**
- Offer: "Would you like to run the project-setup skill first? [yes/no]"
  - If yes: Load and execute the project-setup skill
  - If no: Stop and inform them they must complete project-setup before IDE configuration

**If yes:**
- Continue to Step 1

## Procedure

### Step 1: Choose IDE

Ask the user which IDE they want to configure:
- VSCode
- PyCharm

Once the user specifies their choice, proceed to the corresponding IDE section below.

## IDE Configurations

### VSCode

**Trigger:** User asks to configure VSCode or Visual Studio Code.

**Procedure:**

#### Step 1: Gather Project Paths

**If the user came directly from project-setup:** The paths (`<repo_path>` and `<venv_path>`) are already known from that skill. Skip to Step 2.

**If the user did NOT come from project-setup:** Ask for the required paths:

Ask: "What is the path to your Ansible repository clone?"
- Store as `<repo_path>`

Ask: "What is the path to your Python virtualenv?"
- This should be the path to the venv directory (e.g., `/path/to/ansible` if created with `python3 -m venv ansible`)
- Store as `<venv_path>`

#### Step 2: Open Project in VSCode

1. Open VSCode with the project:
   - Run: `code <repo_path>`
   - Or instruct user to: "Open VSCode and use File → Open Folder, then select `<repo_path>`"

#### Step 3: Install Recommended Extensions

Recommend installing the following VSCode extensions for Ansible development:

**Python Support:**
- **Python** (ms-python.python) - Core Python language support
  - Provides IntelliSense, linting, debugging, code navigation

**Ansible Support:**
- **Ansible** (redhat.ansible) - Ansible language support
  - YAML syntax highlighting for Ansible
  - Ansible-specific autocompletion
  - Integration with ansible-lint

**YAML Support:**
- **YAML** (redhat.vscode-yaml) - YAML language support
  - Syntax highlighting and validation
  - Schema support

**Jinja2 Support:**
- **Jinja** (wholroyd.jinja) - Jinja2 template syntax highlighting
  - Or **Better Jinja** (samuelcolvin.jinjahtml) - Enhanced Jinja2 support

Ask: "Would you like me to install these extensions automatically using the `code` command? [yes/no]"

**If yes:**
1. Check if `code` command is available: `which code` (Mac/Linux) or `where code` (Windows)

   **If code command not found:**
   - Inform user: "The `code` command is not available in your PATH."
   - Provide instructions:
     - **Mac:** Open VSCode, press `Cmd+Shift+P`, type "Shell Command: Install 'code' command in PATH", and select it
     - **Linux:** Usually installed automatically. If not, create a symlink or add VSCode bin directory to PATH
     - **Windows:** Usually available after installation. If not, add VSCode installation directory to PATH
   - Ask: "After installing the `code` command, would you like me to try again? [yes/no]"
     - If yes: Retry the extension installation
     - If no: Provide manual installation instructions below

   **If code command found:**
   - Install extensions:

     ```bash
     code --install-extension ms-python.python
     code --install-extension redhat.ansible
     code --install-extension redhat.vscode-yaml
     code --install-extension wholroyd.jinja
     ```

   - Report success or any errors

**If no:**
- Provide manual installation instructions:
  - Open VSCode
  - Press `Cmd+Shift+P` (Mac) or `Ctrl+Shift+P` (Windows/Linux)
  - Type "Extensions: Install Extensions"
  - Search for and install each extension:
    - ms-python.python
    - redhat.ansible
    - redhat.vscode-yaml
    - wholroyd.jinja (or samuelcolvin.jinjahtml)

#### Step 4: Configure Python Interpreter

1. Open Command Palette: `Cmd+Shift+P` (Mac) or `Ctrl+Shift+P` (Windows/Linux)

2. Type: "Python: Select Interpreter"

3. Select "Enter interpreter path..." if the venv isn't automatically detected

4. Enter the path to the venv Python binary:
   - `<venv_path>/bin/python3` (Linux/Mac)
   - `<venv_path>\Scripts\python.exe` (Windows)

5. Verify the interpreter is set by checking the bottom-right status bar in VSCode

#### Step 5: Configure Workspace Settings

Create or update `.vscode/settings.json` in the repository with Python and Ansible-specific settings:

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

**Note:** Replace `<venv_path>` with the actual virtualenv path. On Windows, use backslashes and escape them (e.g., `"C:\\path\\to\\venv\\Scripts\\python.exe"`).

Ask: "Would you like me to create this settings file for you? [yes/no]"

**If yes:**
- Create `.vscode/` directory if it doesn't exist
- Write the settings.json file with the appropriate paths

**If no:**
- Provide the settings JSON and instruct them to create it manually

#### Step 6: Verification

Instruct the user to verify the setup:

1. Open a Python file from the repository (e.g., `lib/ansible/cli/adhoc.py`)
2. Check that syntax highlighting works
3. Check that the Python interpreter shown in the status bar matches the venv
4. Open a YAML file (e.g., a file in `test/integration/targets/*/tasks/main.yml`)
5. Verify Ansible syntax highlighting is active

Inform the user: "VSCode is now configured for Ansible development with Python, YAML, and Jinja2 support."

---

### PyCharm

**Trigger:** User asks to configure PyCharm.

**Procedure:**
[Reserved for future implementation]

---

## Notes

- Backup existing IDE configuration files before modifying
- Respect user's existing settings when possible
- Provide clear feedback about what was configured

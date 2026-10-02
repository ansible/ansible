---
name: project-setup
description: Assist the user in creating an Ansible project setup, cloning the ansible repo, and setting up a virtualenv
argument-hint: virtualenv
user-invocable: true
---

# project-setup

Automate Python project environment setup for Ansible using virtualenv.

## Overview

Set up Ansible development environment: clone repository and create virtualenv with editable install.

## Workflow Checklist

```markdown
Setup Progress:
- [ ] Locate or clone ansible repository
- [ ] Configure git remotes (upstream + origin)
- [ ] Create or locate virtualenv
- [ ] Install ansible in editable mode
```

## Procedure

### Step 1: Repository Setup

**Auto-detect or set up ansible repository:**

1. Check if current directory is the ansible repo:

   ```bash
   git remote -v 2>/dev/null | grep ansible/ansible
   ```

2. If not found, check common locations:
   - `~/ansible`
   - `~/projects/ansible`
   - `~/dev/ansible`
   - `~/projects/ansibledev/ansible`

3. If still not found, ask: "Where is your ansible repository clone? (or press enter to clone it now)"

4. If user wants to clone:
   - Ask: "Clone your fork or upstream? Provide fork URL or press enter for upstream"
   - If fork URL provided: `git clone <fork-url> ansible && cd ansible`
   - If upstream: `git clone https://github.com/ansible/ansible.git && cd ansible`

5. Store the repository path as `<repo_path>`

**Configure git remotes:**

1. Check remotes: `git remote -v`

2. Ensure `upstream` points to `ansible/ansible`:

   ```bash
   # Add upstream if missing
   git remote add upstream https://github.com/ansible/ansible.git 2>/dev/null || \
   # Update upstream if it exists but points elsewhere
   git remote set-url upstream https://github.com/ansible/ansible.git
   ```

3. Check if origin is a fork:
   - If origin points to `ansible/ansible`: Suggest setting origin to their fork for contributions
   - If origin is a fork: All set

### Step 2: virtualenv Setup

**Auto-detect or create virtualenv:**

1. Check for existing virtualenv:

   ```bash
   # Check $VIRTUAL_ENV first, then common venv locations
   for path in $VIRTUAL_ENV/bin/python3 ./ansible/bin/python3 ~/.virtualenvs/ansible/bin/python3 ~/venv/ansible/bin/python3; do
     if [ -x "$path" ]; then
       echo "Found: $path"
     fi
   done
   ```

2. If found: Ask "Use existing virtualenv at `<path>`? (or press enter to create new)"

3. If creating new or none found:
   - Ask: "Where should the virtualenv be created? (default: ./ansible)"
   - Ask: "Which Python to use? (default: python3)"
   - Create: `<python> -m venv <venv_name>`
   - Store venv python path: `<venv_path>/bin/python3`

**Install ansible in editable mode:**

```bash
<venv_python> -m pip install -e <repo_path> argcomplete
```

Where:
- `<venv_python>` is the path to the virtualenv's python3 binary
- `<repo_path>` is the ansible repository directory from Step 1

---

## Notes

- Always detect existing setup before proceeding to avoid conflicts
- Respect existing configuration files (don't overwrite without confirmation)
- Check for project-specific requirements files before creating defaults
- Provide feedback about what was created/configured

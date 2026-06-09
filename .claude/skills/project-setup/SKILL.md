---
name: project-setup
description: Assist the user in creating an Ansible project setup, cloning the ansible repo, and setting up a virtualenv
user-invocable: true
---

# project-setup

Automate Python project environment setup for Ansible using different tools.

## Invocation

Users can invoke this skill by asking to:

- "Set up the ansible project"
- "Initialize the development environment for ansible"
- "Set up Python virtualenv for ansible"
- "Configure the ansible project environment"

## Overview

This skill provides automated setup procedures for project setup of Ansible. Currently supports:
- virtualenv

Future expansion planned for:
- uv
- Other Python environment management tools

## Procedure

### Step 1: Repository Setup

Ask: "Have you already cloned your ansible repo? [yes/no]"

**If yes:**
1. Ask: "Is the current working directory the clone directory? [yes/no]"
   - If no: Ask for the location, change to that directory, and store as `<repo_path>`
   - If yes: Continue from current directory and store current directory as `<repo_path>`

2. Check git remotes using `git remote -v`
   - Verify `upstream` remote exists and points to `https://github.com/ansible/ansible.git` (or git@github.com:ansible/ansible.git)
     - If upstream doesn't exist: Create it with `git remote add upstream https://github.com/ansible/ansible.git`
     - If upstream exists but points elsewhere: Update it with `git remote set-url upstream https://github.com/ansible/ansible.git`

   - Check if `origin` points to a fork (not ansible/ansible)
     - If origin is their fork: Do nothing
     - If origin is ansible/ansible: Ask "What is your fork URL?" and run `git remote set-url origin <url>`

**If no:**
1. Ask: "Where would you like to clone the repository to?" (get path)

2. Change to this location (create directory if needed)

3. Ask: "Do you want to clone your fork? [yes/no]"

   **If yes:**
   - Ask: "What is your fork URL?"
   - Clone their fork: `git clone <fork-url> ansible`
   - Change into the cloned directory: `cd ansible`
   - Add upstream remote: `git remote add upstream https://github.com/ansible/ansible.git`
   - Store the clone path as `<repo_path>` for later use

   **If no:**
   - Clone upstream: `git clone https://github.com/ansible/ansible.git`
   - Change into the cloned directory: `cd ansible`
   - Store the clone path as `<repo_path>` for later use
   - Warn: Note: Cloning upstream directly will complicate contributions.
     This setup is fine for running ansible from git, but if you plan to
     contribute, you'll want to fork the repository and update your origin
     remote later.

### Step 2: Choose Setup Method

Ask the user which Python environment management tool they want to use:
- virtualenv
- (uv - coming soon)

Once the user specifies their choice, proceed to the corresponding method section below.

## Methods

### virtualenv

**Trigger:** User asks to set up Python virtualenv, create virtual environment, or initialize Python project.

**Procedure:**

#### virtualenv Setup

1. Ask: "Do you want to create a new virtualenv? [yes/no]"

   **If no:**
   - Ask: "What is the path to the python3 binary in your existing virtualenv?"
   - Store this path as `<python3_path>`

   **If yes:**
   - Ask: "Where do you want to create the virtual environment?"
   - Change directory to this path
   - Ask: "Which python binary do you want to use? (default: python3)"
   - If no answer or default chosen, use `python3`
   - Store this as `<python3_path>`
   - Create virtualenv: `<python3_path> -m venv ansible`
   - Update `<python3_path>` to point to the newly created venv: `ansible/bin/python3`

2. Install ansible in editable mode with dependencies:
   - Run: `<python3_path> -m pip install -e <path_to_repo_clone> argcomplete`
   - Note: `<path_to_repo_clone>` is the directory containing the ansible repository (from Step 1)

---

### uv

**Trigger:** User asks to set up project using uv.

**Procedure:**
[Reserved for future implementation]

---

## Notes

- Always detect existing setup before proceeding to avoid conflicts
- Respect existing configuration files (don't overwrite without confirmation)
- Check for project-specific requirements files before creating defaults
- Provide feedback about what was created/configured

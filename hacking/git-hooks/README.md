# Git Hooks for Ansible Development

This directory contains some sample git hooks that can help in ansible
development.

Place them in .git/hooks directory inside the ansible git repository.
This will activate them.  Alternatively you can create symbolic links
to them.   Make sure you give them permission to run (chmod +x <filename>).

### pre-commit hook

The pre commit hook adds some static code checks before your code is
checked in.  Python files are checked with flake8 and yaml files are
checked with yamllint.  You must have both of them installed and in
your pat (e.g. using pip).

Module files are checked with validate-modules which does both python
and ansible specific checks.  Again you must have the appropriate
dependencies installed.  Try it and fix if something is missing.

### post-checkout

The post checkout hook deletes all .pyc files.  This ensures that if
you check out an older version of a python file than the one you had
been using python will recompile it and you won't get strange and
difficult to debug errors.

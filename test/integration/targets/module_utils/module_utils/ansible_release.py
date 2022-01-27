# This file overrides the builtin ansible.module_utils.ansible_release file
# to test that it can be overridden. Previously this was facts.py but caused issues
# with dependencies that may need to execute a module that makes use of facts
data = 'overridden ansible_release.py'

Frequently Asked Questions
==========================

Q:
  Are there any variables available about the target host? Such as its
  ip addresses, OS, architecture, etc... Which ones?
 
A:
  Yes. You can find which ones by running the
  `setup module </docs/modules.html#setup>`_.


Q:
  Is there a variable which contains the name of the target host?

A:
  $inventory_hostname

  eg:
    local_action: shell ssh-keyscan $inventory_hostname >>~/.ssh/known_hosts 2>/dev/null


Q:
  Is there a variable which contains the name of the current playbook?

A:
  No.


Q:
  I registered a variable to use with only_if, but when that task is skipped
  then I get an error that the variable isn't defined. How can execute some
  tasks only if a given one has not been skipped?

A:
  When a task is skipped, variables do not get registered. Use "when_set"
  instead of only_if. See the `conditional execution </docs/playbooks2.html#conditional-execution-simplified>`_ section.


Q:
  What packages do I need to install to be able to run ansible?

A:
  On Debian, Ubuntu: python-yaml, python-paramiko and python-jinja2

  On RedHat, Fedora: PyYAML, python-paramiko and python-jinja2



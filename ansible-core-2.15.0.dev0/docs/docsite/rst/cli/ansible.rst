:source: adhoc.py

.. _ansible:

=======
ansible
=======


:strong:`Define and run a single task 'playbook' against a set of hosts`


.. contents::
   :local:
   :depth: 1


.. program:: ansible

Synopsis
========

.. code-block:: bash

   usage: ansible [-h] [--version] [-v] [-b] [--become-method BECOME_METHOD]
               [--become-user BECOME_USER]
               [-K | --become-password-file BECOME_PASSWORD_FILE]
               [-i INVENTORY] [--list-hosts] [-l SUBSET] [-P POLL_INTERVAL]
               [-B SECONDS] [-o] [-t TREE] [--private-key PRIVATE_KEY_FILE]
               [-u REMOTE_USER] [-c CONNECTION] [-T TIMEOUT]
               [--ssh-common-args SSH_COMMON_ARGS]
               [--sftp-extra-args SFTP_EXTRA_ARGS]
               [--scp-extra-args SCP_EXTRA_ARGS]
               [--ssh-extra-args SSH_EXTRA_ARGS]
               [-k | --connection-password-file CONNECTION_PASSWORD_FILE]
               [-C] [--syntax-check] [-D] [-e EXTRA_VARS]
               [--vault-id VAULT_IDS]
               [--ask-vault-password | --vault-password-file VAULT_PASSWORD_FILES]
               [-f FORKS] [-M MODULE_PATH] [--playbook-dir BASEDIR]
               [--task-timeout TASK_TIMEOUT] [-a MODULE_ARGS]
               [-m MODULE_NAME]
               pattern



Description
===========


is an extra-simple tool/framework/API for doing 'remote things'.
this command allows you to define and run a single task 'playbook' against a set of hosts


Common Options
==============




.. option:: --ask-vault-password, --ask-vault-pass

   ask for vault password


.. option:: --become-method <BECOME_METHOD>

   privilege escalation method to use (default=sudo), use `ansible-doc -t become -l` to list valid choices.


.. option:: --become-password-file <BECOME_PASSWORD_FILE>, --become-pass-file <BECOME_PASSWORD_FILE>

   Become password file


.. option:: --become-user <BECOME_USER>

   run operations as this user (default=root)


.. option:: --connection-password-file <CONNECTION_PASSWORD_FILE>, --conn-pass-file <CONNECTION_PASSWORD_FILE>

   Connection password file


.. option:: --list-hosts

   outputs a list of matching hosts; does not execute anything else


.. option:: --playbook-dir <BASEDIR>

   Since this tool does not use playbooks, use this as a substitute playbook directory. This sets the relative path for many features including roles/ group_vars/ etc.


.. option:: --private-key <PRIVATE_KEY_FILE>, --key-file <PRIVATE_KEY_FILE>

   use this file to authenticate the connection


.. option:: --scp-extra-args <SCP_EXTRA_ARGS>

   specify extra arguments to pass to scp only (e.g. -l)


.. option:: --sftp-extra-args <SFTP_EXTRA_ARGS>

   specify extra arguments to pass to sftp only (e.g. -f, -l)


.. option:: --ssh-common-args <SSH_COMMON_ARGS>

   specify common arguments to pass to sftp/scp/ssh (e.g. ProxyCommand)


.. option:: --ssh-extra-args <SSH_EXTRA_ARGS>

   specify extra arguments to pass to ssh only (e.g. -R)


.. option:: --syntax-check

   perform a syntax check on the playbook, but do not execute it


.. option:: --task-timeout <TASK_TIMEOUT>

   set task timeout limit in seconds, must be positive integer.


.. option:: --vault-id

   the vault identity to use


.. option:: --vault-password-file, --vault-pass-file

   vault password file


.. option:: --version

   show program's version number, config file location, configured module search path, module location, executable location and exit


.. option:: -B <SECONDS>, --background <SECONDS>

   run asynchronously, failing after X seconds (default=N/A)


.. option:: -C, --check

   don't make any changes; instead, try to predict some of the changes that may occur


.. option:: -D, --diff

   when changing (small) files and templates, show the differences in those files; works great with --check


.. option:: -K, --ask-become-pass

   ask for privilege escalation password


.. option:: -M, --module-path

   prepend colon-separated path(s) to module library (default={{ ANSIBLE_HOME ~ "/plugins/modules:/usr/share/ansible/plugins/modules" }})


.. option:: -P <POLL_INTERVAL>, --poll <POLL_INTERVAL>

   set the poll interval if using -B (default=15)


.. option:: -T <TIMEOUT>, --timeout <TIMEOUT>

   override the connection timeout in seconds (default=10)


.. option:: -a <MODULE_ARGS>, --args <MODULE_ARGS>

   The action's options in space separated k=v format: -a 'opt1=val1 opt2=val2' or a json string: -a '{"opt1": "val1", "opt2": "val2"}'


.. option:: -b, --become

   run operations with become (does not imply password prompting)


.. option:: -c <CONNECTION>, --connection <CONNECTION>

   connection type to use (default=smart)


.. option:: -e, --extra-vars

   set additional variables as key=value or YAML/JSON, if filename prepend with @


.. option:: -f <FORKS>, --forks <FORKS>

   specify number of parallel processes to use (default=5)


.. option:: -h, --help

   show this help message and exit


.. option:: -i, --inventory, --inventory-file

   specify inventory host path or comma separated host list. --inventory-file is deprecated


.. option:: -k, --ask-pass

   ask for connection password


.. option:: -l <SUBSET>, --limit <SUBSET>

   further limit selected hosts to an additional pattern


.. option:: -m <MODULE_NAME>, --module-name <MODULE_NAME>

   Name of the action to execute (default=command)


.. option:: -o, --one-line

   condense output


.. option:: -t <TREE>, --tree <TREE>

   log output to this directory


.. option:: -u <REMOTE_USER>, --user <REMOTE_USER>

   connect as this user (default=None)


.. option:: -v, --verbose

   Causes Ansible to print more debug messages. Adding multiple -v will increase the verbosity, the builtin plugins currently evaluate up to -vvvvvv. A reasonable level to start is -vvv, connection debugging might require -vvvv.







Environment
===========

The following environment variables may be specified.



:envvar:`ANSIBLE_CONFIG` -- Override the default ansible config file

Many more are available for most options in ansible.cfg


Files
=====


:file:`/etc/ansible/ansible.cfg` -- Config file, used if present

:file:`~/.ansible.cfg` -- User config file, overrides the default config if present

Author
======

Ansible was originally written by Michael DeHaan.

See the `AUTHORS` file for a complete list of contributors.


License
=======

Ansible is released under the terms of the GPLv3+ License.

See also
========

:manpage:`ansible(1)`,  :manpage:`ansible-config(1)`,  :manpage:`ansible-console(1)`,  :manpage:`ansible-doc(1)`,  :manpage:`ansible-galaxy(1)`,  :manpage:`ansible-inventory(1)`,  :manpage:`ansible-playbook(1)`,  :manpage:`ansible-pull(1)`,  :manpage:`ansible-vault(1)`,  
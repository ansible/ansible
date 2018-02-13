.. _ansible-playbook:

================
ansible-playbook
================


:strong:`Runs Ansible playbooks, executing the defined tasks on the targeted hosts.`


.. contents::
   :local:
   :depth: 2


.. program:: ansible-playbook

Synopsis
========

.. code-block:: bash

   ansible-playbook [options] playbook.yml [playbook2 ...]


Description
===========


the tool to run *Ansible playbooks*, which are a configuration and multinode deployment system.
See the project home page (https://docs.ansible.com) for more information.


Common Options
==============




.. option:: --ask-su-pass

   ask for su password (deprecated, use become)


.. option:: --ask-sudo-pass

   ask for sudo password (deprecated, use become)


.. option:: --ask-vault-pass

   ask for vault password


.. option:: --become-method <BECOME_METHOD>

   privilege escalation method to use (default=sudo), valid choices: [ sudo | su | pbrun | pfexec | doas | dzdo | ksu | runas | pmrun | enable ]


.. option:: --become-user <BECOME_USER>

   run operations as this user (default=root)


.. option:: --flush-cache

   clear the fact cache for every host in inventory


.. option:: --force-handlers

   run handlers even if a task fails


.. option:: --list-hosts

   outputs a list of matching hosts; does not execute anything else


.. option:: --list-tags

   list all available tags


.. option:: --list-tasks

   list all tasks that would be executed


.. option:: --private-key, --key-file

   use this file to authenticate the connection


.. option:: --scp-extra-args <SCP_EXTRA_ARGS>

   specify extra arguments to pass to scp only (e.g. -l)


.. option:: --sftp-extra-args <SFTP_EXTRA_ARGS>

   specify extra arguments to pass to sftp only (e.g. -f, -l)


.. option:: --skip-tags

   only run plays and tasks whose tags do not match these values


.. option:: --ssh-common-args <SSH_COMMON_ARGS>

   specify common arguments to pass to sftp/scp/ssh (e.g. ProxyCommand)


.. option:: --ssh-extra-args <SSH_EXTRA_ARGS>

   specify extra arguments to pass to ssh only (e.g. -R)


.. option:: --start-at-task <START_AT_TASK>

   start the playbook at the task matching this name


.. option:: --step

   one-step-at-a-time: confirm each task before running


.. option:: --syntax-check

   perform a syntax check on the playbook, but do not execute it


.. option:: --vault-id

   the vault identity to use


.. option:: --vault-password-file

   vault password file


.. option:: --version

   show program's version number and exit


.. option:: -C, --check

   don't make any changes; instead, try to predict some of the changes that may occur


.. option:: -D, --diff

   when changing (small) files and templates, show the differences in those files; works great with --check


.. option:: -K, --ask-become-pass

   ask for privilege escalation password


.. option:: -M, --module-path

   prepend colon-separated path(s) to module library (default=[u'/Users/sbutler/.ansible/plugins/modules', u'/usr/share/ansible/plugins/modules'])


.. option:: -R <SU_USER>, --su-user <SU_USER>

   run operations with su as this user (default=None) (deprecated, use become)


.. option:: -S, --su

   run operations with su (deprecated, use become)


.. option:: -T <TIMEOUT>, --timeout <TIMEOUT>

   override the connection timeout in seconds (default=10)


.. option:: -U <SUDO_USER>, --sudo-user <SUDO_USER>

   desired sudo user (default=root) (deprecated, use become)


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


.. option:: -s, --sudo

   run operations with sudo (nopasswd) (deprecated, use become)


.. option:: -t, --tags

   only run plays and tasks tagged with these values


.. option:: -u <REMOTE_USER>, --user <REMOTE_USER>

   connect as this user (default=None)


.. option:: -v, --verbose

   verbose mode (-vvv for more, -vvvv to enable connection debugging)







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


Copyright
=========

Copyright © 2017 Red Hat, Inc | Ansible.

Ansible is released under the terms of the GPLv3 License.

See also
========

:manpage:`ansible(1)`,  :manpage:`ansible-config(1)`,  :manpage:`ansible-console(1)`,  :manpage:`ansible-doc(1)`,  :manpage:`ansible-galaxy(1)`,  :manpage:`ansible-inventory(1)`,  :manpage:`ansible-playbook(1)`,  :manpage:`ansible-pull(1)`,  :manpage:`ansible-vault(1)`,  

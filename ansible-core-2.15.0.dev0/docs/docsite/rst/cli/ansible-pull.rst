:source: pull.py

.. _ansible-pull:

============
ansible-pull
============


:strong:`pulls playbooks from a VCS repo and executes them for the local host`


.. contents::
   :local:
   :depth: 1


.. program:: ansible-pull

Synopsis
========

.. code-block:: bash

   usage: ansible-pull [-h] [--version] [-v] [--private-key PRIVATE_KEY_FILE]
                    [-u REMOTE_USER] [-c CONNECTION] [-T TIMEOUT]
                    [--ssh-common-args SSH_COMMON_ARGS]
                    [--sftp-extra-args SFTP_EXTRA_ARGS]
                    [--scp-extra-args SCP_EXTRA_ARGS]
                    [--ssh-extra-args SSH_EXTRA_ARGS]
                    [-k | --connection-password-file CONNECTION_PASSWORD_FILE]
                    [--vault-id VAULT_IDS]
                    [--ask-vault-password | --vault-password-file VAULT_PASSWORD_FILES]
                    [-e EXTRA_VARS] [-t TAGS] [--skip-tags SKIP_TAGS]
                    [-i INVENTORY] [--list-hosts] [-l SUBSET]
                    [-M MODULE_PATH]
                    [-K | --become-password-file BECOME_PASSWORD_FILE]
                    [--purge] [-o] [-s SLEEP] [-f] [-d DEST] [-U URL]
                    [--full] [-C CHECKOUT] [--accept-host-key]
                    [-m MODULE_NAME] [--verify-commit] [--clean]
                    [--track-subs] [--check] [--diff]
                    [playbook.yml ...]



Description
===========


Used to pull a remote copy of ansible on each managed node,
each set to run via cron and update playbook source via a source repository.
This inverts the default *push* architecture of ansible into a *pull* architecture,
which has near-limitless scaling potential.

The setup playbook can be tuned to change the cron frequency, logging locations, and parameters to ansible-pull.
This is useful both for extreme scale-out as well as periodic remediation.
Usage of the 'fetch' module to retrieve logs from ansible-pull runs would be an
excellent way to gather and analyze remote logs from ansible-pull.


Common Options
==============




.. option:: --accept-host-key

   adds the hostkey for the repo url if not already added


.. option:: --ask-vault-password, --ask-vault-pass

   ask for vault password


.. option:: --become-password-file <BECOME_PASSWORD_FILE>, --become-pass-file <BECOME_PASSWORD_FILE>

   Become password file


.. option:: --check

   don't make any changes; instead, try to predict some of the changes that may occur


.. option:: --clean

   modified files in the working repository will be discarded


.. option:: --connection-password-file <CONNECTION_PASSWORD_FILE>, --conn-pass-file <CONNECTION_PASSWORD_FILE>

   Connection password file


.. option:: --diff

   when changing (small) files and templates, show the differences in those files; works great with --check


.. option:: --full

   Do a full clone, instead of a shallow one.


.. option:: --list-hosts

   outputs a list of matching hosts; does not execute anything else


.. option:: --private-key <PRIVATE_KEY_FILE>, --key-file <PRIVATE_KEY_FILE>

   use this file to authenticate the connection


.. option:: --purge

   purge checkout after playbook run


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


.. option:: --track-subs

   submodules will track the latest changes. This is equivalent to specifying the --remote flag to git submodule update


.. option:: --vault-id

   the vault identity to use


.. option:: --vault-password-file, --vault-pass-file

   vault password file


.. option:: --verify-commit

   verify GPG signature of checked out commit, if it fails abort running the playbook. This needs the corresponding VCS module to support such an operation


.. option:: --version

   show program's version number, config file location, configured module search path, module location, executable location and exit


.. option:: -C <CHECKOUT>, --checkout <CHECKOUT>

   branch/tag/commit to checkout. Defaults to behavior of repository module.


.. option:: -K, --ask-become-pass

   ask for privilege escalation password


.. option:: -M, --module-path

   prepend colon-separated path(s) to module library (default={{ ANSIBLE_HOME ~ "/plugins/modules:/usr/share/ansible/plugins/modules" }})


.. option:: -T <TIMEOUT>, --timeout <TIMEOUT>

   override the connection timeout in seconds (default=10)


.. option:: -U <URL>, --url <URL>

   URL of the playbook repository


.. option:: -c <CONNECTION>, --connection <CONNECTION>

   connection type to use (default=smart)


.. option:: -d <DEST>, --directory <DEST>

   absolute path of repository checkout directory (relative paths are not supported)


.. option:: -e, --extra-vars

   set additional variables as key=value or YAML/JSON, if filename prepend with @


.. option:: -f, --force

   run the playbook even if the repository could not be updated


.. option:: -h, --help

   show this help message and exit


.. option:: -i, --inventory, --inventory-file

   specify inventory host path or comma separated host list. --inventory-file is deprecated


.. option:: -k, --ask-pass

   ask for connection password


.. option:: -l <SUBSET>, --limit <SUBSET>

   further limit selected hosts to an additional pattern


.. option:: -m <MODULE_NAME>, --module-name <MODULE_NAME>

   Repository module name, which ansible will use to check out the repo. Choices are ('git', 'subversion', 'hg', 'bzr'). Default is git.


.. option:: -o, --only-if-changed

   only run the playbook if the repository has been updated


.. option:: -s <SLEEP>, --sleep <SLEEP>

   sleep for random interval (between 0 and n number of seconds) before starting. This is a useful way to disperse git requests


.. option:: -t, --tags

   only run plays and tasks tagged with these values


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
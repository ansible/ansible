:source: inventory.py

.. _ansible-inventory:

=================
ansible-inventory
=================


:strong:`None`


.. contents::
   :local:
   :depth: 1


.. program:: ansible-inventory

Synopsis
========

.. code-block:: bash

   usage: ansible-inventory [-h] [--version] [-v] [-i INVENTORY]
                         [--vault-id VAULT_IDS]
                         [--ask-vault-password | --vault-password-file VAULT_PASSWORD_FILES]
                         [--playbook-dir BASEDIR] [-e EXTRA_VARS] [--list]
                         [--host HOST] [--graph] [-y] [--toml] [--vars]
                         [--export] [--output OUTPUT_FILE]
                         [host|group]



Description
===========


used to display or dump the configured inventory as Ansible sees it


Common Options
==============




.. option:: --ask-vault-password, --ask-vault-pass

   ask for vault password


.. option:: --export

   When doing an --list, represent in a way that is optimized for export,not as an accurate representation of how Ansible has processed it


.. option:: --graph

   create inventory graph, if supplying pattern it must be a valid group name


.. option:: --host <HOST>

   Output specific host info, works as inventory script


.. option:: --list

   Output all hosts info, works as inventory script


.. option:: --list-hosts

   ==SUPPRESS==


.. option:: --output <OUTPUT_FILE>

   When doing --list, send the inventory to a file instead of to the screen


.. option:: --playbook-dir <BASEDIR>

   Since this tool does not use playbooks, use this as a substitute playbook directory. This sets the relative path for many features including roles/ group_vars/ etc.


.. option:: --toml

   Use TOML format instead of default JSON, ignored for --graph


.. option:: --vars

   Add vars to graph display, ignored unless used with --graph


.. option:: --vault-id

   the vault identity to use


.. option:: --vault-password-file, --vault-pass-file

   vault password file


.. option:: --version

   show program's version number, config file location, configured module search path, module location, executable location and exit


.. option:: -e, --extra-vars

   set additional variables as key=value or YAML/JSON, if filename prepend with @


.. option:: -h, --help

   show this help message and exit


.. option:: -i, --inventory, --inventory-file

   specify inventory host path or comma separated host list. --inventory-file is deprecated


.. option:: -l, --limit

   ==SUPPRESS==


.. option:: -v, --verbose

   Causes Ansible to print more debug messages. Adding multiple -v will increase the verbosity, the builtin plugins currently evaluate up to -vvvvvv. A reasonable level to start is -vvv, connection debugging might require -vvvv.


.. option:: -y, --yaml

   Use YAML format instead of default JSON, ignored for --graph







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
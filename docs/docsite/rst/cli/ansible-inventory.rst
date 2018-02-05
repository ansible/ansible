.. _ansible-inventory:

=================
ansible-inventory
=================


:strong:`None`


.. contents::
   :local:
   :depth: 2


.. program:: ansible-inventory

Synopsis
========

.. code-block:: bash

   ansible-inventory [options] [host|group]


Description
===========


used to display or dump the configured inventory as Ansible sees it


Common Options
==============




.. option:: --ask-vault-pass

   ask for vault password


.. option:: --graph

   create inventory graph, if supplying pattern it must be a valid group name


.. option:: --host <HOST>

   Output specific host info, works as inventory script


.. option:: --list

   Output all hosts info, works as inventory script


.. option:: --list-hosts

   outputs a list of matching hosts; does not execute anything else


.. option:: --playbook-dir <BASEDIR>

   Since this tool does not use playbooks, use this as a subsitute playbook directory.This sets the relative path for many features including roles/ group_vars/ etc.


.. option:: --vars

   Add vars to graph display, ignored unless used with --graph


.. option:: --vault-id

   the vault identity to use


.. option:: --vault-password-file

   vault password file


.. option:: --version

   show program's version number and exit


.. option:: -h, --help

   show this help message and exit


.. option:: -i, --inventory, --inventory-file

   specify inventory host path or comma separated host list. --inventory-file is deprecated


.. option:: -l <SUBSET>, --limit <SUBSET>

   further limit selected hosts to an additional pattern


.. option:: -v, --verbose

   verbose mode (-vvv for more, -vvvv to enable connection debugging)


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


Copyright
=========

Copyright © 2017 Red Hat, Inc | Ansible.

Ansible is released under the terms of the GPLv3 License.

See also
========

:manpage:`ansible(1)`,  :manpage:`ansible-config(1)`,  :manpage:`ansible-console(1)`,  :manpage:`ansible-doc(1)`,  :manpage:`ansible-galaxy(1)`,  :manpage:`ansible-inventory(1)`,  :manpage:`ansible-playbook(1)`,  :manpage:`ansible-pull(1)`,  :manpage:`ansible-vault(1)`,  

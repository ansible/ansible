.. _ansible-config:

==============
ansible-config
==============


:strong:`View, edit, and manage ansible configuration.`


.. contents::
   :local:
   :depth: 2


.. program:: ansible-config

Synopsis
========

.. code-block:: bash

   ansible-config [view|dump|list] [--help] [options] [ansible.cfg]


Description
===========


Config command line class


Common Options
==============




.. option:: --version

   show program's version number and exit


.. option:: -c <CONFIG_FILE>, --config <CONFIG_FILE>

   path to configuration file, defaults to first file found in precedence.


.. option:: -h, --help

   show this help message and exit


.. option:: -v, --verbose

   verbose mode (-vvv for more, -vvvv to enable connection debugging)






Actions
=======



.. program:: ansible-config list
.. _ansible_config_list:

list
----

list all current configs reading lib/constants.py and shows env and config file setting names





.. program:: ansible-config dump
.. _ansible_config_dump:

dump
----

Shows the current settings, merges ansible.cfg if specified





.. option:: --only-changed 

   Only show configurations that have changed from the default





.. program:: ansible-config view
.. _ansible_config_view:

view
----

Displays the current config file




.. program:: ansible-config


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

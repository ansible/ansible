:source: config.py

.. _ansible-config:

==============
ansible-config
==============


:strong:`View ansible configuration.`


.. contents::
   :local:
   :depth: 2


.. program:: ansible-config

Synopsis
========

.. code-block:: bash

   usage: ansible-config [-h] [--version] [-v] {list,dump,view,init} ...



Description
===========


Config command line class


Common Options
==============




.. option:: --version

   show program's version number, config file location, configured module search path, module location, executable location and exit


.. option:: -h, --help

   show this help message and exit


.. option:: -v, --verbose

   Causes Ansible to print more debug messages. Adding multiple -v will increase the verbosity, the builtin plugins currently evaluate up to -vvvvvv. A reasonable level to start is -vvv, connection debugging might require -vvvv.






Actions
=======



.. program:: ansible-config list
.. _ansible_config_list:

list
----

list and output available configs





.. option:: --format  <FORMAT>, -f  <FORMAT>

   Output format for list

.. option:: -c  <CONFIG_FILE>, --config  <CONFIG_FILE>

   path to configuration file, defaults to first file found in precedence.

.. option:: -t  <TYPE>, --type  <TYPE>

   Filter down to a specific plugin type.







.. program:: ansible-config dump
.. _ansible_config_dump:

dump
----

Shows the current settings, merges ansible.cfg if specified





.. option:: --format  <FORMAT>, -f  <FORMAT>

   Output format for dump

.. option:: --only-changed , --changed-only 

   Only show configurations that have changed from the default

.. option:: -c  <CONFIG_FILE>, --config  <CONFIG_FILE>

   path to configuration file, defaults to first file found in precedence.

.. option:: -t  <TYPE>, --type  <TYPE>

   Filter down to a specific plugin type.







.. program:: ansible-config view
.. _ansible_config_view:

view
----

Displays the current config file





.. option:: -c  <CONFIG_FILE>, --config  <CONFIG_FILE>

   path to configuration file, defaults to first file found in precedence.

.. option:: -t  <TYPE>, --type  <TYPE>

   Filter down to a specific plugin type.







.. program:: ansible-config init
.. _ansible_config_init:

init
----







.. option:: --disabled 

   Prefixes all entries with a comment character to disable them

.. option:: --format  <FORMAT>, -f  <FORMAT>

   Output format for init

.. option:: -c  <CONFIG_FILE>, --config  <CONFIG_FILE>

   path to configuration file, defaults to first file found in precedence.

.. option:: -t  <TYPE>, --type  <TYPE>

   Filter down to a specific plugin type.






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


License
=======

Ansible is released under the terms of the GPLv3+ License.

See also
========

:manpage:`ansible(1)`,  :manpage:`ansible-config(1)`,  :manpage:`ansible-console(1)`,  :manpage:`ansible-doc(1)`,  :manpage:`ansible-galaxy(1)`,  :manpage:`ansible-inventory(1)`,  :manpage:`ansible-playbook(1)`,  :manpage:`ansible-pull(1)`,  :manpage:`ansible-vault(1)`,  
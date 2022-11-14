:source: doc.py

.. _ansible-doc:

===========
ansible-doc
===========


:strong:`plugin documentation tool`


.. contents::
   :local:
   :depth: 1


.. program:: ansible-doc

Synopsis
========

.. code-block:: bash

   usage: ansible-doc [-h] [--version] [-v] [-M MODULE_PATH]
                   [--playbook-dir BASEDIR]
                   [-t {become,cache,callback,cliconf,connection,httpapi,inventory,lookup,netconf,shell,vars,module,strategy,test,filter,role,keyword}]
                   [-j] [-r ROLES_PATH]
                   [-e ENTRY_POINT | -s | -F | -l | --metadata-dump]
                   [--no-fail-on-errors]
                   [plugin ...]



Description
===========


displays information on modules installed in Ansible libraries.
It displays a terse listing of plugins and their short descriptions,
provides a printout of their DOCUMENTATION strings,
and it can create a short "snippet" which can be pasted into a playbook.


Common Options
==============




.. option:: --metadata-dump

   **For internal use only** Dump json metadata for all entries, ignores other options.


.. option:: --no-fail-on-errors

   **For internal use only** Only used for --metadata-dump. Do not fail on errors. Report the error message in the JSON instead.


.. option:: --playbook-dir <BASEDIR>

   Since this tool does not use playbooks, use this as a substitute playbook directory. This sets the relative path for many features including roles/ group_vars/ etc.


.. option:: --version

   show program's version number, config file location, configured module search path, module location, executable location and exit


.. option:: -F, --list_files

   Show plugin names and their source files without summaries (implies --list). A supplied argument will be used for filtering, can be a namespace or full collection name.


.. option:: -M, --module-path

   prepend colon-separated path(s) to module library (default={{ ANSIBLE_HOME ~ "/plugins/modules:/usr/share/ansible/plugins/modules" }})


.. option:: -e <ENTRY_POINT>, --entry-point <ENTRY_POINT>

   Select the entry point for role(s).


.. option:: -h, --help

   show this help message and exit


.. option:: -j, --json

   Change output into json format.


.. option:: -l, --list

   List available plugins. A supplied argument will be used for filtering, can be a namespace or full collection name.


.. option:: -r, --roles-path

   The path to the directory containing your roles.


.. option:: -s, --snippet

   Show playbook snippet for these plugin types: inventory, lookup, module


.. option:: -t <TYPE>, --type <TYPE>

   Choose which plugin type (defaults to "module"). Available plugin types are : ('become', 'cache', 'callback', 'cliconf', 'connection', 'httpapi', 'inventory', 'lookup', 'netconf', 'shell', 'vars', 'module', 'strategy', 'test', 'filter', 'role', 'keyword')


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
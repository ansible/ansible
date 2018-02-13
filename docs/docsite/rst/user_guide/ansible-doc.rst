.. _ansible-doc:

===========
ansible-doc
===========


:strong:`plugin documentation tool`


.. contents::
   :local:
   :depth: 2


.. program:: ansible-doc

Synopsis
========

.. code-block:: bash

   ansible-doc [-l|-F|-s] [options] [-t <plugin type> ] [plugin]


Description
===========


displays information on modules installed in Ansible libraries.
It displays a terse listing of plugins and their short descriptions,
provides a printout of their DOCUMENTATION strings,
and it can create a short "snippet" which can be pasted into a playbook.


Common Options
==============




.. option:: --version

   show program's version number and exit


.. option:: -F, --list_files

   Show plugin names and their source files without summaries (implies --list)


.. option:: -M, --module-path

   prepend colon-separated path(s) to module library (default=[u'/Users/sbutler/.ansible/plugins/modules', u'/usr/share/ansible/plugins/modules'])


.. option:: -a, --all

   **For internal testing only** Show documentation for all plugins.


.. option:: -h, --help

   show this help message and exit


.. option:: -l, --list

   List available plugins


.. option:: -s, --snippet

   Show playbook snippet for specified plugin(s)


.. option:: -t <TYPE>, --type <TYPE>

   Choose which plugin type (defaults to "module")


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

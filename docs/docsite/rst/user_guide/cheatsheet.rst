.. _cheatsheet:

**********************
Ansible CLI cheatsheet
**********************

This page shows one or more examples of each Ansible command line utility with some common flags added and a link to the full documentation for the command. This page offers a quick reminder of some common use cases only - it may be out of date or incomplete or both. For canonical documentation, follow the links to the CLI pages.

.. contents::
   :local:

ansible-playbook
================

.. code-block:: bash

   ansible-playbook -i /path/to/my_inventory_file -u my_connection_user -k /path/to/my_ssh_key -f 3 -T 30 -t my_tag -m /path/to/my_modules -b -K my_playbook.yml

Loads ``my_playbook.yml`` from the current working directory and:
  - ``-i`` - uses ``my_inventory_file`` in the path provided for inventory.
  - ``-u`` - connects over SSH as ``my_connection_user``.
  - ``-k`` - uses ``my_ssh_key`` in the path provided for authentication.
  - ``-f`` - allocates 3 forks.
  - ``-T`` - sets a 30-second timeout.
  - ``-t`` - runs only tasks marked with ``my_tag``.
  - ``-m`` - loads local modules from ``/path/to/my/modules``.
  - ``-b`` - executes with elevated privileges (uses become).
  - ``-K`` - prompts the user for the become password.

See :ref:`ansible-playbook` for detailed documentation.


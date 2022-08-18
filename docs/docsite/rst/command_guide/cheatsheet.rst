.. _cheatsheet:

**********************
Ansible CLI cheatsheet
**********************

This page shows one or more examples of each Ansible command line utility with some common flags added and a link to the full documentation for the command.
This page offers a quick reminder of some common use cases only - it may be out of date or incomplete or both.
For canonical documentation, follow the links to the CLI pages.

.. contents::
   :local:

ansible-playbook
================

.. code-block:: bash

   ansible-playbook -i /path/to/my_inventory_file -u my_connection_user -k -f 3 -T 30 -t my_tag -m /path/to/my_modules -b -K my_playbook.yml

Loads ``my_playbook.yml`` from the current working directory and:
  - ``-i`` - uses ``my_inventory_file`` in the path provided for :ref:`inventory <intro_inventory>` to match the :ref:`pattern <intro_patterns>`.
  - ``-u`` - connects :ref:`over SSH <connections>` as ``my_connection_user``.
  - ``-k`` - asks for password which is then provided to SSH authentication.
  - ``-f`` - allocates 3 :ref:`forks <playbooks_strategies>`.
  - ``-T`` - sets a 30-second timeout.
  - ``-t`` - runs only tasks marked with the :ref:`tag <tags>` ``my_tag``.
  - ``-m`` - loads :ref:`local modules <developing_locally>` from ``/path/to/my/modules``.
  - ``-b`` - executes with elevated privileges (uses :ref:`become <become>`).
  - ``-K`` - prompts the user for the become password.

See :ref:`ansible-playbook` for detailed documentation.


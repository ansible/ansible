bin-symlinks
============

The ``bin/`` directory in Ansible must contain only symbolic links to executable files.
These files must reside in the ``lib/ansible/`` or ``test/lib/ansible_test/`` directories.

This is required to allow ``ansible-test`` to work with containers and remote hosts when running from an installed version of Ansible.

Symlinks for each entry point in ``bin/`` must also be present in ``test/lib/ansible_test/_data/injector/``.
Each symlink should point to the ``python.py`` script in the same directory.
This facilitates running with the correct Python interpreter and enabling code coverage.

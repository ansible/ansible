bin-symlinks
============

The ``bin/`` directory in Ansible must contain only symbolic links to executable files.
These files must reside in the ``lib/ansible/`` or ``test/lib/ansible_test/`` directories.

This is required to allow ``ansible-test`` to work with containers and remote hosts when running from an installed version of Ansible.

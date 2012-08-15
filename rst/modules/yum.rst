.. _yum:

yum
```

Will install, upgrade, remove, and list packages with the yum package manager.

+--------------------+----------+---------+----------------------------------------------------------------------------+
| parameter          | required | default | comments                                                                   |
+====================+==========+=========+============================================================================+
| name               | yes      |         | package name, or package specifier with version, like 'name-1.0'           |
+--------------------+----------+---------+----------------------------------------------------------------------------+
| state              |          | present | 'present', 'latest', or 'absent'.                                          |
+--------------------+----------+---------+----------------------------------------------------------------------------+
| list               |          |         | various non-idempotent commands for usage with /usr/bin/ansible and not    |
|                    |          |         | playbooks.  See examples below.                                            |
+--------------------+----------+---------+----------------------------------------------------------------------------+

Example action from Ansible :doc:`playbooks`::

    yum name=httpd state=latest
    yum name=httpd state=removed
    yum name=httpd state=installed

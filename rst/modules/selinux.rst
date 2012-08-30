.. _selinux:

selinux
```````

.. versionadded:: 0.7

Configures the SELinux mode and policy.  A reboot may be required after usage.  Ansible will not issue this reboot but
will let you know when it is required.

+--------------------+----------+---------------------+----------------------------------------------------------------------------+
| parameter          | required | default             | comments                                                                   |
+====================+==========+=====================+============================================================================+
| policy             | yes      |                     | name of the SELinux policy to use (example: 'targetted')                   |
+--------------------+----------+---------------------+----------------------------------------------------------------------------+
| state              | yes      |                     | the SELinux mode.  'enforcing', 'permissive', or 'disabled'                |
+--------------------+----------+---------------------+----------------------------------------------------------------------------+
| conf               | no       | /etc/selinux/config | path to the SELinux configuration file, if non-standard                    |
+--------------------+----------+---------------------+----------------------------------------------------------------------------+

Example from Ansible :doc:`playbooks`::

    selinux policy=targetted state=enforcing
    selinux policy=targetted state=disabled


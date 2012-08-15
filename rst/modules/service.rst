.. _service:

service
```````

Controls services on remote machines.

+--------------------+----------+---------+----------------------------------------------------------------------------+
| parameter          | required | default | comments                                                                   |
+====================+==========+=========+============================================================================+
| name               | yes      |         | name of the service                                                        |
+--------------------+----------+---------+----------------------------------------------------------------------------+
| state              | no       | started | 'started', 'stopped', 'reloaded', or 'restarted'.  Started/stopped are     |
|                    |          |         | idempotent actions that will not run commands unless neccessary.           |
|                    |          |         | 'restarted' will always bounce the service, 'reloaded' will always reload. |
+--------------------+----------+---------+----------------------------------------------------------------------------+
| enabled            | no       |         | Whether the service should start on boot.  Either 'yes' or 'no'.           |
+--------------------+----------+---------+----------------------------------------------------------------------------+

Example action from Ansible :doc:`playbooks`::

    service name=httpd state=started
    service name=httpd state=stopped
    service name=httpd state=restarted
    service name=httpd state=reloaded

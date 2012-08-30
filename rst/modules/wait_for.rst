.. _wait_for:

wait_for
````````

.. versionadded:: 0.7

Waits for a given port to become accessible (or inaccessible) on a local or remote server.

This is useful for when services are not immediately available after their init scripts return -- which is true of certain
Java application servers.  It is also useful when starting guests with the virt module and 
needing to pause until they are ready.

+--------------------+----------+-----------+----------------------------------------------------------------------------+
| parameter          | required | default   | comments                                                                   |
+====================+==========+===========+============================================================================+
| host               | no       | 127.0.0.1 | hostname or IP to wait for                                                 |
+--------------------+----------+-----------+----------------------------------------------------------------------------+
| timeout            | no       | 300       | maximum number of seconds to wait                                          |
+--------------------+----------+-----------+----------------------------------------------------------------------------+
| delay              | no       | 0         | number of seconds to wait before starting to poll                          |
+--------------------+----------+-----------+----------------------------------------------------------------------------+
| port               | yes      |           | port to poll for openness or closedness                                    |
+--------------------+----------+-----------+----------------------------------------------------------------------------+
| state              | no       | started   | either 'started', or 'stopped' depending on whether the module should poll |
|                    |          |           | for the port being open or closed.                                         |
+--------------------+----------+-----------+----------------------------------------------------------------------------+

Example from Ansible :doc:`playbooks`::

    wait_for port=8080 delay=10


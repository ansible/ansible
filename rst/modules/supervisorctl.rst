.. _supervisorctl:

supervisorctl
`````````````

.. versionadded:: 0.7

Manage the state of a program or group of programs running via Supervisord

+--------------------+----------+---------+----------------------------------------------------------------------------+
| parameter          | required | default | comments                                                                   |
+====================+==========+=========+============================================================================+
| name               | yes      |         | The name of the supervisord program/process to manage                      |
+--------------------+----------+---------+----------------------------------------------------------------------------+
| state              | yes      |         | 'started', 'stopped' or 'restarted'                                        |
+--------------------+----------+---------+----------------------------------------------------------------------------+

Example action from a playbook::

    supervisorctl name=my_app state=started

.. _copy:

copy
````

The copy module moves a file on the local box to remote locations.  In addition to the options
listed below, the arguments available to the `file` module can also be passed to the copy
module.

+--------------------+----------+---------+----------------------------------------------------------------------------+
| parameter          | required | default | comments                                                                   |
+====================+==========+=========+============================================================================+
| src                | yes      |         | Local path to a file to copy to the remote server, can be absolute or      |
|                    |          |         | relative.                                                                  |
+--------------------+----------+---------+----------------------------------------------------------------------------+
| dest               | yes      |         | Remote absolute path where the file should end up                          |
+--------------------+----------+---------+----------------------------------------------------------------------------+
| OTHERS             |          |         | All arguments the file module takes are also supported                     |
+--------------------+----------+---------+----------------------------------------------------------------------------+

Example action from Ansible :doc:`playbooks`::

    copy src=/srv/myfiles/foo.conf dest=/etc/foo.conf owner=foo group=foo mode=0644

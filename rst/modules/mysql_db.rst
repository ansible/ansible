.. _mysql_db:

mysql_db
````````

.. versionadded:: 0.6

Add or remove MySQL databases from a remote host.

Requires the MySQLdb Python package on the remote host. For Ubuntu, this is as easy as
apt-get install python-mysqldb.

+--------------------+----------+-----------+-----------------------------------------------------------------------------+
| parameter          | required | default   | comments                                                                    |
+====================+==========+===========+=============================================================================+
| name               | yes      |           | name of the database to add or remove                                       |
+--------------------+----------+-----------+-----------------------------------------------------------------------------+
| login_user         | no       |           | user name used to authenticate with                                         |
+--------------------+----------+-----------+-----------------------------------------------------------------------------+
| login_password     | no       |           | password used to authenticate with                                          |
+--------------------+----------+-----------+-----------------------------------------------------------------------------+
| login_host         | no       | localhost | host running the database                                                   |
+--------------------+----------+-----------+-----------------------------------------------------------------------------+
| state              | no       | present   | 'absent' or 'present'                                                       |
+--------------------+----------+-----------+-----------------------------------------------------------------------------+
| collation          | no       |           | collation mode                                                              |
+--------------------+----------+-----------+-----------------------------------------------------------------------------+
| encoding           | no       |           | encoding mode                                                               |
+--------------------+----------+-----------+-----------------------------------------------------------------------------+

Both 'login_password' and 'login_username' are required when you are passing credentials.
If none are present, the module will attempt to read the credentials from ~/.my.cnf, and
finally fall back to using the MySQL default login of 'root' with no password.

Example action from Ansible :doc:`playbooks`::

   - name: Create database
     action: mysql_db db=bobdata state=present

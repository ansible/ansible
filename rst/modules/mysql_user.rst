mysql_user
``````````

.. versionadded:: 0.6

Adds or removes a user from a MySQL database.

Requires the MySQLdb Python package on the remote host. For Ubuntu, this is as easy as
apt-get install python-mysqldb.

+--------------------+----------+------------+----------------------------------------------------------------------------+
| parameter          | required | default    | comments                                                                   |
+====================+==========+============+============================================================================+
| name               | yes      |            | name of the user (role) to add or remove                                   |
+--------------------+----------+------------+----------------------------------------------------------------------------+
| password           | no       |            | set the user's password                                                    |
+--------------------+----------+------------+----------------------------------------------------------------------------+
| host               | no       | localhost  | the 'host' part of the MySQL username                                      |
+--------------------+----------+------------+----------------------------------------------------------------------------+
| login_user         | no       |            | user name used to authenticate with                                        |
+--------------------+----------+------------+----------------------------------------------------------------------------+
| login_password     | no       |            | password used to authenticate with                                         |
+--------------------+----------+------------+----------------------------------------------------------------------------+
| login_host         | no       | localhost  | host running MySQL.                                                        |
+--------------------+----------+------------+----------------------------------------------------------------------------+
| priv               | no       |            | MySQL privileges string in the format: db.table:priv1,priv2                |
+--------------------+----------+------------+----------------------------------------------------------------------------+
| state              | no       | present    | 'absent' or 'present'                                                      |
+--------------------+----------+------------+----------------------------------------------------------------------------+

Both 'login_password' and 'login_username' are required when you are passing credentials.
If none are present, the module will attempt to read the credentials from ~/.my.cnf, and
finally fall back to using the MySQL default login of 'root' with no password.

Example privileges string format:

    mydb.*:INSERT,UPDATE/anotherdb.*:SELECT/yetanotherdb.*:ALL

Example action from Ansible :doc:`playbooks`::

    - name: Create database user
      action: mysql_user name=bob passwd=12345 priv=*.*:ALL state=present

    - name: Ensure no user named 'sally' exists, also passing in the auth credentials.
      action: mysql_user login_user=root login_password=123456 name=sally state=absent

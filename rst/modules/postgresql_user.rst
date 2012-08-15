.. _postgresql_user:

postgresql_user
```````````````

.. versionadded:: 0.6

Add or remove PostgreSQL users (roles) from a remote host, and grant the users
access to an existing database.

The default authentication assumes that you are either logging in as or
sudo'ing to the postgres account on the host.

This module uses psycopg2, a Python PostgreSQL database adapter. You must
ensure that psycopg2 is installed on the host before using this module. If
the remote host is the PostgreSQL server (which is the default case), then
PostgreSQL must also be installed on the remote host. For Ubuntu-based systems,
install the postgresql, libpq-dev, and python-psycopg2 packages on the remote
host before using this module.

+--------------------+----------+----------+----------------------------------------------------------------------------+
| parameter          | required | default  | comments                                                                   |
+====================+==========+==========+============================================================================+
| name               | yes      |          | name of the user (role) to add or remove                                   |
+--------------------+----------+----------+----------------------------------------------------------------------------+
| password           | yes      |          | set the user's password                                                    |
+--------------------+----------+----------+----------------------------------------------------------------------------+
| db                 | yes      |          | name of an existing database to grant user access to                       |
+--------------------+----------+----------+----------------------------------------------------------------------------+
| login_user         | no       | postgres | user (role) used to authenticate with PostgreSQL                           |
+--------------------+----------+----------+----------------------------------------------------------------------------+
| login_password     | no       |          | password used to authenticate with PostgreSQL                              |
+--------------------+----------+----------+----------------------------------------------------------------------------+
| login_host         | no       |          | host running PostgreSQL. Default (blank) implies localhost                 |
+--------------------+----------+----------+----------------------------------------------------------------------------+
| state              |          | present  | 'absent' or 'present'                                                      |
+--------------------+----------+----------+----------------------------------------------------------------------------+


Example action from Ansible :doc:`playbooks`::

    postgresql_user db=acme user=django password=ceec4eif7ya

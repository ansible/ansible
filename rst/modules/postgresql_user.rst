.. _postgresql_user:

postgresql_user
```````````````

.. versionadded:: 0.6

Add or remove PostgreSQL users (roles) from a remote host and, optionally, grant the users
access to an existing database or tables.

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
| db                 | no       |          | name of database where permissions will be granted                         |
+--------------------+----------+----------+----------------------------------------------------------------------------+
| priv               | no       |          | PostgreSQL privileges string in the format: table:priv1,priv2              |
+--------------------+----------+----------+----------------------------------------------------------------------------+
| fail_on_user       | no       | yes      | if yes, fail when user can't be removed. Otherwise just log and continue   |
+--------------------+----------+----------+----------------------------------------------------------------------------+
| login_user         | no       | postgres | user (role) used to authenticate with PostgreSQL                           |
+--------------------+----------+----------+----------------------------------------------------------------------------+
| login_password     | no       |          | password used to authenticate with PostgreSQL                              |
+--------------------+----------+----------+----------------------------------------------------------------------------+
| login_host         | no       |          | host running PostgreSQL. Default (blank) implies localhost                 |
+--------------------+----------+----------+----------------------------------------------------------------------------+
| state              |          | present  | 'absent' or 'present'                                                      |
+--------------------+----------+----------+----------------------------------------------------------------------------+

The fundamental function of the module is to create, or delete, roles from a PostgreSQL cluster.
Privilege assignment, or removal, is an optional step, which works on one database at a time.
This allows for the module to be called several times in the same module to modify the permissions on
different databases, or to grant permissions to already existing users.

A user cannot be removed untill all the privileges have been stripped from the user. In such situation,
if the module tries to remove the user it will fail. To avoid this from happening the *fail_on_user* option
signals the module to try to remove the user, but if not possible keep going; the module will report if changes
happened and separately if the user was removed or not.

Example privileges string format:

    INSERT,UPDATE/table:SELECT/anothertable:ALL

Example action from Ansible :doc:`playbooks`::

    - name: Create django user and grant access to database and products table
      postgresql_user db=acme user=django password=ceec4eif7ya priv=CONNECT/products:ALL

    - name: Remove test user privileges from acme
      postgresql_user db=acme user=test priv=ALL/products:ALL state=absent fail_on_user=no
    - name: Remove test user from test database and the cluster
      postgresql_user db=test user=test priv=ALL state=absent

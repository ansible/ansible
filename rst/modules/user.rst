.. _user:

user
````

Creates user accounts, manipulates existing user accounts, and removes user accounts.

+--------------------+----------+---------+----------------------------------------------------------------------------+
| parameter          | required | default | comments                                                                   |
+====================+==========+=========+============================================================================+
| name               | yes      |         | name of the user to create, remove, or edit                                |
+--------------------+----------+---------+----------------------------------------------------------------------------+
| comment            |          |         | optionally sets the description of the user                                |
+--------------------+----------+---------+----------------------------------------------------------------------------+
| uid                |          |         | optionally sets the uid of the user                                        |
+--------------------+----------+---------+----------------------------------------------------------------------------+
| group              |          |         | optionally sets the user's primary group (takes a group name)              |
+--------------------+----------+---------+----------------------------------------------------------------------------+
| groups             |          |         | puts the user in this comma-delimited list of groups                       |
+--------------------+----------+---------+----------------------------------------------------------------------------+
| append             |          | no      | if 'yes', will only add groups, not set them to just the list in 'groups'  |
+--------------------+----------+---------+----------------------------------------------------------------------------+
| shell              |          |         | optionally set the user's shell                                            |
+--------------------+----------+---------+----------------------------------------------------------------------------+
| createhome         |          | yes     | unless 'no', a home directory will be made for the user                    |
+--------------------+----------+---------+----------------------------------------------------------------------------+
| home               |          |         | sets where the user's homedir should be, if not the default                |
+--------------------+----------+---------+----------------------------------------------------------------------------+
| password           |          |         | optionally set the user's password to this crypted value.  See the user's  |
|                    |          |         | example in the github examples directory for what this looks like in a     |
|                    |          |         | playbook                                                                   |
+--------------------+----------+---------+----------------------------------------------------------------------------+
| state              |          | present | when 'absent', removes the user.                                           |
+--------------------+----------+---------+----------------------------------------------------------------------------+
| system             |          | no      | only when initially creating, setting this to 'yes' makes the user a       |
|                    |          |         | system account.  This setting cannot be changed on existing users.         |
+--------------------+----------+---------+----------------------------------------------------------------------------+
| force              |          | no      | when used with state=absent, behavior is as with userdel --force           |
+--------------------+----------+---------+----------------------------------------------------------------------------+
| remove             |          | no      | when used with state=remove, behavior is as with userdel --remove          |
+--------------------+----------+---------+----------------------------------------------------------------------------+

Example action from Ansible :doc:`playbooks`::

    user name=mdehaan comment=awesome password=awWxVV.JvmdHw createhome=yes
    user name=mdehaan groups=wheel,skynet
    user name=mdehaan state=absent force=yes

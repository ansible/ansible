.. _lineinfile:

lineinfile
``````````

.. versionadded:: 0.7

This module will search a file for a line, and ensure that it is present or
absent.

This is primarily useful when you only want to change a single line in a file.
For other cases, see the copy or template modules.

+--------------------+----------+---------+----------------------------------------------------------------------------+
| parameter          | required | default | comments                                                                   |
+====================+==========+=========+============================================================================+
| state              | no       | present | 'absent' or 'present'                                                      |
+--------------------+----------+---------+----------------------------------------------------------------------------+
| name               | yes      |         | The file to modify.                                                        |
+--------------------+----------+---------+----------------------------------------------------------------------------+
| regexp             | yes      |         | The regular expression to look for in the file. For state=present, the     |
|                    |          |         | pattern to replace. For state=absent, the pattern of the line to           |
|                    |          |         | remove.                                                                    |
+--------------------+----------+---------+----------------------------------------------------------------------------+
| line               | maybe    |         | Required for state=present. The line to insert/replace into the file. Must |
|                    |          |         | match the value given to 'regexp'.                                         |
+--------------------+----------+---------+----------------------------------------------------------------------------+
| insertafter        | no       | EOF     | Used with state=present. If specified, the line will be inserted after the |
|                    |          |         | specified regular expression. Two special values are available: BOF for    |
|                    |          |         | inserting the line at the beginning of the file, and EOF for inserting the |
|                    |          |         | line at the end of the file.                                               |
+--------------------+----------+---------+----------------------------------------------------------------------------+

Example::

    lineinfile name=/etc/selinux/config regexp=^SELINUX= line=SELINUX=disabled
    lineinfile name=/etc/sudoers regexp="^#includedir" line="#includedir /etc/sudoers.d"
    lineinfile name=/etc/httpd/conf/httpd.conf regexp="^ServerName " insertafter="^#ServerName " line="ServerName ansible.example.com"
    lineinfile name=/etc/sudoers state=absent regexp="^%wheel" 


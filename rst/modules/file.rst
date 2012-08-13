.. _file:

file
````

Sets attributes of files, symlinks, and directories, or removes files/symlinks/directories.  Many other modules
support the same options as the file module -- including 'copy', 'template', and 'assmeble'.

+--------------------+----------+---------+----------------------------------------------------------------------------+
| parameter          | required | default | comments                                                                   |
+====================+==========+=========+============================================================================+
| dest               | yes      |         | defines the file being managed, unless when used with state=link, and      |
|                    |          |         | then sets the destination to create a symbolic link to using 'src'         |
+--------------------+----------+---------+----------------------------------------------------------------------------+
| state              |          | file    | values are 'file', 'link', 'directory', or 'absent'.  If directory,        |
|                    |          |         | all immediate subdirectories will be created if they do not exist.  If     |
|                    |          |         | 'file', the file will NOT be created if it does not exist, see the 'copy'  |
|                    |          |         | or 'template' module if you want that behavior.  If 'link', the symbolic   |
|                    |          |         | link will be created or changed.  If absent, directories will be           |
|                    |          |         | recursively deleted, and files or symlinks will be unlinked.               |
+--------------------+----------+---------+----------------------------------------------------------------------------+
| mode               |          |         | mode the file or directory shoudl be, such as 0644 as would be fed to      |
|                    |          |         | chmod.  English modes like 'g+x' are not yet supported                     |
+--------------------+----------+---------+----------------------------------------------------------------------------+
| owner              |          |         | name of the user that should own the file/directory, as would be fed to    |
|                    |          |         | chown                                                                      |
+--------------------+----------+---------+----------------------------------------------------------------------------+
| group              |          |         | name of the group that should own the file/directory, as would be fed to   |
|                    |          |         | group                                                                      |
+--------------------+----------+---------+----------------------------------------------------------------------------+
| src                |          |         | path of the file to link to (applies only to state=link)                   |
+--------------------+----------+---------+----------------------------------------------------------------------------+
| seuser             |          |         | user part of SELinux file context.  Will default to system policy, if      |
|                    |          |         | applicable.  If set to '_default', it will use the 'user' portion of the   |
|                    |          |         | the policy if available                                                    |
+--------------------+----------+---------+----------------------------------------------------------------------------+
| serole             |          |         | role part of SELinux file context, '_default' feature works as above.      |
+--------------------+----------+---------+----------------------------------------------------------------------------+
| setype             |          |         | type part of SELinux file context, '_default' feature works as above       |
+--------------------+----------+---------+----------------------------------------------------------------------------+
| selevel            |          | s0      | level part of the SELinux file context.  This is the MLS/MCS attribute,    |
|                    |          |         | sometimes known as the 'range'.  '_default' feature works as above         |
+--------------------+----------+---------+----------------------------------------------------------------------------+
| context            |          |         | accepts only 'default' as a value.  This will restore a file's selinux     |
|                    |          |         | context in the policy.  Does nothing if no default is available.           |
+--------------------+----------+---------+----------------------------------------------------------------------------+

Example action from Ansible :doc:`playbooks`::

    file path=/etc/foo.conf owner=foo group=foo mode=0644
    file path=/some/path owner=foo group=foo state=directory
    file path=/path/to/delete state=absent
    file src=/file/to/link/to dest=/path/to/symlink owner=foo group=foo state=link
    file path=/some/path state=directory setype=httpd_sys_content_t
    file path=/some/path state=directory context=default

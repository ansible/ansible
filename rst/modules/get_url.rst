.. _get_url:

get_url
```````

Downloads files from http, https, or ftp to the remote server.  The remote server must have direct
access to the remote resource.

+--------------------+----------+---------+----------------------------------------------------------------------------+
| parameter          | required | default | comments                                                                   |
+====================+==========+=========+============================================================================+
| url                | yes      |         | http, https, or ftp URL                                                    |
+--------------------+----------+---------+----------------------------------------------------------------------------+
| dest               | yes      |         | absolute path of where to download the file to.  If dest is a directory,   |
|                    |          |         | the basename of the file on the remote server will be used.  If a          |
|                    |          |         | directory, thirsty=yes must also be set.                                   |
+--------------------+----------+---------+----------------------------------------------------------------------------+
| thirsty            | no       | 'no'    | (new in 0.7) if yes, will download the file every time and replace the     |
|                    |          |         | file if the contents change.  if no, the file will only be downloaded      |
|                    |          |         | if the destination does not exist.  Generally should be 'yes' only for     |
|                    |          |         | small local files.  prior to 0.6, acts if 'yes' by default.                |
+--------------------+----------+---------+----------------------------------------------------------------------------+
| OTHERS             | no       |         | all arguments accepted by the file module also work here                   |
+--------------------+----------+---------+----------------------------------------------------------------------------+

Example action from Ansible :doc:`playbooks`::

    - action: get_url url=http://example.com/path/file.conf dest=/etc/foo.conf mode=0444


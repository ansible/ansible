.. _fetch:

fetch
`````

This module works like 'copy', but in reverse.  It is used for fetching files
from remote machines and storing them locally in a file tree, organized by hostname.

+--------------------+----------+---------+----------------------------------------------------------------------------+
| parameter          | required | default | comments                                                                   |
+====================+==========+=========+============================================================================+
| src                | yes      |         | The file on the remote system to fetch.  This needs to be a file, not      |
|                    |          |         | a directory.  Recursive fetching may be supported in a later release.      |
+--------------------+----------+---------+----------------------------------------------------------------------------+
| dest               | yes      |         | A directory to save the file into.  For example, if the 'dest' directory   |
|                    |          |         | is '/foo', a src file named '/tmp/bar' on host 'host.example.com', would   |
|                    |          |         | be saved into '/foo/host.example.com/tmp/bar'                              |
+--------------------+----------+---------+----------------------------------------------------------------------------+

Example::

    fetch src=/var/log/messages dest=/home/logtree

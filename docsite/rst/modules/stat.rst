==========================================
stat - retrieve file or file system status
==========================================

>>>**Author:**	Bruce Pennypacker 

`Synopsis`_
`Options`_
`Examples`_

Synopsis
------------

New in version 1.3.

Retrieves facts for a file similar to the linux/unix 'stat' command.

Options
----------
.. csv-table::
   :header: "parameter", "required", "	default 	choices", "comments"
   :widths: 15, 15, 15, 15, 60
   
   "follow", "no", "", "", "	Whether to follow symlinks"
   "get_md5", "no", "True", "", "Whether to return the md5 sum of the file"
   "path", "yes", "", "", "The full path of the file/object to get the facts of"

.. csv-table:: Test parameters
   :header: "parameter", "meaning", "type"
   :widths: 15, 40, 15
   
   "exists", "", "boolean"
   "isdir", "is a directory", "boolean"
   "ischr", "is a character device", "boolean"
   "isblk", "is block device", "boolean"
   "isreg", "is a regular file", "boolean"
   "isfifo", "is a named pipe", "boolean"
   "islnk", "is a symbolic link", "boolean"
   "issock", "is a socket", "boolean"
   "uid", "user ID of owner", "int"
   "gid", "group ID of owner", "int"
   "size", "total size, in bytes", int
   "inode", "inode number", "int"
   "dev", "device ID", "int"
   "nlink", "number of hard links", "int"
   "atime", "time of last access", "int"
   "mtime", "time of last modification", "int"
   "ctime", "time of last status change", "int"
   "wusr", "write permission, owner", "boolean"
   "rusr", "read permission, owner", "boolean"
   "xusr", "execute/search permission, owner ", "boolean"
   "wgrp", "write permission, group", "boolean"
   "rgrp", "read permission, group", "boolean"
   "xgrp", "execute/search permission, group", "boolean"
   "woth", "write permission, other", "boolean"
   "roth", "read permission, other", "boolean"
   "xoth", "execute/search permission, other", "boolean"
   "isuid", "", "boolean"
   "isgid", "", "boolean"

        ======= ======================== =======
          exists                                                                        boolean
          isdir              is a directory                                         boolean
          ischr             is a character device                             boolean
          isblk             is block device                                       boolean
          isreg             is a regular file                                       boolean
          isfifo             is a named pipe                                     boolean
          islnk             is a symbolic link                                    boolean
          issock           is a socket                                              boolean
          uid                user ID of owner                                     int
          gid                group ID of owner                                   int
          size               total size, in bytes                                  int
          inode             inode number                                         int
          dev                device ID                                                int
          nlink              number of hard links                               int
          atime             time of last access                                 int
          mtime            time of last modification                        int
          ctime             time of last status change                      int
          wusr               write permission, owner                        boolean
          rusr                read permission, owner                         boolean
          xusr               execute/search permission, owner         boolean
          wgrp              write permission, group                         boolean
          rgrp               read permission, group                          boolean
          xgrp               execute/search permission, group         boolean
          woth               write permission, other                         boolean
          roth                read permission, other                          boolean
          xoth               execute/search permission, other          boolean
          isuid                                                                            boolean
          isgid                                                                            boolean

Examples
-------------
::

    # Obtain the stats of /etc/foo.conf, and check that the file still belongs
    # to "root". Fail otherwise.
    - stat: path=/etc/foo.conf
      register: st
    - fail: msg="Whoops! file ownership has changed"
      when: st.stat.pw_name != "root"

    # Determine if a path exists and is a directory.  Note we need to test
    # both that p.stat.isdir actually exists, and also that it"s set to true.
    - stat: path=/path/to/something
      register: p
    - debug: msg="Path exists and is a directory"
      when: p.stat.isdir is defined and p.stat.isdir == true

    # Don"t do md5 checksum
    - stat: path=/path/to/myhugefile get_md5=no

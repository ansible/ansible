no-illegal-filenames
====================

Files and directories should not contain illegal characters or names so that
Ansible can be checked out on any Operating System.

Illegal Characters
------------------

The following characters are not allowed to be used in any part of the file or
directory name;

* ``<``
* ``>``
* ``:``
* ``"``
* ``/``
* ``\``
* ``|``
* ``?``
* ``*``
* Any characters whose integer representations are in the range from 0 through to 31 like ``\n``

The following characters are not allowed to be used as the last character of a
file or directory;

* ``.``
* ``" "`` (just the space character)

Illegal Names
-------------

The following names are not allowed to be used as the name of a file or
directory excluding the extension;

* ``CON``
* ``PRN``
* ``AUX``
* ``NUL``
* ``COM1``
* ``COM2``
* ``COM3``
* ``COM4``
* ``COM5``
* ``COM6``
* ``COM7``
* ``COM8``
* ``COM9``
* ``LPT1``
* ``LPT2``
* ``LPT3``
* ``LPT4``
* ``LPT5``
* ``LPT6``
* ``LPT7``
* ``LPT8``
* ``LPT9``

For example, the file ``folder/COM1``, ``folder/COM1.txt`` are illegal but
``folder/COM1-file`` or ``folder/COM1-file.txt`` is allowed.


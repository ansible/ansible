.. _assemble:

assemble
````````

.. versionadded:: 0.5

Assembles a configuration file from fragments.  Often a particular
program will take a single configuration file and does not support a
conf.d style structure where it is easy to build up the configuration
from multiple sources.  Assemble will take a directory of files that
have already been transferred to the system, and concatenate them
together to produce a destination file.  Files are assembled in string
sorting order.  Puppet calls this idea "fragments".

+--------------------+----------+---------+----------------------------------------------------------------------------+
| parameter          | required | default | comments                                                                   |
+====================+==========+=========+============================================================================+
| src                | yes      |         | An already existing directory full of source files                         |
+--------------------+----------+---------+----------------------------------------------------------------------------+
| dest               | yes      |         | A file to create using the concatenation of all of the source files        |
+--------------------+----------+---------+----------------------------------------------------------------------------+
| OTHERS             |          |         | All arguments that the file module takes may also be used                  |
+--------------------+----------+---------+----------------------------------------------------------------------------+

Example action from Ansible :doc:`playbooks`::

    assemble src=/etc/someapp/fragments dest=/etc/someapp/someapp.conf

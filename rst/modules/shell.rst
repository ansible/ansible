.. _shell:

shell
`````

The shell module takes the command name followed by a list of
arguments, space delimited.  It is almost exactly like the command module
but runs the command through the user's configured shell on the remote node.

+--------------------+----------+---------+----------------------------------------------------------------------------+
| parameter          | required | default | comments                                                                   |
+====================+==========+=========+============================================================================+
| (free form)        | N/A      | N/A     | the command module takes a free form command to run                        |
+--------------------+----------+---------+----------------------------------------------------------------------------+
| creates            | no       |         | a filename, when it already exists, this step will NOT be run              |
+--------------------+----------+---------+----------------------------------------------------------------------------+
| chdir              | no       |         | cd into this directory before running the command (0.6 and later)          |
+--------------------+----------+---------+----------------------------------------------------------------------------+

The given command will be executed on all selected nodes.

.. note::
   If you want to execute a command securely and predicably, it may be
   better to use the 'command' module instead.  Best practices when
   writing playbooks will follow the trend of using 'command' unless
   'shell' is explicitly required.  When running ad-hoc commands, use
   your best judgement.

Example action from a playbook::

    shell somescript.sh >> somelog.txt

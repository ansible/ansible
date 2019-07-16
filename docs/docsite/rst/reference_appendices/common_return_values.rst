.. _common_return_values:

Return Values
-------------

.. contents:: Topics

Ansible modules normally return a data structure that can be registered into a variable, or seen directly when output by
the `ansible` program. Each module can optionally document its own unique return values (visible through ansible-doc and on the :ref:`main docsite<ansible_documentation>`).

This document covers return values common to all modules.

.. note:: Some of these keys might be set by Ansible itself once it processes the module's return information.


Common
^^^^^^

backup_file
```````````
For those modules that implement `backup=no|yes` when manipulating files, a path to the backup file created.

changed
```````
A boolean indicating if the task had to make changes.

failed
``````
A boolean that indicates if the task was failed or not.

invocation
``````````
Information on how the module was invoked.

msg
```
A string with a generic message relayed to the user.

rc
``
Some modules execute command line utilities or are geared for executing commands directly (raw, shell, command, etc), this field contains 'return code' of these utilities.

results
```````
If this key exists, it indicates that a loop was present for the task and that it contains a list of the normal module 'result' per item.

skipped
```````
A boolean that indicates if the task was skipped or not

stderr
``````
Some modules execute command line utilities or are geared for executing commands directly (raw, shell, command, etc), this field contains the error output of these utilities.

stderr_lines
````````````
When `stderr` is returned we also always provide this field which is a list of strings, one item per line from the original.

stdout
``````
Some modules execute command line utilities or are geared for executing commands directly (raw, shell, command, etc). This field contains the normal output of these utilities.

stdout_lines
````````````
When `stdout` is returned, Ansible always provides a list of strings, each containing one item per line from the original output.


.. _internal_return_values:

Internal use
^^^^^^^^^^^^

These keys can be added by modules but will be removed from registered variables; they are 'consumed' by Ansible itself.

ansible_facts
`````````````
This key should contain a dictionary which will be appended to the facts assigned to the host. These will be directly accessible and don't require using a registered variable.

exception
`````````
This key can contain traceback information caused by an exception in a module. It will only be displayed on high verbosity (-vvv).

warnings
````````
This key contains a list of strings that will be presented to the user.

deprecations
````````````
This key contains a list of dictionaries that will be presented to the user. Keys of the dictionaries are `msg` and `version`, values are string, value for the `version` key can be an empty string.

.. seealso::

   :ref:`all_modules`
       Learn about available modules
   `GitHub modules directory <https://github.com/ansible/ansible/tree/devel/lib/ansible/modules>`_
       Browse source of core and extras modules
   `Mailing List <https://groups.google.com/group/ansible-devel>`_
       Development mailing list
   `irc.freenode.net <http://irc.freenode.net>`_
       #ansible IRC chat channel

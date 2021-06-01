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

    .. code-block:: console

      "backup_file": "./foo.txt.32729.2020-07-30@06:24:19~"
    

changed
```````
A boolean indicating if the task had to make changes.

    .. code-block:: console

        "changed": true

diff
````
Information on differences between the previous and current state. Often a dictionary with entries ``before`` and ``after``, which will then be formatted by the callback plugin to a diff view.

    .. code-block:: console

        "diff": [
                {
                    "after": "",
                    "after_header": "foo.txt (content)",
                    "before": "",
                    "before_header": "foo.txt (content)"
                },
                {
                    "after_header": "foo.txt (file attributes)",
                    "before_header": "foo.txt (file attributes)"
                }

failed
``````
A boolean that indicates if the task was failed or not.

    .. code-block:: console

        "failed": false

invocation
``````````
Information on how the module was invoked.

    .. code-block:: console

        "invocation": {
                "module_args": {
                    "_original_basename": "foo.txt",
                    "attributes": null,
                    "backup": true,
                    "checksum": "da39a3ee5e6b4b0d3255bfef95601890afd80709",
                    "content": null,
                    "delimiter": null,
                    "dest": "./foo.txt",
                    "directory_mode": null,
                    "follow": false,
                    "force": true,
                    "group": null,
                    "local_follow": null,
                    "mode": "666",
                    "owner": null,
                    "regexp": null,
                    "remote_src": null,
                    "selevel": null,
                    "serole": null,
                    "setype": null,
                    "seuser": null,
                    "src": "/Users/foo/.ansible/tmp/ansible-tmp-1596115458.110205-105717464505158/source",
                    "unsafe_writes": null,
                    "validate": null
                }

msg
```
A string with a generic message relayed to the user.

    .. code-block:: console

        "msg": "line added"

rc
``
Some modules execute command line utilities or are geared for executing commands directly (raw, shell, command, and so on), this field contains 'return code' of these utilities.

    .. code-block:: console

        "rc": 257

results
```````
If this key exists, it indicates that a loop was present for the task and that it contains a list of the normal module 'result' per item.

    .. code-block:: console

        "results": [
            {
                "ansible_loop_var": "item",
                "backup": "foo.txt.83170.2020-07-30@07:03:05~",
                "changed": true,
                "diff": [
                    {
                        "after": "",
                        "after_header": "foo.txt (content)",
                        "before": "",
                        "before_header": "foo.txt (content)"
                    },
                    {
                        "after_header": "foo.txt (file attributes)",
                        "before_header": "foo.txt (file attributes)"
                    }
                ],
                "failed": false,
                "invocation": {
                    "module_args": {
                        "attributes": null,
                        "backrefs": false,
                        "backup": true
                    }
                },
                "item": "foo",
                "msg": "line added"
            },
            {
                "ansible_loop_var": "item", 
                "backup": "foo.txt.83187.2020-07-30@07:03:05~",
                "changed": true,
                "diff": [
                    {
                        "after": "",
                        "after_header": "foo.txt (content)",
                        "before": "",
                        "before_header": "foo.txt (content)"
                    },
                    {
                        "after_header": "foo.txt (file attributes)",
                        "before_header": "foo.txt (file attributes)"
                    }
                ],
                "failed": false,
                "invocation": {
                    "module_args": {
                        "attributes": null,
                        "backrefs": false,
                        "backup": true
                    }
                },
                "item": "bar",
                "msg": "line added"
            }
            ]

skipped
```````
A boolean that indicates if the task was skipped or not

    .. code-block:: console
    
        "skipped": true

stderr
``````
Some modules execute command line utilities or are geared for executing commands directly (raw, shell, command, and so on), this field contains the error output of these utilities.

    .. code-block:: console

        "stderr": "ls: foo: No such file or directory"

stderr_lines
````````````
When `stderr` is returned we also always provide this field which is a list of strings, one item per line from the original.

    .. code-block:: console

        "stderr_lines": [
                "ls: doesntexist: No such file or directory"
                ]

stdout
``````
Some modules execute command line utilities or are geared for executing commands directly (raw, shell, command, and so on). This field contains the normal output of these utilities.

    .. code-block:: console

        "stdout": "foo!"

stdout_lines
````````````
When `stdout` is returned, Ansible always provides a list of strings, each containing one item per line from the original output.

    .. code-block:: console

        "stdout_lines": [
        "foo!"
        ]


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

   :ref:`list_of_collections`
       Browse existing collections, modules, and plugins
   `GitHub modules directory <https://github.com/ansible/ansible/tree/devel/lib/ansible/modules>`_
       Browse source of core and extras modules
   `Mailing List <https://groups.google.com/group/ansible-devel>`_
       Development mailing list
   `irc.libera.chat <https://libera.chat/>`_
       #ansible IRC chat channel

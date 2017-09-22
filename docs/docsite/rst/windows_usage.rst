Using Ansible and Windows
=========================
Info about using Ansible and Windows such as common use cases and how to write
tasks.

Use Cases
`````````
Some common use cases with Ansible and Windows.

Installing Programs
-------------------

Installing Updates
------------------

Setup Users and Groups
----------------------

Local
+++++

Domain
++++++

Running Commands
----------------

Escaping Spaces
+++++++++++++++

Command or Shell
++++++++++++++++

Path Formatting for Windows
```````````````````````````
Windows is unlike a traditional POSIX operating system in many ways but one of
the major changes is the shift from ``/`` as the path separator to ``\``. This
can cause major issues with how playbooks are written as ``\`` can be seen as
an escape character in certain situations.

There are two ways of writting tasks in Ansible and each way have their own
recommended way of dealing with path separators for Windows.

YAML Style
----------

Legacy key=value Style
----------------------


What you Cannot Do
``````````````````
Some things you cannot do, or do easily, with Ansible are:

* Upgrade powershell

* Interact with the WinRM listeners

Examples
````````

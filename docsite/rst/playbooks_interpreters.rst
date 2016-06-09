Specifying Interpreters
+++++++++++++++++++++++

.. contents:: Topics

Ansible modules are written in Python, or other interpreted languages such as Perl or Ruby.
Following UNIX convention, the implementation language of a given module is identified
by its shebang line, such as '#! /usr/bin/python'. This indicates the default interpreter
to be used when running the module.

However, the actual location of the appropriate interpreter may vary
from host to host. For instance, on \*BSD systems, it is usually
'/usr/local/bin/python'; on some machines, the default Python binary
may be a 3.X one, whereas Ansible modules require a Python 2.X
interpreter, which could be installed as '/usr/bin/python2'.


Inventory variables
-------------------

The interpreter for a given language can be set using inventory variables named
after the base name of the default interpreter. So, for Python, the default interpreter
is '/usr/bin/python', so the variable is 'ansible_python_interpreter'. Likewise
for other languages, the variable is 'ansible_*_interpreter'.

Examples from a host file::

    [linux_group]
    python3_host ansible_python_interpreter=/usr/bin/python2
    ruby_host  ansible_ruby_interpreter=/usr/bin/ruby.1.9.3

    [freebsd_group:vars]
    ansible_python_interpreter=/usr/local/bin/python

Relying on PATH
---------------

Ansible by default requires the full path of interpreters to be set in inventory,
if you want to override the default path. This ensures that the result of
executing a playbook is independent of environment settings. However, if
'ansible_*_interpreter' is set to just a base name, then the corresponding
command will be searched in PATH.

Specifying multiple interpreters
--------------------------------

In general it is best to specify the exact location of the correct
interpreter for each machine in the inventory. However, in the
context of managing farms of heterogeneous hosts, it may be impractical
to maintain an up-to-date record of what exact interpreter path is
to be used on a given machine. In such a context, Ansible can be
configured to look for the interpreter from a set of possible
candidates given as a colon-separated list. Each item is either a
full name, or just a base name that will be resolved from PATH:

Example::

    ansible_python_interpreter=/usr/local/bin/python2.7:python2:/usr/bin/python:python

This indicates that Ansible should try the following Python interpreters in order:

- '/usr/local/bin/python2.7'
- a 'python2' binary from PATH
- '/usr/bin/python'
- a 'python' binary from PATH

Ansible stops the search as soon as a matching executable is found. Note that
this is not supported for machines using a release of the fish shell older than
2.2.0.

Interpreter caching
-------------------

In the case where an interpreter is looked up from PATH, or from a list of possible
candidates, the lookup is done only once per playbook for each host. The result
is stored as a host fact so that it remains in effect for the whole playbook.

If fact caching is used, the setting is also part of the cached information, and
the lookup is not performed again until the cache is flushed.

.. seealso::

   `Mailing List <http://groups.google.com/group/ansible-project>`_
       Questions? Help? Ideas?  Stop by the list on Google Groups
   `irc.freenode.net <http://irc.freenode.net>`_
       #ansible IRC chat channel


.. _facter:

facter
``````

Runs the discovery program 'facter' on the remote system, returning
JSON data that can be useful for inventory purposes.

Requires that 'facter' and 'ruby-json' be installed on the remote end.

Playbooks do not actually use this module, they use the :ref:`setup`
module behind the scenes.

Example from /usr/bin/ansible::

    ansible foo.example.org -m facter

.. _ohai:

ohai
````

Similar to the :ref:`facter` module, this returns JSON inventory data.
Ohai data is a bit more verbose and nested than facter.

Requires that 'ohai' be installed on the remote end.

Playbooks should not call the ohai module, playbooks call the
:ref:`setup` module behind the scenes instead.

Example::

    ansible foo.example.org -m ohai

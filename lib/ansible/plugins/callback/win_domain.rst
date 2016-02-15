win\_domain.py
=================

Ansible plugin for attaching to a windows domain at runtime.
It is a wrapper for the tools kinit and kdestroy, so these 
must be available to the current user.

Usage
-----

Configure your windows hosts for domain authentication as described 
here: http://docs.ansible.com/ansible/intro_windows.html#active-directory-support
Add ``win_domain`` to the ``callback_whitelist`` in ``ansible.cfg``.
Optionally, set ``bin_ansible_callbacks = True win_domain`` in ``ansible.cfg``.
This will allow automatically connecting to domains when using the 
 ``ansible`` command as well as when using ``ansible-playbook``.

Run playbooks as normal.

Features
--------

Since a domain login is good for all machines on the domain, the plugin
will cache a domain login for the first host configured as a windows host
in the current inventory and then return control to the play / playbook.

Assumes you only wish to connect to a single domain per inventory.

To view debug messages run with -vv

Compatibility
-------------

Ansible 2.0+

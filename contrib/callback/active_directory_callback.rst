active\_directory_callback.py
=================

Ansible plugin for attaching to a windows domain at runtime.
It is a wrapper for the tools kinit and kdestroy, so these 
must be available to the current user.

Usage
-----

Configure your windows hosts for domain authentication as described 
here: http://docs.ansible.com/ansible/intro_windows.html#active-directory-support
Ensure you have used the new names ``ansible_user`` and ``ansible_password``, rather than the older names ``ansible_ssh_user`` and ``ansible_ssh_pass`` as this
plugin only recognizes the newer style username and password
Optionally, set ``bin_ansible_callbacks = True win_domain`` in ``ansible.cfg``.
This will allow automatically connecting to Active Directory domains when using the 
 ``ansible`` command as well as when using ``ansible-playbook``.

Run playbooks as normal.

Features
--------

Since a domain login is good for all machines on the domain, the plugin
will cache a domain login for the first host configured as a windows host
in the current inventory and then return control to the play / playbook.

This saves caching lots of unnecessary logins for each host, but assumes you 
only wish to connect to a single domain per inventory.

To view debug messages run with -vv

Compatibility
-------------

Ansible 2.0+

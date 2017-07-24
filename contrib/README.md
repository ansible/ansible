contrib
-------
Files here provide an extension mechanism for Ansible similar to plugins. They are not maintained by the Ansible core team or installed with Ansible.


inventory
=========

Before 2.4 introduced inventory plugins, inventory scripts were the only way to provide sources that were not built into Ansible. Inventory scripts allow you to store your hosts, groups, and variables in any way you like. 

Starting with Ansible version 2.4, they are enabled via the 'script' inventory plugin.
Examples of use include discovering inventory from EC2 or pulling it from Cobbler. These could also be used to interface with LDAP or the database.

`chmod +x` an inventory plugin and either name it `/etc/ansible/hosts` or use `ansible -i /path/to/inventory/script`. You might also need to copy a configuration file with the same name and/or set environment variables. The scripts or configuration files can provide more details.

vault
=====

If the file passed to `--vault-password-file` has the executable bit set, Ansible will execute it and use the stdout of that execution as 'the secret'.
Vault scripts provided here use this facility to retrieve the vault secret from a number of sources.

contributions welcome
=====================

Send in pull requests to add scripts of your own.  The sky is the limit!


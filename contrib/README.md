contrib
-------
Files here are not maintained by the Ansible core team nor are they necessarily installed with Ansible.
They are provided here as they allow for extension of Ansible similar to plugins.

inventory
=========

Before 2.4 introduced inventory plugins, before that inventory scripts were the only way to provide sources that were not 'built into Ansible'.
Inventory scripts allow you to store your hosts, groups, and variables in any way you like. Since 2.4 they are enabled via the 'script' inventory plugin.
Examples include discovering inventory from EC2 or pulling it from Cobbler. These could also be used to interface with LDAP or database.

`chmod +x` an inventory plugin and either name it `/etc/ansible/hosts` or use `ansible -i /path/to/inventory/script`. You might also need to copy a configuration file with the same name and/or set environment variables, the scripts or configuration files have more details.

vault
=====

If the file passed to `--vault-password-file` has the executable bit set, Ansible will execute it and use the stdout of that execution as 'the secret'.
Vault scripts provided here use this facility to retrieve the vault secret from a number of sources.

contributions welcome
=====================

Send in pull requests to add scripts of your own.  The sky is the limit!


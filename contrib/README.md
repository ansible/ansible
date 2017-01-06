inventory
=========

Inventory scripts allow you to store your hosts, groups, and variables in any way
you like.  Examples include discovering inventory from EC2 or pulling it from
Cobbler.  These could also be used to interface with LDAP or database.

`chmod +x` an inventory plugin and either name it `/etc/ansible/hosts` or use `ansible -i /path/to/inventory/script`. You might also need to copy a configuration
file with the same name and/or set environment variables, the scripts or configuration
files have more details.

contributions welcome
=====================

Send in pull requests to add plugins of your own.  The sky is the limit!


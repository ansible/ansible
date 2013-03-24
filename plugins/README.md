ansible-plugins
===============

You can extend ansible with optional callback and connection plugins.

callbacks
=========

Callbacks can be used to add logging or monitoring capability, or just make
interesting sound effects.

Drop callback plugins in your ansible/lib/callback_plugins/ directory.

connections
===========

Connection plugins allow ansible to talk over different protocols.

Drop connection plugins in your ansible/lib/runner/connection_plugins/ directory.

inventory
=========

Inventory plugins allow you to store your hosts, groups, and variables in any way
you like.  Examples include discovering inventory from EC2 or pulling it from
Cobbler.  These could also be used to interface with LDAP or database.

chmod +x an inventory plugin and either name it /etc/ansible/hosts or use ansible
with -i to designate the path to the plugin.

contributions welcome
=====================

Send in pull requests to add plugins of your own.  The sky is the limit!


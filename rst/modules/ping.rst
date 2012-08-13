.. _ping:

ping
````

A trivial test module, this module always returns 'pong' on
successful contact.  It does not make sense in playbooks, but is useful
from /usr/bin/ansible::

    ansible webservers -m ping

Ansible Test System
===================

Folders
=======

unit
----

Unit tests that test small pieces of code not suited for the integration test layer, usually very API based, and should leverage
mock interfaces rather than producing side effects.

Playbook engine code is better suited for integration tests.

Requirements: `sudo pip install paramiko PyYAML jinja2 httplib2 passlib nose mock`

integration
-----------

Integration test layer, constructed using playbooks.

Some tests may require cloud credentials, others will not, and destructive tests are separated from non-destructive so a subset
can be run on development machines.

learn more
----------

hop into a subdirectory and see the associated README.md for more info.




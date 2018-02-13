.. _ansible-vault:

=============
ansible-vault
=============


:strong:`encryption/decryption utility for Ansible data files`


.. contents::
   :local:
   :depth: 2


.. program:: ansible-vault

Synopsis
========

.. code-block:: bash

   ansible-vault [create|decrypt|edit|encrypt|encrypt_string|rekey|view] [options] [vaultfile.yml]


Description
===========


can encrypt any structured data file used by Ansible.
This can include *group_vars/* or *host_vars/* inventory variables,
variables loaded by *include_vars* or *vars_files*, or variable files
passed on the ansible-playbook command line with *-e @file.yml* or *-e @file.json*.
Role variables and defaults are also included!

Because Ansible tasks, handlers, and other objects are data, these can also be encrypted with vault.
If you'd like to not expose what variables you are using, you can keep an individual task file entirely encrypted.

The password used with vault currently must be the same for all files you wish to use together at the same time.


Common Options
==============




.. option:: --ask-vault-pass

   ask for vault password


.. option:: --new-vault-id <NEW_VAULT_ID>

   the new vault identity to use for rekey


.. option:: --new-vault-password-file

   new vault password file for rekey


.. option:: --vault-id

   the vault identity to use


.. option:: --vault-password-file

   vault password file


.. option:: --version

   show program's version number and exit


.. option:: -h, --help

   show this help message and exit


.. option:: -v, --verbose

   verbose mode (-vvv for more, -vvvv to enable connection debugging)






Actions
=======



.. program:: ansible-vault encrypt
.. _ansible_vault_encrypt:

encrypt
-------

encrypt the supplied file using the provided vault secret





.. option:: --encrypt-vault-id  <ENCRYPT_VAULT_ID>

   the vault id used to encrypt (required if more than vault-id is provided)

.. option:: --output 

   output file name for encrypt or decrypt; use - for stdout





.. program:: ansible-vault rekey
.. _ansible_vault_rekey:

rekey
-----

re-encrypt a vaulted file with a new secret, the previous secret is required





.. option:: --encrypt-vault-id  <ENCRYPT_VAULT_ID>

   the vault id used to encrypt (required if more than vault-id is provided)





.. program:: ansible-vault encrypt_string
.. _ansible_vault_encrypt_string:

encrypt_string
--------------

encrypt the supplied string using the provided vault secret





.. option:: --encrypt-vault-id  <ENCRYPT_VAULT_ID>

   the vault id used to encrypt (required if more than vault-id is provided)

.. option:: --output 

   output file name for encrypt or decrypt; use - for stdout

.. option:: --stdin-name  <ENCRYPT_STRING_STDIN_NAME>

   Specify the variable name for stdin

.. option:: -n , --name 

   Specify the variable name

.. option:: -p , --prompt 

   Prompt for the string to encrypt





.. program:: ansible-vault edit
.. _ansible_vault_edit:

edit
----

open and decrypt an existing vaulted file in an editor, that will be encryped again when closed





.. program:: ansible-vault create
.. _ansible_vault_create:

create
------

create and open a file in an editor that will be encryped with the provided vault secret when closed





.. option:: --encrypt-vault-id  <ENCRYPT_VAULT_ID>

   the vault id used to encrypt (required if more than vault-id is provided)





.. program:: ansible-vault decrypt
.. _ansible_vault_decrypt:

decrypt
-------

decrypt the supplied file using the provided vault secret





.. option:: --output 

   output file name for encrypt or decrypt; use - for stdout





.. program:: ansible-vault view
.. _ansible_vault_view:

view
----

open, decrypt and view an existing vaulted file using a pager using the supplied vault secret




.. program:: ansible-vault


Environment
===========

The following environment variables may be specified.



:envvar:`ANSIBLE_CONFIG` -- Override the default ansible config file

Many more are available for most options in ansible.cfg


Files
=====


:file:`/etc/ansible/ansible.cfg` -- Config file, used if present

:file:`~/.ansible.cfg` -- User config file, overrides the default config if present

Author
======

Ansible was originally written by Michael DeHaan.

See the `AUTHORS` file for a complete list of contributors.


Copyright
=========

Copyright © 2017 Red Hat, Inc | Ansible.

Ansible is released under the terms of the GPLv3 License.

See also
========

:manpage:`ansible(1)`,  :manpage:`ansible-config(1)`,  :manpage:`ansible-console(1)`,  :manpage:`ansible-doc(1)`,  :manpage:`ansible-galaxy(1)`,  :manpage:`ansible-inventory(1)`,  :manpage:`ansible-playbook(1)`,  :manpage:`ansible-pull(1)`,  :manpage:`ansible-vault(1)`,  

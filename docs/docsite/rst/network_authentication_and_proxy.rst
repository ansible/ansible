.. network-authentication-and-proxt:

*******************************
Network getting started example
*******************************

.. contents:: Topics


Overview
========

FIXME Explain types of connection

FIXME table of platforms and when network_cli was added, list of what doesn't support it (e.g. Python REST API)

Authenticating against APIs
===========================


Proxy
=====

* FIXME move content here, update links in porting & debug page


Stuff
=====

FIXME Link to details regarding different ways to specify credentials (this should be in the main docs somewhere). This should just be a summary that links to the existing docs (``intro_inventory``, ``playbooks_best_practices.html#best-practices-for-variables-and-vaults``, ``ansible-playbook.rst``, etc)

Somewhere in the main docs we need to list the different ways of authenticating


:Command line:

  * Using ``--user`` (``-u``) and ``--ask-pass`` (``-k``).
  * Note: This only works if all devices use the same credentials

:Inventory file:

  :``ansible_user``:

    * Details
    * Link to main docs

  :``ansible_ssh_pass``:

    * Generally used along side ``ansible_user``.
    * Not for REST transports such as `eapi`, `nxapi`.
    * Link to main docs

  :``ansible_ssh_private_key_file``:

    * Details
    * Link to main docs

:top-level module options:

  * As of Ansible 2.3 this is deprecated.
  * Link to main docs

:``provider``: argument to module:

  * This is OK
  * Link to main docs

:Env variables:

  * ``ANSIBLE_NET_USERNAME``
  * ``ANSIBLE_NET_PASSWORD``



FIXME
======

* network debug page should link to this
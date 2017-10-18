.. network-authentication-and-proxy:

*******************************
Network getting started example
*******************************

.. contents:: Topics


Overview
========

This page will explains the different ways you can authentication against the various network modules (LINKTONETWORKMODULEINDEXPAGE).

As Ansible is a flexible tool there are a number of different ways this can be achieved, the pros and cons will be detailed.


.. network-types-of-connections:

Types of connection
===================

The types of authentication depend on the transport (the way Ansible communicates) to the remote device.


:cli (ssh based):

  * What is this
  * Most common
  * Other stuff

:eAPI:

  * Arista EOS specific
  * Over HTTP(S)

:NXAPI:

  * Cisco NX-OS specific
  * Over HTTP(S)

:Other stuff:

  * Goes
  * Here



.. network-platform-connections:

Network Platforms
=================

FIXME: Table of platforms and connections available, may need to include version added.




.. network-connection-auth-matrix

Authentication methods available on each connection type
========================================================


                                        CLI, eAPI/NXAPI  F5 Notes
Command line: (``--user`` & ``-k``)     Y    Y           ?
top-level                               Y    Y           X  Deprecated



Best practice
=============

Wherever possible use the standard Ansible way, that is do not use ``provider:`` (or the even older top-level) arguments.

FIXME Show correct way
FIXME Link to network-getting-started




REST (eAPI, NXAPI)
==================

Currently (2.4) has to use provider






Other types
===========





FIXME Show other types

FIXME add links to ansible(-playbook) commandline arguments








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

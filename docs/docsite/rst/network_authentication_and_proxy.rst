.. network-authentication-and-proxy:

*******************************
Network getting started example
*******************************

.. contents:: Topics


Overview
========

This page will explains the different ways you can authentication against the various :doc:`list_of_network_modules`.

As Ansible is a flexible tool there are a number of different ways this can be achieved, the pros and cons will be detailed.


By the end of this document you will know:

* What communication methods (transports) are available for each network platforms and how to use them
* For platforms that support privilege mode, how to use it
* How to connect to via CLI transports (ssh) via a jump host


Terms
------

:Transport:
  The communication method used to access the remote node (switch).

  :CLI Transport:

    Communication to the remote node is done over SSH.

  :API:

    Communication to the remote node is done over HTTP(S).
:Platform:
:Privilege mode: Enable/EXEC mode on switches that support different levels of user privilege.
:Controller: The machine running ``ansible-playbook``
:Remote node: The network switch or router we are configuring
:Jump host/Bastian: Machine that sits between the `controller` and the `remote node`
:Ansible_connection: Ansible "keyword" used to specify the
:Connection local:
:Connection network_cli:

Specifying Network Credentials
==============================

.. network-platform-connections:

Transports available
--------------------

The following table gives a summary of the connection methods supported by this version of Ansible.

+-------------+---------------------------+-------------------------------+
| Platform    | CLI connection method     | API                           |
+=============+===========================+===============================+
| eos         | connection: network_cli   | provider: transport: eapi     |
+-------------+---------------------------+-------------------------------+
| ce          | provider                  | top-level module argument     |
+-------------+---------------------------+-------------------------------+
| dellos      | provider                  |                               |
+-------------+---------------------------+-------------------------------+
| ios         | connection: network_cli   |                               |
+-------------+---------------------------+-------------------------------+
| iosxr       | connection: network_cli   |                               |
+-------------+---------------------------+-------------------------------+
| junos       | connection: network_cli   |                               |
+-------------+---------------------------+-------------------------------+
| openvswitch |                           |                               |
+-------------+---------------------------+-------------------------------+
| nxos        | connection: network_cli   | provider: transport: nxapi    |
+-------------+---------------------------+-------------------------------+
| vyos        | connection: network_cli   |                               |
+-------------+---------------------------+-------------------------------+
|             |                           |                               |
+-------------+---------------------------+-------------------------------+
|             |                           |                               |
+-------------+---------------------------+-------------------------------+


If a platform isn't listed in the above table consult the module documentation.

.. _network-cli:

connection: network_cli
-----------------------

From Ansible 2.5 ``network_cli`` connections are first class citizens. Previously (in Ansible 2.2 to 2.4) playbook writers had to use ``connection: local``.

The ansible-connection setting tells Ansible how it should connect to a remote device. When working with Ansible Networking, setting this to ``ansible_connection: network_cli`` informs Ansible that the remote node is a network device with a limited execution environment. Without this setting, Ansible would attempt to use ssh to connect to the remote and execute the Python script on the network device, which would fail because Python generally isn't available on network devices.

Along with ansible_connection in Ansible 2.5 you must specify the platform. One way to do this is via vars:

.. code-block::

   [eos:vars]
   ansible_connection: network_cli
   ansible_network_os: eos

   [vyos:vars]
   ansible_connection: network_cli
   ansible_network_os: vyos


Just like using Ansible to manage your Linux machines, thee is no need to specify any connection arguments.

.. code-block:: yaml

   - name: "Demonstrate connecting to switches"
     hosts: switches
     gather_facts: no

     tasks:
       - name: Gather facts (eos)
         eos_facts:
         gather_subset:
           - config
         become: true
         become_method: enable
         when: "'eos' in group_names"


For a full example showing how to use ``network_cli`` as well as an overview of how Ansible can be used to manage Networking can be found in :ref:`network-getting-started-example`.

provider
--------

The ``provider:`` interface will be removed in Ansible 2.9, we encurage you to move to ``network_cli`` at your earliest convenience.

Although ``connection: network_cli`` is the preferred way to specifying the connection, there are two instances when ``provider`` may still need when:

* You wish to use the ``eapi`` or ``nxapi`` transport
* The module hasn't been updated to support network_cli, the network-platform-connections table will show this

.. code-block::

   [eos:vars]
   cli
     username: user
     password: VAULTEDSTRING
     hostname: "{{ inventory_hostname }}"

.. code-block:: yaml

   - name: "Download switch configuration"
     hosts: switches
     connection: local
     gather_facts: no


     tasks:
       - name: Gather facts (ios)
         ios_facts:
           provider: "{{ cli }}"
         register: result_ios
         when: "'ios' in group_names"





FIXME: Deprecation warning about top-level - Include warning, link to porting guide

FIXME: Include error wrong connection specified


Best Practice for supplying credentials
---------------------------------------

FIXME Add example here

FIXME Link to Getting Started example


FIXME Detail different ways credentials can be specified



* List the various ways
* Link to existing core docs - which may need improving
* Link to ansible command line anchors
* Detail advantages and disadvantages
* FIXME Link to details regarding different ways to specify credentials (this should be in the main docs somewhere). This should just be a summary that links to the existing docs (``intro_inventory``, ``playbooks_best_practices.html#best-practices-for-variables-and-vaults``, ``ansible-playbook.rst``, etc)

* NOTE: Passwords will be redacted. If username & PW are the same this may cause you issues
* Keys - https://github.com/ansible/ansible/issues/31988
* Details of ssh keys with passphrases and not using ssh-agent


Using CLI to enable API
=======================

FIXME: Show example

Proxy
=====

CLI (SSH) Proxy
===============

 .. _network_delegate_to_vs_ProxyCommand:

delegate_to vs ProxyCommand
---------------------------

The new connection framework for Network Modules in Ansible 2.3 that uses ``cli`` transport
no longer supports the use of the ``delegate_to`` directive.
In order to use a bastion or intermediate jump host to connect to network devices over ``cli``
transport, network modules now support the use of ``ProxyCommand``.

To use ``ProxyCommand``, configure the proxy settings in the Ansible inventory
file to specify the proxy host.

.. code-block:: ini

    [nxos]
    nxos01
    nxos02

    [nxos:vars]
    ansible_ssh_common_args='-o ProxyCommand="ssh -W %h:%p -q bastion01"'


With the configuration above, simply build and run the playbook as normal with
no additional changes necessary.  The network module will now connect to the
network device by first connecting to the host specified in
``ansible_ssh_common_args``, which is ``bastion01`` in the above example.


.. note:: Using ``ProxyCommand`` with passwords via variables

   By design, SSH doesn't support providing passwords via environment variables.
   This is done to prevent secrets from leaking out, for example in ``ps`` output.

   We recommend using SSH Keys, and if needed an ssh-agent, rather than passwords, where ever possible.

API (HTTP) Proxy
================


* FIXME https://github.com/ansible/ansible/pull/30813
* FIXME https://github.com/ansible/ansible/issues/22885#issuecomment-293741361

Privilege Mode
==============


For more information see the :ref:`become-network guide`.




Stuff
=====

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
* Link to _become-network

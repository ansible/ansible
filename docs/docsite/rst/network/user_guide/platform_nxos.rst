.. _nxos_platform_options:

***************************************
NXOS Platform Options
***************************************

The `Cisco NXOS <https://galaxy.ansible.com/cisco/nxos>`_ supports multiple connections. This page offers details on how each connection works in Ansible and how to use it.

.. contents::
  :local:

Connections available
================================================================================

.. table::
    :class: documentation-table

    ====================  ==========================================  =========================
    ..                    CLI                                         NX-API
    ====================  ==========================================  =========================
    Protocol              SSH                                         HTTP(S)

    Credentials           uses SSH keys / SSH-agent if present        uses HTTPS certificates if
                                                                      present
                          accepts ``-u myuser -k`` if using password

    Indirect Access       via a bastion (jump host)                   via a web proxy

    Connection Settings   ``ansible_connection:``                     ``ansible_connection:``
                            ``ansible.netcommon.network_cli``             ``ansible.netcommon.httpapi``

    |enable_mode|         supported: use ``ansible_become: yes``      not supported by NX-API
                          with ``ansible_become_method: enable``
                          and ``ansible_become_password:``

    Returned Data Format  ``stdout[0].``                              ``stdout[0].messages[0].``
    ====================  ==========================================  =========================

.. |enable_mode| replace:: Enable Mode |br| (Privilege Escalation) |br| supported as of 2.5.3


The ``ansible_connection: local`` has been deprecated. Please use ``ansible_connection: ansible.netcommon.network_cli`` or ``ansible_connection: ansible.netcommon.httpapi`` instead.

Using CLI in Ansible
====================

Example CLI ``group_vars/nxos.yml``
-----------------------------------

.. code-block:: yaml

   ansible_connection: ansible.netcommon.network_cli
   ansible_network_os: cisco.nxos.nxos
   ansible_user: myuser
   ansible_password: !vault...
   ansible_become: yes
   ansible_become_method: enable
   ansible_become_password: !vault...
   ansible_ssh_common_args: '-o ProxyCommand="ssh -W %h:%p -q bastion01"'


- If you are using SSH keys (including an ssh-agent) you can remove the ``ansible_password`` configuration.
- If you are accessing your host directly (not through a bastion/jump host) you can remove the ``ansible_ssh_common_args`` configuration.
- If you are accessing your host through a bastion/jump host, you cannot include your SSH password in the ``ProxyCommand`` directive. To prevent secrets from leaking out (for example in ``ps`` output), SSH does not support providing passwords via environment variables.

Example CLI task
----------------

.. code-block:: yaml

   - name: Backup current switch config (nxos)
     cisco.nxos.nxos_config:
       backup: yes
     register: backup_nxos_location
     when: ansible_network_os == 'cisco.nxos.nxos'



Using NX-API in Ansible
=======================

Enabling NX-API
---------------

Before you can use NX-API to connect to a switch, you must enable NX-API. To enable NX-API on a new switch via Ansible, use the ``nxos_nxapi`` module via the CLI connection. Set up group_vars/nxos.yml just like in the CLI example above, then run a playbook task like this:

.. code-block:: yaml

   - name: Enable NX-API
      cisco.nxos.nxos_nxapi:
          enable_http: yes
          enable_https: yes
      when: ansible_network_os == 'cisco.nxos.nxos'

To find out more about the options for enabling HTTP/HTTPS and local http see the :ref:`nxos_nxapi <nxos_nxapi_module>` module documentation.

Once NX-API is enabled, change your ``group_vars/nxos.yml`` to use the NX-API connection.

Example NX-API ``group_vars/nxos.yml``
--------------------------------------

.. code-block:: yaml

   ansible_connection: ansible.netcommon.httpapi
   ansible_network_os: cisco.nxos.nxos
   ansible_user: myuser
   ansible_password: !vault...
   proxy_env:
     http_proxy: http://proxy.example.com:8080

- If you are accessing your host directly (not through a web proxy) you can remove the ``proxy_env`` configuration.
- If you are accessing your host through a web proxy using ``https``, change ``http_proxy`` to ``https_proxy``.


Example NX-API task
-------------------

.. code-block:: yaml

   - name: Backup current switch config (nxos)
     cisco.nxos.nxos_config:
       backup: yes
     register: backup_nxos_location
     environment: "{{ proxy_env }}"
     when: ansible_network_os == 'cisco.nxos.nxos'

In this example the ``proxy_env`` variable defined in ``group_vars`` gets passed to the ``environment`` option of the module used in the task.

.. include:: shared_snippets/SSH_warning.txt

Cisco Nexus platform support matrix
===================================

The following platforms and software versions have been certified by Cisco to work with this version of Ansible.

.. table:: Platform / Software Minimum Requirements
     :align: center

     ===================  =====================
     Supported Platforms  Minimum NX-OS Version
     ===================  =====================
     Cisco Nexus N3k      7.0(3)I2(5) and later
     Cisco Nexus N9k      7.0(3)I2(5) and later
     Cisco Nexus N5k      7.3(0)N1(1) and later
     Cisco Nexus N6k      7.3(0)N1(1) and later
     Cisco Nexus N7k      7.3(0)D1(1) and later
     ===================  =====================

.. table:: Platform Models
     :align: center

     ========  ==============================================
     Platform  Description
     ========  ==============================================
     N3k       Support includes N30xx, N31xx and N35xx models
     N5k       Support includes all N5xxx models
     N6k       Support includes all N6xxx models
     N7k       Support includes all N7xxx models
     N9k       Support includes all N9xxx models
     ========  ==============================================

.. seealso::

    :ref:`timeout_options`

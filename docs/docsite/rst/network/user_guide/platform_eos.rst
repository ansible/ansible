.. _eos_platform_options:

***************************************
EOS Platform Options
***************************************

The `Arista EOS <https://galaxy.ansible.com/arista/eos>`_ collection supports multiple connections. This page offers details on how each connection works in Ansible and how to use it.

.. contents::
  :local:

Connections available
================================================================================

.. table::
    :class: documentation-table

    ====================  ==========================================  ===========================
    ..                    CLI                                         eAPI
    ====================  ==========================================  ===========================
    Protocol              SSH                                         HTTP(S)

    Credentials           uses SSH keys / SSH-agent if present        uses HTTPS certificates if
                                                                      present
                          accepts ``-u myuser -k`` if using password

    Indirect Access       via a bastion (jump host)                   via a web proxy

    Connection Settings   ``ansible_connection:``                     ``ansible_connection:``
                          ``ansible.netcommon.network_cli``           ``ansible.netcommon.httpapi``


    |enable_mode|         supported: |br|                             supported: |br|

                          * use ``ansible_become: yes``               * ``httpapi``
                            with ``ansible_become_method: enable``      uses ``ansible_become: yes``
                                                                        with ``ansible_become_method: enable``

    Returned Data Format  ``stdout[0].``                              ``stdout[0].messages[0].``
    ====================  ==========================================  ===========================

.. |enable_mode| replace:: Enable Mode |br| (Privilege Escalation)


The ``ansible_connection: local`` has been deprecated. Please use ``ansible_connection: ansible.netcommon.network_cli`` or ``ansible_connection: ansible.netcommon.httpapi`` instead.

Using CLI in Ansible
====================

Example CLI ``group_vars/eos.yml``
----------------------------------

.. code-block:: yaml

   ansible_connection: ansible.netcommon.network_cli
   ansible_network_os: arista.eos.eos
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

   - name: Backup current switch config (eos)
     arista.eos.eos_config:
       backup: yes
     register: backup_eos_location
     when: ansible_network_os == 'arista.eos.eos'



Using eAPI in Ansible
=====================

Enabling eAPI
-------------

Before you can use eAPI to connect to a switch, you must enable eAPI. To enable eAPI on a new switch with Ansible, use the ``arista.eos.eos_eapi`` module through the CLI connection. Set up ``group_vars/eos.yml`` just like in the CLI example above, then run a playbook task like this:

.. code-block:: yaml

   - name: Enable eAPI
     arista.eos.eos_eapi:
       enable_http: yes
       enable_https: yes
     become: true
     become_method: enable
     when: ansible_network_os == 'arista.eos.eos'

You can find more options for enabling HTTP/HTTPS connections in the :ref:`arista.eos.eos_eapi <ansible_collections.arista.eos.eos_eapi_module>` module documentation.

Once eAPI is enabled, change your ``group_vars/eos.yml`` to use the eAPI connection.

Example eAPI ``group_vars/eos.yml``
-----------------------------------

.. code-block:: yaml

   ansible_connection: ansible.netcommon.httpapi
   ansible_network_os: arista.eos.eos
   ansible_user: myuser
   ansible_password: !vault...
   ansible_become: yes
   ansible_become_method: enable
   proxy_env:
     http_proxy: http://proxy.example.com:8080

- If you are accessing your host directly (not through a web proxy) you can remove the ``proxy_env`` configuration.
- If you are accessing your host through a web proxy using ``https``, change ``http_proxy`` to ``https_proxy``.


Example eAPI task
-----------------

.. code-block:: yaml

   - name: Backup current switch config (eos)
     arista.eos.eos_config:
       backup: yes
     register: backup_eos_location
     environment: "{{ proxy_env }}"
     when: ansible_network_os == 'arista.eos.eos'

In this example the ``proxy_env`` variable defined in ``group_vars`` gets passed to the ``environment`` option of the module in the task.

.. include:: shared_snippets/SSH_warning.txt

.. seealso::

       :ref:`timeout_options`

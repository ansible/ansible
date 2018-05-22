.. _nxos_platform_options:

***************************************
NXOS Platform Options
***************************************

Cisco NXOS supports multiple connections. This page offers details on how each connection works in Ansible 2.5 and how to use it.

.. contents:: Topics

Connections Available
================================================================================

+---------------------------+-----------------------------------------------+-----------------------------------------+
|..                         | CLI                                           | NX-API                                  |
+===========================+===============================================+=========================================+
| **Protocol**              |  SSH                                          | HTTP(S)                                 |
+---------------------------+-----------------------------------------------+-----------------------------------------+
| | **Credentials**         | | uses SSH keys / SSH-agent if present        | | uses HTTPS certificates if present    |
| |                         | | accepts ``-u myuser -k`` if using password  | |                                       |
+---------------------------+-----------------------------------------------+-----------------------------------------+
| **Indirect Access**       | via a bastion (jump host)                     | via a web proxy                         |
+---------------------------+-----------------------------------------------+-----------------------------------------+
| | **Connection Settings** | | ``ansible_connection: network_cli``         | | ``ansible_connection: httpapi``       |
+---------------------------+-----------------------------------------------+-----------------------------------------+
| | **Enable Mode**         | | supported - use ``ansible_become: yes``     | | not supported by NX-API               |
| | (Privilege Escalation)  | | with ``ansible_become_method: enable``      | |                                       |
| | supported as of 2.5.3   | | and ``ansible_become_pass:``                | |                                       |
+---------------------------+-----------------------------------------------+-----------------------------------------+
| **Returned Data Format**  | ``stdout[0].``                                | ``stdout[0].messages[0].``              |
+---------------------------+-----------------------------------------------+-----------------------------------------+

For legacy playbooks, NXOS still supports ``ansible_connection: local``. We recommend modernizing to use ``ansible_connection: network_cli`` or ``ansible_connection: httpapi`` as soon as possible.

Using CLI in Ansible 2.5
================================================================================

Example CLI ``group_vars/nxos.yml``
-----------------------------------

.. code-block:: yaml

   ansible_connection: network_cli
   ansible_network_os: nxos
   ansible_user: myuser
   ansible_ssh_pass: !vault...
   ansible_become: yes
   ansible_become_method: enable
   ansible_become_pass: !vault...
   ansible_ssh_common_args: '-o ProxyCommand="ssh -W %h:%p -q bastion01"'


- If you are using SSH keys (including an ssh-agent) you can remove the ``ansible_ssh_pass`` configuration.
- If you are accessing your host directly (not through a bastion/jump host) you can remove the ``ansible_ssh_common_args`` configuration.
- If you are accessing your host through a bastion/jump host, you cannot include your SSH password in the ``ProxyCommand`` directive. To prevent secrets from leaking out (for example in ``ps`` output), SSH does not support providing passwords via environment variables.

Example CLI Task
----------------

.. code-block:: yaml

   - name: Backup current switch config (nxos)
     nxos_config:
       backup: yes
     register: backup_nxos_location
     when: ansible_network_os == 'nxos'



Using NX-API in Ansible 2.5
================================================================================

Enabling NX-API
---------------

Before you can use NX-API to connect to a switch, you must enable NX-API. To enable NX-API on a new switch via Ansible, use the ``nxos_nxapi`` module via the CLI connection. Set up group_vars/nxos.yml just like in the CLI example above, then run a playbook task like this:

.. code-block:: yaml

   - name: Enable NX-API
      nxos_nxapi:
          enable_http: yes
          enable_https: yes
      when: ansible_network_os == 'nxos'

To find out more about the options for enabling HTTP/HTTPS and local http see the :ref:`nxos_nxapi <nxos_nxapi_module>` module documentation.

Once NX-API is enabled, change your ``group_vars/nxos.yml`` to use the NX-API connection.

Example NX-API ``group_vars/nxos.yml``
--------------------------------------

.. code-block:: yaml

   ansible_connection: httpapi
   ansible_network_os: nxos
   ansible_user: myuser
   ansible_ssh_pass: !vault... 
   proxy_env:
     http_proxy: http://proxy.example.com:8080

- If you are accessing your host directly (not through a web proxy) you can remove the ``proxy_env`` configuration.
- If you are accessing your host through a web proxy using ``https``, change ``http_proxy`` to ``https_proxy``.


Example NX-API Task
-------------------

.. code-block:: yaml

   - name: Backup current switch config (nxos)
     nxos_config:
       backup: yes
     register: backup_nxos_location
     environment: "{{ proxy_env }}"
     when: ansible_network_os == 'nxos'

In this example the ``proxy_env`` variable defined in ``group_vars`` gets passed to the ``environment`` option of the module used in the task.

.. include:: shared_snippets/SSH_warning.txt

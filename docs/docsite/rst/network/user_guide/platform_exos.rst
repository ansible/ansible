.. _exos_platform_options:

***************************************
EXOS Platform Options
***************************************

Extreme EXOS Ansible modules support multiple connections. This page offers details on how each connection works in Ansible and how to use it.

.. contents:: Topics

Connections Available
================================================================================

+---------------------------+-----------------------------------------------+-----------------------------------------+
|..                         | CLI                                           | EXOS-API                                |
+===========================+===============================================+=========================================+
| **Protocol**              |  SSH                                          | HTTP(S)                                 |
+---------------------------+-----------------------------------------------+-----------------------------------------+
| | **Credentials**         | | uses SSH keys / SSH-agent if present        | | uses HTTPS certificates if present    |
| |                         | | accepts ``-u myuser -k`` if using password  | |                                       |
+---------------------------+-----------------------------------------------+-----------------------------------------+
| **Indirect Access**       | via a bastion (jump host)                     | via a web proxy                         |
+---------------------------+-----------------------------------------------+-----------------------------------------+
| | **Connection Settings** | | ``ansible_connection: network_cli``         | | ``ansible_connection: httpapi``       |
| |                         | |                                             | |                                       |
| |                         | |                                             | |                                       |
| |                         | |                                             | |                                       |
| |                         | |                                             | |                                       |
+---------------------------+-----------------------------------------------+-----------------------------------------+
| | **Enable Mode**         | | not supported by EXOS                       | | not supported by EXOS                 |
| | (Privilege Escalation)  | |                                             | |                                       |
| |                         | |                                             | |                                       |
+---------------------------+-----------------------------------------------+-----------------------------------------+
| **Returned Data Format**  | ``stdout[0].``                                | ``stdout[0].messages[0].``              |
+---------------------------+-----------------------------------------------+-----------------------------------------+

EXOS does not support ``ansible_connection: local``. You must use ``ansible_connection: network_cli`` or ``ansible_connection: httpapi``

Using CLI in Ansible
====================

Example CLI ``group_vars/exos.yml``
-----------------------------------

.. code-block:: yaml

   ansible_connection: network_cli
   ansible_network_os: exos
   ansible_user: myuser
   ansible_password: !vault...
   ansible_ssh_common_args: '-o ProxyCommand="ssh -W %h:%p -q bastion01"'


- If you are using SSH keys (including an ssh-agent) you can remove the ``ansible_password`` configuration.
- If you are accessing your host directly (not through a bastion/jump host) you can remove the ``ansible_ssh_common_args`` configuration.
- If you are accessing your host through a bastion/jump host, you cannot include your SSH password in the ``ProxyCommand`` directive. To prevent secrets from leaking out (for example in ``ps`` output), SSH does not support providing passwords via environment variables.

Example CLI Task
----------------

.. code-block:: yaml

   - name: Retrieve EXOS OS version
     exos_command:
       commands: show version
     when: ansible_network_os == 'exos'

Complete Steps for the above Example CLI Task
---------------------------------------------

1.Ensure hosts are configured for inventory file and hosts files on the host OS :

# cat ~/playbooks/hosts
[all_exos]
S2
S1

# cat /etc/hosts
192.168.75.110  S1
192.168.75.105  S2

2.Ensure the ansible.cfg is configured for the inventory path

# cat ansible.cfg
[defaults]
ansible_python_interpreter = ~/ansible/venv/bin/python
host_key_checking = False
inventory = ~/playbooks/hosts

3. Create the group_vars/exos.yaml file

# cat playbooks/group_vars/exos.yaml
---
ansible_network_os: exos
ansible_connection: network_cli
ansible_user: xtrm_user
ansible_ssh_pass: xtrm_pass

4. Create a playbook.yaml

# cat playbook.yml

---
- hosts: all
  tasks:
  - name: Retrieve EXOS OS version
    exos_command:
      commands: show version
    when: ansible_network_os == 'exos'


5. Run the playbook using ansible-playbook


# ansible-playbook playbook.yml




Using EXOS-API in Ansible
=========================

Example EXOS-API ``group_vars/exos.yml``
----------------------------------------

.. code-block:: yaml

   ansible_connection: httpapi
   ansible_network_os: exos
   ansible_user: myuser
   ansible_password: !vault...
   proxy_env:
     http_proxy: http://proxy.example.com:8080

- If you are accessing your host directly (not through a web proxy) you can remove the ``proxy_env`` configuration.
- If you are accessing your host through a web proxy using ``https``, change ``http_proxy`` to ``https_proxy``.


Example EXOS-API Task
---------------------

.. code-block:: yaml

   - name: Retrieve EXOS OS version
     exos_command:
       commands: show version
     when: ansible_network_os == 'exos'

In this example the ``proxy_env`` variable defined in ``group_vars`` gets passed to the ``environment`` option of the module used in the task.

.. include:: shared_snippets/SSH_warning.txt

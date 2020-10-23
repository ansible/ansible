.. _vmware_http_api_usage:

***********************************
Using VMware HTTP API using Ansible
***********************************

.. contents::
   :local:

Introduction
============

This guide will show you how to utilize Ansible to use VMware HTTP APIs to automate various tasks.

Scenario requirements
=====================

* Software

    * Ansible 2.5 or later must be installed.

    * We recommend installing the latest version with pip: ``pip install Pyvmomi`` on the Ansible control node
      (as the OS packages are usually out of date and incompatible) if you are planning to use any existing VMware modules.

* Hardware

    * vCenter Server 6.5 and above with at least one ESXi server

* Access / Credentials

    * Ansible (or the target server) must have network access to either the vCenter server or the ESXi server

    * Username and Password for vCenter

Caveats
=======

- All variable names and VMware object names are case sensitive.
- You need to use Python 2.7.9 version in order to use ``validate_certs`` option, as this version is capable of changing the SSL verification behaviours.
- VMware HTTP APIs are introduced in vSphere 6.5 and above so minimum level required in 6.5.
- There are very limited number of APIs exposed, so you may need to rely on XMLRPC based VMware modules.


Example description
===================

With the following Ansible playbook you can find the VMware ESXi host system(s) and can perform various tasks depending on the list of host systems.
This is a generic example to show how Ansible can be utilized to consume VMware HTTP APIs.

.. code-block:: yaml

    ---
    - name: Example showing VMware HTTP API utilization
      hosts: localhost
      gather_facts: no
      vars_files:
        - vcenter_vars.yml
      vars:
        ansible_python_interpreter: "/usr/bin/env python3"
      tasks:
        - name: Login into vCenter and get cookies
          uri:
            url: https://{{ vcenter_server }}/rest/com/vmware/cis/session
            force_basic_auth: yes
            validate_certs: no
            method: POST
            user: "{{ vcenter_user }}"
            password: "{{ vcenter_pass }}"
          register: login

        - name: Get all hosts from vCenter using cookies from last task
          uri:
            url: https://{{ vcenter_server }}/rest/vcenter/host
            force_basic_auth: yes
            validate_certs: no
            headers:
              Cookie: "{{ login.set_cookie }}"
          register: vchosts

        - name: Change Log level configuration of the given hostsystem
          vmware_host_config_manager:
            hostname: "{{ vcenter_server }}"
            username: "{{ vcenter_user }}"
            password: "{{ vcenter_pass }}"
            esxi_hostname: "{{ item.name }}"
            options:
              'Config.HostAgent.log.level': 'error'
            validate_certs: no
          loop: "{{ vchosts.json.value }}"
          register: host_config_results


Since Ansible utilizes the VMware HTTP API using the ``uri`` module to perform actions, in this use case it will be connecting directly to the VMware HTTP API from localhost.

This means that playbooks will not be running from the vCenter or ESXi Server.

Note that this play disables the ``gather_facts`` parameter, since you don't want to collect facts about localhost.

Before you begin, make sure you have:

- Hostname of the vCenter server
- Username and password for the vCenter server
- Version of vCenter is at least 6.5

For now, you will be entering these directly, but in a more advanced playbook this can be abstracted out and stored in a more secure fashion using :ref:`ansible-vault` or using `Ansible Tower credentials <https://docs.ansible.com/ansible-tower/latest/html/userguide/credentials.html>`_.

If your vCenter server is not setup with proper CA certificates that can be verified from the Ansible server, then it is necessary to disable validation of these certificates by using the ``validate_certs`` parameter. To do this you need to set ``validate_certs=False`` in your playbook.

As you can see, we are using the ``uri`` module in first task to login into the vCenter server and storing result in the ``login`` variable using register. In the second task, using cookies from the first task we are gathering information about the ESXi host system.

Using this information, we are changing the ESXi host system's advance configuration.

What to expect
--------------

Running this playbook can take some time, depending on your environment and network connectivity. When the run is complete you will see

.. code-block:: yaml

    "results": [
        {
            ...
            "invocation": {
                "module_args": {
                    "cluster_name": null,
                    "esxi_hostname": "10.76.33.226",
                    "hostname": "10.65.223.114",
                    "options": {
                        "Config.HostAgent.log.level": "error"
                    },
                    "password": "VALUE_SPECIFIED_IN_NO_LOG_PARAMETER",
                    "port": 443,
                    "username": "administrator@vsphere.local",
                    "validate_certs": false
                }
            },
            "item": {
                "connection_state": "CONNECTED",
                "host": "host-21",
                "name": "10.76.33.226",
                "power_state": "POWERED_ON"
            },
            "msg": "Config.HostAgent.log.level changed."
            ...
        }
    ]


Troubleshooting
---------------

If your playbook fails:

- Check if the values provided for username and password are correct.
- Check if you are using vCenter 6.5 and onwards to use this HTTP APIs.

.. seealso::

    `VMware vSphere and Ansible From Zero to Useful by @arielsanchezmor <https://www.youtube.com/watch?v=0_qwOKlBlo8>`_
        vBrownBag session video related to VMware HTTP APIs
    `Sample Playbooks for using VMware HTTP APIs <https://github.com/Akasurde/ansible-vmware-http>`_
        GitHub repo for examples of Ansible playbook to manage VMware using HTTP APIs

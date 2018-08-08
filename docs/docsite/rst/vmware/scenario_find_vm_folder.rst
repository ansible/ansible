.. _vmware_guest_find_folder:

******************************************************
Find folder path of an existing VMware virtual machine
******************************************************

.. contents:: Topics

Introduction
============

This guide will show you how to utilize Ansible to find folder path of an existing VMware virtual machine.

Scenario Requirements
=====================

* Software

    * Ansible 2.5 or later must be installed.

    * The Python module ``Pyvmomi`` must be installed on the Ansible control node (or Target host if not executing against localhost).

    * We recommend installing the latest version with pip: ``pip install Pyvmomi`` (as the OS packages are usually out of date and incompatible).

* Hardware

    * At least one standalone ESXi server or

    * vCenter Server with at least one ESXi server

* Access / Credentials

    * Ansible (or the target server) must have network access to the either vCenter server or the ESXi server

    * Username and Password for vCenter or ESXi server

Caveats
=======

- All variable names and VMware object names are case sensitive.
- You need to use Python 2.7.9 version in order to use ``validate_certs`` option, as this version is capable of changing the SSL verification behaviours.


Example Description
===================

With the following Ansible playbook you can find the folder path of an existing virtual machine using name.

.. code-block:: yaml

    ---
    - name: Find folder path of an existing virtual machine
      hosts: localhost
      gather_facts: False
      vars_files:
        - vcenter_vars.yml
      vars:
        ansible_python_interpreter: "/usr/bin/env python3"
      tasks:
        - set_fact:
            vm_name: "DC0_H0_VM0"

        - name: "Find folder for VM - {{ vm_name }}"
          vmware_guest_find:
            hostname: "{{ vcenter_server }}"
            username: "{{ vcenter_user }}"
            password: "{{ vcenter_pass }}"
            validate_certs: False
            name: "{{ vm_name }}"
          delegate_to: localhost
          register: vm_facts


Since Ansible utilizes the VMware API to perform actions, in this use case it will be connecting directly to the API from localhost.

This means that playbooks will not be running from the vCenter or ESXi Server.

Note that this play disables the ``gather_facts`` parameter, since you don't want to collect facts about localhost.

You can run these modules against another server that would then connect to the API if localhost does not have access to vCenter. If so, the required Python modules will need to be installed on that target server. We recommend installing the latest version with pip: ``pip install Pyvmomi`` (as the OS packages are usually out of date and incompatible).

Before you begin, make sure you have:

- Hostname of the ESXi server or vCenter server
- Username and password for the ESXi or vCenter server
- Name of the existing Virtual Machine for which you want to collect folder path

For now, you will be entering these directly, but in a more advanced playbook this can be abstracted out and stored in a more secure fashion using :ref:`ansible-vault` or using `Ansible Tower credentials <http://docs.ansible.com/ansible-tower/latest/html/userguide/credentials.html>`_.

If your vCenter or ESXi server is not setup with proper CA certificates that can be verified from the Ansible server, then it is necessary to disable validation of these certificates by using the ``validate_certs`` parameter. To do this you need to set ``validate_certs=False`` in your playbook.

The name of existing virtual machine will be used as input for ``vmware_guest_find`` module via ``name`` parameter.


What to expect
--------------

Running this playbook can take some time, depending on your environment and network connectivity. When the run is complete you will see

.. code-block:: yaml

    "vm_facts": {
        "changed": false,
        "failed": false,
        ...
        "folders": [
            "/F0/DC0/vm/F0"
        ]
    }


Troubleshooting
---------------

If your playbook fails:

- Check if the values provided for username and password are correct.
- Check if the datacenter you provided is available.
- Check if the virtual machine specified exists and you have respective permissions to access VMware object.
- Ensure the full folder path you specified already exists.

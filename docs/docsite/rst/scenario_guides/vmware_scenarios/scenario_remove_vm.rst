.. _vmware_guest_remove_virtual_machine:

*****************************************
Remove an existing VMware virtual machine
*****************************************

.. contents:: Topics

Introduction
============

This guide will show you how to utilize Ansible to remove an existing VMware virtual machine.

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

    * Hosts in the ESXi cluster must have access to the datastore that the template resides on.

Caveats
=======

- All variable names and VMware object names are case sensitive.
- You need to use Python 2.7.9 version in order to use ``validate_certs`` option, as this version is capable of changing the SSL verification behaviours.
- ``vmware_guest`` module tries to mimic VMware Web UI and workflow, so the virtual machine must be in powered off state in order to remove it from the VMware inventory.

.. warning::

   The removal VMware virtual machine using ``vmware_guest`` module is destructive operation and can not be reverted, so it is strongly recommended to take the backup of virtual machine and related files (vmx and vmdk files) before proceeding.

Example Description
===================

In this use case / example, user will be removing a virtual machine using name. The following Ansible playbook showcases the basic parameters that are needed for this.

.. code-block:: yaml

    ---
    - name: Remove virtual machine
      gather_facts: no
      vars_files:
        - vcenter_vars.yml
      vars:
        ansible_python_interpreter: "/usr/bin/env python3"
      hosts: localhost
      tasks:
        - set_fact:
            vm_name: "VM_0003"
            datacenter: "DC1"

        - name: Remove "{{ vm_name }}"
          vmware_guest:
            hostname: "{{ vcenter_server }}"
            username: "{{ vcenter_user }}"
            password: "{{ vcenter_pass }}"
            validate_certs: no
            cluster: "DC1_C1"
            name: "{{ vm_name }}"
            state: absent
          delegate_to: localhost
          register: facts


Since Ansible utilizes the VMware API to perform actions, in this use case it will be connecting directly to the API from localhost.

This means that playbooks will not be running from the vCenter or ESXi Server.

Note that this play disables the ``gather_facts`` parameter, since you don't want to collect facts about localhost.

You can run these modules against another server that would then connect to the API if localhost does not have access to vCenter. If so, the required Python modules will need to be installed on that target server. We recommend installing the latest version with pip: ``pip install Pyvmomi`` (as the OS packages are usually out of date and incompatible).

Before you begin, make sure you have:

- Hostname of the ESXi server or vCenter server
- Username and password for the ESXi or vCenter server
- Name of the existing Virtual Machine you want to remove

For now, you will be entering these directly, but in a more advanced playbook this can be abstracted out and stored in a more secure fashion using :ref:`ansible-vault` or using `Ansible Tower credentials <https://docs.ansible.com/ansible-tower/latest/html/userguide/credentials.html>`_.

If your vCenter or ESXi server is not setup with proper CA certificates that can be verified from the Ansible server, then it is necessary to disable validation of these certificates by using the ``validate_certs`` parameter. To do this you need to set ``validate_certs=False`` in your playbook.

The name of existing virtual machine will be used as input for ``vmware_guest`` module via ``name`` parameter.


What to expect
--------------

- You will not see any JSON output after this playbook completes as compared to other operations performed using ``vmware_guest`` module.

.. code-block:: yaml

    {
        "changed": true
    }

- State is changed to ``True`` which notifies that the virtual machine is removed from the VMware inventory. This can take some time depending upon your environment and network connectivity.


Troubleshooting
---------------

If your playbook fails:

- Check if the values provided for username and password are correct.
- Check if the datacenter you provided is available.
- Check if the virtual machine specified exists and you have permissions to access the datastore.
- Ensure the full folder path you specified already exists. It will not create folders automatically for you.

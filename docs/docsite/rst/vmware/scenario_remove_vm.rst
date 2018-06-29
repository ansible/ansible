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

    * The Python module ``Pyvmomi`` must be installed on the Ansible (or Target host if not executing against localhost).

    * Installing the latest ``Pyvmomi`` via pip is recommended [as the OS packages are usually out of date and incompatible].

* Hardware

    * At least one standalone ESXi server or

    * vCenter Server with at least one ESXi server

* Access / Credentials

    * Ansible (or the target server) must have network access to the either vCenter server or the ESXi server

    * Username and Password for vCenter or ESXi server

Assumptions
===========

- All variable names and VMware object names are case sensitive.
- You need to use Python 2.7.9 version in order to use ``validate_certs`` option, as this version is capable of changing the SSL verification behaviours.

Caveats
=======

- Hosts in the ESXi cluster must have access to the datastore that the template resides on.
- ``vmware_guest`` module tries to mimick VMware Web UI and workflow, so the virtual machine must be in powered off state in order to remove it from the VMware inventory.

.. warning::

   The removal VMware virtual machine using ``vmware_guest`` module is destructive and can not be reverted, so it is recommended to take backup before proceeding.

Example Description
===================

In this use case / example, user will be selecting a virtual machine using name for removal. The following Ansible playbook showcases the basic parameters that are needed for this.

.. code-block:: yaml

    ---
    - name: Purge virtual machine
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

The ``gather_facts`` parameter will be disabled as it is not necessarily need to collect facts about localhost.

User can run these modules against another server that would then connect to the API if localhost does not have access to vCenter. If so, the required Python modules will need to be installed on that target server.

To begin, there are a few bits of information we will need -

* First is the hostname of the ESXi server or vCenter server.

* After this, you will need the username and password for this server. For now, you will be entering these directly, but in a more advanced playbook this can be abstracted out and stored in a more secure fashion using :ref:`ansible-vault` or using `Ansible Tower credentials <http://docs.ansible.com/ansible-tower/latest/html/userguide/credentials.html>`_.

* If your vCenter or ESXi server is not setup with proper CA certificates that can be verified from the Ansible server, then it is necessary to disable validation of these certificates by using the ``validate_certs`` parameter. To do this you need to set ``validate_certs=False`` in your playbook.

Now you need to supply the information about the existing virtual machine which will be removed. The name of virtual machine will be used as input for ``vmware_guest`` module. Specify name of the existing virtual machine as ``name`` parameter.


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

Things to inspect

- Check if the values provided for username and password are correct.
- Check if the datacenter you provided is available.
- Check if the virtual machine specified exists and you have permissions to access the datastore.
- Ensure the full folder path you specified already exists. It will not create folders automatically for you.

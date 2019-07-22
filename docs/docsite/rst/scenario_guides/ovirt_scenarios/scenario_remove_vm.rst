.. _oVirt_guest_remove_virtual_machine:

*****************************************
Remove an existing oVirt virtual machine
*****************************************

.. contents::
   :local:

Introduction
============

This guide will show you how to utilize Ansible to remove an existing oVirt virtual machine.

Scenario Requirements
=====================

* Software

    * Ansible 2.5 or later must be installed.

    * The Python module ``Pyvmomi`` must be installed on the Ansible control node (or Target host if not executing against localhost).

    * We recommend installing the latest version with pip: ``pip install Pyvmomi`` (as the OS packages are usually out of date and incompatible).

* Hardware

    * At least one standalone host server or

    * oVirt/RHV engine Server with at least one host server

* Access / Credentials

    * Ansible (or the target server) must have network access to the either oVirt/RHV engine server or the host server

    * Username and Password for oVirt/RHV engine or host server

    * Hosts in the host cluster must have access to the storage domain that the template resides on.

Caveats
=======

- All variable names and oVirt object names are case sensitive.
- You need to use Python 2.7.9 version in order to use ``validate_certs`` option, as this version is capable of changing the SSL verification behaviours.


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
          oVirt_guest:
            hostname: "{{ vcenter_server }}"
            username: "{{ vcenter_user }}"
            password: "{{ vcenter_pass }}"
            validate_certs: no
            cluster: "DC1_C1"
            name: "{{ vm_name }}"
            state: absent
          delegate_to: localhost
          register: facts


Since Ansible utilizes the oVirt API to perform actions, in this use case it will be connecting directly to the API from localhost.

This means that playbooks will not be running from the oVirt/RHV engine or host Server.

Note that this play disables the ``gather_facts`` parameter, since you don't want to collect facts about localhost.

You can run these modules against another server that would then connect to the API if localhost does not have access to oVirt/RHV engine. If so, the required Python modules will need to be installed on that target server. We recommend installing the latest version with pip: ``pip install Pyvmomi`` (as the OS packages are usually out of date and incompatible).

Before you begin, make sure you have:

- Hostname of the host server or oVirt/RHV engine server
- Username and password for the host or oVirt/RHV engine server
- Name of the existing Virtual Machine you want to remove

For now, you will be entering these directly, but in a more advanced playbook this can be abstracted out and stored in a more secure fashion using :ref:`ansible-vault` or using `Ansible Tower credentials <https://docs.ansible.com/ansible-tower/latest/html/userguide/credentials.html>`_.

If your oVirt/RHV engine or host server is not setup with proper CA certificates that can be verified from the Ansible server, then it is necessary to disable validation of these certificates by using the ``validate_certs`` parameter. To do this you need to set ``validate_certs=False`` in your playbook.

The name of existing virtual machine will be used as input for ``oVirt_guest`` module via ``name`` parameter.


What to expect
--------------

- You will not see any JSON output after this playbook completes as compared to other operations performed using ``oVirt_guest`` module.

.. code-block:: yaml

    {
        "changed": true
    }

- State is changed to ``True`` which notifies that the virtual machine is removed from the oVirt inventory. This can take some time depending upon your environment and network connectivity.


Troubleshooting
---------------

If your playbook fails:

- Check if the values provided for username and password are correct.
- Check if the datacenter you provided is available.
- Check if the virtual machine specified exists and you have permissions to access the storage domain.
- Ensure the full folder path you specified already exists. It will not create folders automatically for you.

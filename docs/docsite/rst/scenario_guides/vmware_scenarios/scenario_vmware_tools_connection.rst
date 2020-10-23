.. _vmware_tools_connection:

************************************
Using vmware_tools connection plugin
************************************

.. contents::
   :local:

Introduction
============

This guide will show you how to utilize VMware Connection plugin to communicate and automate various tasks on VMware guest machines.

Scenario requirements
=====================

* Software

    * Ansible 2.9 or later must be installed.

    * We recommend installing the latest version with pip: ``pip install Pyvmomi`` on the Ansible control node
      (as the OS packages are usually out of date and incompatible) if you are planning to use any existing VMware modules.

* Hardware

    * vCenter Server 6.5 and above

* Access / Credentials

    * Ansible (or the target server) must have network access to either the vCenter server

    * Username and Password for vCenter with required permissions

    * VMware tools or openvm-tools with required dependencies like Perl installed on the given virtual machine

Caveats
=======

- All variable names and VMware object names are case sensitive.
- You need to use Python 2.7.9 version in order to use ``validate_certs`` option, as this version is capable of changing the SSL verification behaviors.


Example description
===================

User can run playbooks against VMware virtual machines using ``vmware_tools`` connection plugin.

In order work with ``vmware_tools`` connection plugin, you will need to specify hostvars for the given virtual machine.

For example, if you want to run a playbook on a virtual machine called ``centos_7`` located at ``/Asia-Datacenter1/prod/centos_7`` in the given vCenter, you will need to specify hostvars as follows:

.. code-block:: ini

    [centos7]
    host1

    [centos7:vars]
    # vmware_tools related variables
    ansible_connection=vmware_tools
    ansible_vmware_host=10.65.201.128
    ansible_vmware_user=administrator@vsphere.local
    ansible_vmware_password=Esxi@123$%
    ansible_vmware_validate_certs=no

    # Location of the virtual machine
    ansible_vmware_guest_path=Asia-Datacenter1/vm/prod/centos_7

    # Credentials
    ansible_vmware_tools_user=root
    ansible_vmware_tools_password=Secret123

Here, we are providing vCenter details and credentials for the given virtual machine to run the playbook on.
If your virtual machine path is ``Asia-Datacenter1/prod/centos_7``, you specify ``ansible_vmware_guest_path`` as ``Asia-Datacenter1/vm/prod/centos_7``. Please take a note that ``/vm`` is added in the virtual machine path, since this is a logical folder structure in the VMware inventory.

Let us now run following playbook,

.. code-block:: yaml

    ---
    - name: Example showing VMware Connection plugin
      hosts: centos7
      tasks:
        - name: Gather information about temporary directory inside VM
          shell: ls /tmp


Since Ansible utilizes the ``vmware-tools`` or ``openvm-tools`` service capabilities running in the virtual machine to perform actions, in this use case it will be connecting directly to the guest machine.


For now, you will be entering credentials in plain text, but in a more advanced playbook this can be abstracted out and stored in a more secure fashion using :ref:`ansible-vault` or using `Ansible Tower credentials <https://docs.ansible.com/ansible-tower/latest/html/userguide/credentials.html>`_.


What to expect
--------------

Running this playbook can take some time, depending on your environment and network connectivity. When the run is complete you will see:

.. code-block:: yaml

    {
        "changed": true,
        "cmd": "ls /tmp",
        "delta": "0:00:00.005440",
        "end": "2020-10-01 07:30:56.940813",
        "rc": 0,
        "start": "2020-10-01 07:30:56.935373",
        "stderr": "",
        "stderr_lines": [],
        "stdout": "ansible_command_payload_JzWiL9\niso",
        "stdout_lines": ["ansible_command_payload_JzWiL9", "iso", "vmware-root"]
    }

Troubleshooting
---------------

If your playbook fails:

- Check if the values provided for username and password are correct.
- Check if the path of virtual machine is correct. Please mind that ``/vm/`` needs to be provided while specifying virtual machine location.

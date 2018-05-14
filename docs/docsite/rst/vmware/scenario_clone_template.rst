.. _vmware_guest_from_template:

****************************************
Deploy a virtual machine from a template
****************************************

Introduction
============

This guide will show you how to utilize Ansible to clone a virtual machine from already existing VMware template.

Scenario Requirements
=====================

* Software

    * Ansible 2.5 or later must be installed

    * The Python module *Pyvmomi* must be installed on the Ansible (or Target host if not executing against localhost)

    * Installing the latest *Pyvmomi* via pip is recommended [as the OS packages are usually out of date and incompatible]

* Hardware

    * At least one standalone ESXi server or

    * vCenter Server with at least one ESXi server

* Access / Credentials

    * Ansible (or the target server) must have network access to the either vCenter server or the ESXi server you will be deploying to

    * Username and Password

    * Administrator user with following privileges

        - Virtual machine.Provisioning.Clone virtual machine on the virtual machine you are cloning
        - Virtual machine.Inventory.Create from existing on the datacenter or virtual machine folder
        - Virtual machine.Configuration.Add new disk on the datacenter or virtual machine folder.
        - Resource.Assign virtual machine to resource pool on the destination host, cluster, or resource pool.
        - Datastore.Allocate space on the destination datastore or datastore folder.
        - Network.Assign network on the network to which the virtual machine will be assigned.
        - Virtual machine.Provisioning.Customize on the virtual machine or virtual machine folder if you are customizing the guest operating system.
        - Virtual machine.Provisioning.Read customization specifications on the root vCenter Server if you are customizing the guest operating system.

Assumptions
===========

- All variable names and VMware object names are case sensitive
- VMware allows creation of virtual machine and templates with same name across datacenters and within datacenters.
- You need to use Python 2.7.9 version in order to use *validate_certs* option, as this version is capable of changing the SSL verification behaviours.

Caveats
=======

- Hosts in the ESXI cluster must have access to the datastore that the template resides on.
- Multiple templates with the same name will cause module failures.
- In order to utilize Guest Customization, VMWare Tools must be installed on the template. For Linux, the open-vm-tools package is recommended, and it requires that Perl be installed.


Example Description
===================

In this use case / example, we will be selecting a virtual machine template and cloning it into a specific folder in our Datacenter / Cluster.  The following Ansible playbook showcases the basic parameters that are needed for this.

.. code-block:: yaml

    ---
    - name: Create a VM from a template
      hosts: localhost
      connection: local
      gather_facts: no
      tasks:
      - name: Clone the template
        vmware_guest:
          hostname: 192.0.2.44
          username: administrator@vsphere.local
          password: vmware
          validate_certs: False
          name: testvm_2
          template: template_el7
          datacenter: dc1
          folder: /dc1/vm
          state: poweredon
          wait_for_ip_address: yes


Since Ansible utilizes the VMware API to perform actions, in this use case we will be connecting directly to the API from our localhost. This means that our playbooks will not be running from the vCenter or ESXi Server. We do not necessarily need to collect facts about our localhost, so the *gather_facts* parameter will be disabled. You can run these modules against another server that would then connect to the API if your localhost does not have access to vCenter. If so, the required Python modules will need to be installed on that target server.

To begin, there are a few bits of information we will need. First and foremost is the hostname of the ESXi server or vCenter server. After this, we will need the username and password for this server. For now, you will be entering these directly, but in a more advanced playbook this can be abstracted out and stored in a more secure fashion [1][2]. If your vCenter or ESXi server is not setup with proper CA certificates that can be verified from the Ansible server, then it is necessary to disable validation of these certificates by using the *validate_certs* parameter. To do this you need to set `validate_certs=False` in your playbook.

Now we get into supplying the information about the VM we will be creating. We will need to give this VM a name. It must conform to all VMware requirements for naming conventions.  Next we will need the display name of the template that we will be cloning. This must match exactly with what is displayed in VMware.  A folder to place this virtual machine in can then be specified. This can either be a relative path or a full path to the folder including the Datacenter. We must then specify a state for the VM.  This simply tells it which action we want to take, in this case we will be ensure that the VM exists and is powered on.  An optional parameter is *wait_for_ip_address*, this will tell Ansible to wait for the machine to fully boot up and VMware Tools is running before completing this task.


What to expect
--------------

- You will see a bit of JSON output after this playbook completes. This output shows various parameters that are returned from the module and from vCenter about the newly created VM.

- State is changed to *True* which notifies that the virtual machine is built using given template. The module will not complete until the clone task in VMware is finished. This can take some time depending on your environment.

- If you utilize the *wait_for_ip_address* parameter, then it will also increase the clone time as it will wait until virtual machine boots into the OS and an IP Address has been assigned to the given NIC.



Troubleshooting
---------------

Things to inspect

- Check if the values provided for username and password are correct
- Check if the datacenter you provided is available
- Check if the template specified exists and you have permissions to access the datastore
- Ensure the full folder path you specified already exists. It will not create folders automatically for you.



Appendix
--------

- [1] - https://docs.ansible.com/ansible/latest/vault.html

- [2] - http://docs.ansible.com/ansible-tower/latest/html/userguide/credentials.html


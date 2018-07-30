.. _vmware_guest_from_template:

****************************************
Deploy a virtual machine from a template
****************************************

.. contents:: Topics

Introduction
============

This guide will show you how to utilize Ansible to clone a virtual machine from already existing VMware template or existing VMware guest.

Scenario Requirements
=====================

* Software

    * Ansible 2.5 or later must be installed

    * The Python module ``Pyvmomi`` must be installed on the Ansible (or Target host if not executing against localhost)

    * Installing the latest ``Pyvmomi`` via ``pip`` is recommended [as the OS provided packages are usually out of date and incompatible]

* Hardware

    * At least one standalone ESXi server or

    * vCenter Server with at least one ESXi server

* Access / Credentials

    * Ansible (or the target server) must have network access to the either vCenter server or the ESXi server you will be deploying to

    * Username and Password

    * Administrator user with following privileges

        - Virtual machine.Provisioning.Clone virtual machine on the virtual machine you are cloning
        - Virtual machine.Inventory.Create from existing on the datacenter or virtual machine folder
        - Virtual machine.Configuration.Add new disk on the datacenter or virtual machine folder
        - Resource.Assign virtual machine to resource pool on the destination host, cluster, or resource pool
        - Datastore.Allocate space on the destination datastore or datastore folder
        - Network.Assign network on the network to which the virtual machine will be assigned
        - Virtual machine.Provisioning.Customize on the virtual machine or virtual machine folder if you are customizing the guest operating system
        - Virtual machine.Provisioning.Read customization specifications on the root vCenter Server if you are customizing the guest operating system

Assumptions
===========

- All variable names and VMware object names are case sensitive
- VMware allows creation of virtual machine and templates with same name across datacenters and within datacenters
- You need to use Python 2.7.9 version in order to use ``validate_certs`` option, as this version is capable of changing the SSL verification behaviours

Caveats
=======

- Hosts in the ESXi cluster must have access to the datastore that the template resides on.
- Multiple templates with the same name will cause module failures.
- In order to utilize Guest Customization, VMWare Tools must be installed on the template. For Linux, the ``open-vm-tools`` package is recommended, and it requires that ``Perl`` be installed.


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
          hostname: "{{ vcenter_ip }}"
          username: "{{ vcenter_username }}"
          password: "{{ vcenter_password }}"
          validate_certs: False
          name: testvm_2
          template: template_el7
          datacenter: "{{ datacenter_name }}"
          folder: /DC1/vm
          state: poweredon
          cluster: "{{ cluster_name }}"
          wait_for_ip_address: yes


Since Ansible utilizes the VMware API to perform actions, in this use case we will be connecting directly to the API from our localhost. This means that our playbooks will not be running from the vCenter or ESXi Server. We do not necessarily need to collect facts about our localhost, so the ``gather_facts`` parameter will be disabled. You can run these modules against another server that would then connect to the API if your localhost does not have access to vCenter. If so, the required Python modules will need to be installed on that target server.

To begin, there are a few bits of information we will need. First and foremost is the hostname of the ESXi server or vCenter server. After this, you will need the username and password for this server. For now, you will be entering these directly, but in a more advanced playbook this can be abstracted out and stored in a more secure fashion using  :ref:`ansible-vault` or using `Ansible Tower credentials <http://docs.ansible.com/ansible-tower/latest/html/userguide/credentials.html>`_. If your vCenter or ESXi server is not setup with proper CA certificates that can be verified from the Ansible server, then it is necessary to disable validation of these certificates by using the ``validate_certs`` parameter. To do this you need to set ``validate_certs=False`` in your playbook.

Now you need to supply the information about the virtual machine which will be created. Give your virtual machine a name, one that conforms to all VMware requirements for naming conventions.  Next, select the display name of the template from which you want to clone new virtual machine. This must match what's displayed in VMware Web UI exactly. Then you can specify a folder to place this new virtual machine in. This path can either be a relative path or a full path to the folder including the Datacenter. You may need to specify a state for the virtual machine.  This simply tells the module which action you want to take, in this case you will be ensure that the virtual machine exists and is powered on.  An optional parameter is ``wait_for_ip_address``, this will tell Ansible to wait for the virtual machine to fully boot up and VMware Tools is running before completing this task.


What to expect
--------------

- You will see a bit of JSON output after this playbook completes. This output shows various parameters that are returned from the module and from vCenter about the newly created VM.

.. code-block:: yaml

    {
        "changed": true,
        "instance": {
            "annotation": "",
            "current_snapshot": null,
            "customvalues": {},
            "guest_consolidation_needed": false,
            "guest_question": null,
            "guest_tools_status": "guestToolsNotRunning",
            "guest_tools_version": "0",
            "hw_cores_per_socket": 1,
            "hw_datastores": [
                "ds_215"
            ],
            "hw_esxi_host": "192.0.2.44",
            "hw_eth0": {
                "addresstype": "assigned",
                "ipaddresses": null,
                "label": "Network adapter 1",
                "macaddress": "00:50:56:8c:19:f4",
                "macaddress_dash": "00-50-56-8c-19-f4",
                "portgroup_key": "dvportgroup-17",
                "portgroup_portkey": "0",
                "summary": "DVSwitch: 50 0c 5b 22 b6 68 ab 89-fc 0b 59 a4 08 6e 80 fa"
            },
            "hw_files": [
                "[ds_215] testvm_2/testvm_2.vmx",
                "[ds_215] testvm_2/testvm_2.vmsd",
                "[ds_215] testvm_2/testvm_2.vmdk"
            ],
            "hw_folder": "/DC1/vm",
            "hw_guest_full_name": null,
            "hw_guest_ha_state": null,
            "hw_guest_id": null,
            "hw_interfaces": [
                "eth0"
            ],
            "hw_is_template": false,
            "hw_memtotal_mb": 512,
            "hw_name": "testvm_2",
            "hw_power_status": "poweredOff",
            "hw_processor_count": 2,
            "hw_product_uuid": "420cb25b-81e8-8d3b-dd2d-a439ee54fcc5",
            "hw_version": "vmx-13",
            "instance_uuid": "500cd53b-ed57-d74e-2da8-0dc0eddf54d5",
            "ipv4": null,
            "ipv6": null,
            "module_hw": true,
            "snapshots": []
        },
        "invocation": {
            "module_args": {
                "annotation": null,
                "cdrom": {},
                "cluster": "DC1_C1",
                "customization": {},
                "customization_spec": null,
                "customvalues": [],
                "datacenter": "DC1",
                "disk": [],
                "esxi_hostname": null,
                "folder": "/DC1/vm",
                "force": false,
                "guest_id": null,
                "hardware": {},
                "hostname": "192.0.2.44",
                "is_template": false,
                "linked_clone": false,
                "name": "testvm_2",
                "name_match": "first",
                "networks": [],
                "password": "VALUE_SPECIFIED_IN_NO_LOG_PARAMETER",
                "port": 443,
                "resource_pool": null,
                "snapshot_src": null,
                "state": "present",
                "state_change_timeout": 0,
                "template": "template_el7",
                "username": "administrator@vsphere.local",
                "uuid": null,
                "validate_certs": false,
                "vapp_properties": [],
                "wait_for_ip_address": true
            }
        }
    }

- State is changed to ``True`` which notifies that the virtual machine is built using given template. The module will not complete until the clone task in VMware is finished. This can take some time depending on your environment.

- If you utilize the ``wait_for_ip_address`` parameter, then it will also increase the clone time as it will wait until virtual machine boots into the OS and an IP Address has been assigned to the given NIC.



Troubleshooting
---------------

Things to inspect

- Check if the values provided for username and password are correct
- Check if the datacenter you provided is available
- Check if the template specified exists and you have permissions to access the datastore
- Ensure the full folder path you specified already exists. It will not create folders automatically for you


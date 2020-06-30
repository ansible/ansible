*****************************
ThinkAgile CP Ansible Modules
*****************************

This repository contains Lenovo-created Ansible modules
for automating workflows with the ThinkAgile CP composable cloud platform.

Getting Started
===============
The following instructions will show you how to download and install the
tacp_info, tacp_instance, and tacp_network modules into your existing 
Ansible environment.

Requirements
------------
- Python >= 3.6
- python3-pip
- ansible
- tacp


Installation
------------
Download this git respository.

``cd ~``

``git clone https://github.com/lenovo/ansible.lenovo-tacp.git``

``cd ./ansible.lenovo-tacp``

|

The tacp modules and module_utils files can be added to any of the following dfirectories:

- any directory added to the ``ANSIBLE_LIBRARY`` environment variable (``$ANSIBLE_LIBRARY`` takes a colon-separated list like ``$PATH``)

- ``~/.ansible/plugins/``

- On CentOS/RHEL systems, ``/usr/share/ansible/plugins/``

|

1. For example, create the ``~/.ansible/plugins/`` directory:

``[user@hostname ansible.lenovo-tacp]# mkdir -p ~/.ansible/plugins/``

2. Create the ``~/.ansible/plugins/module_utils`` directory:

``[user@hostname ansible.lenovo-tacp]# mkdir -p ~/.ansible/plugins/module_utils``

3. Create the ``~/.ansible/plugins/modules/cloud`` directory:

``[user@hostname ansible.lenovo-tacp]# mkdir -p ~/.ansible/plugins/modules/cloud``

4. Copy the ``module_utils/tacp_ansible/`` directory from this ansible.lenovo-tacp repo into
   the local ansible installation's ``module_utils/`` directory. In this example the module files 
   are copied to the ``/usr/share/ansible/plugins`` location, which requires ``sudo``.

``[user@hostname ansible.lenovo-tacp]# sudo cp -R ./lib/ansible/module_utils/tacp_ansible 
~/.ansible/plugins/module_utils``

5. Copy the ``modules/tacp/`` directory from this ansible.lenovo-tacp repo into
   the local ansible installation's ``modules/cloud/`` directory.

``[user@hostname ansible.lenovo-tacp]# sudo cp -R ./lib/ansible/modules/tacp 
~/.ansible/plugins/modules/cloud``

6. Verify the manual installation worked:

.. code-block:: shell 

  [user@hostname ansible.lenovo-tacp]# ansible-doc -t module tacp_instance
  > TACP_INSTANCE    (/home/user/.ansible/plugins/modules/cloud/tacp/tacp_instance.py)

        This module can be used to create new application instances on the ThinkAgile CP cloud platform, as well as delete and modify power states of existing application instances. Currently this module cannot modify the resources of
        existing application instances aside from performing deletion and power state operations.
        .
        .
        .

Examples
========

**tacp_info**

.. code-block:: yaml

   ---
   - name: Test tacp_info Ansible module for ThinkAgile CP
     hosts: localhost
     gather_facts: false
     tasks:
     - name: Get details about application instances from ThinkAgile CP
       tacp_info:
         api_key: "{{ api_key}}"
         resource: instance

     - name: Get details about datacenters and networks from ThinkAgile CP
       tacp_info:
         api_key: "{{ api_key}}"
         resource: "{{ resource }}"
      loop:
         - datacenter
         - vlan
         - vnet
      loop_control:
         loop_var: resource

      - name: Get a list of the available marketplace application templates from
            ThinkAgile CP
        tacp_info:
          api_key: "{{ api_key}}"
          resource: marketplace_template

**tacp_instance**

.. code-block:: yaml

   ---
   - name: Test tacp_instance Ansible module for ThinkAgile CP
     hosts: localhost
     gather_facts: false
     tasks:
      - name: Create a basic VM on ThinkAgile CP
        tacp_instance:
          api_key: "{{ api_key }}"
          name: Basic_VM1
          state: started
          datacenter: Datacenter1
          migration_zone: Zone1
          template: CentOS 7.5 (64-bit) - Lenovo Template
          storage_pool: Pool1
          vcpu_cores: 1
          memory: 4096GB
          disks:
          - name: Disk 0
            size_gb: 50
            boot_order: 1
          nics:
          - name: vNIC 0
            type: VNET
            network: VNET-TEST
            boot_order: 2

      - name: Create a shutdown VM with multiple disks and set its NIC to the first 
            boot device
        tacp_instance:
          api_key: "{{ api_key }}"
          name: Basic_VM2
          state: started
          datacenter: Datacenter1
          migration_zone: Zone1
          template: RHEL 7.4 (Minimal) - Lenovo Template
          storage_pool: Pool1
          vcpu_cores: 1
          memory: 8G
          disks:
            - name: Disk 0
              size_gb: 50
              boot_order: 2
            - name: Disk 1
              size_gb: 200
              boot_order: 3
          nics:
            - name: vNIC 0
              type: VLAN
              network: VLAN-300
              boot_order: 1

      - name: Create a VM with multiple disks with limits, and two NICs with static
            MAC addresses, and don't power it on after creation
        tacp_instance:
          api_key: "{{ api_key }}"
          name: Basic_VM3
          state: shutdown
          datacenter: Datacenter1
          migration_zone: Zone1
          template: RHEL 7.4 (Minimal) - Lenovo Template
          storage_pool: Pool1
          vcpu_cores: 1
          memory: 8GB
          disks:
            - name: Disk 0
              size_gb: 50
              boot_order: 2
              iops_limit: 200
            - name: Disk 1
              size_gb: 200
              boot_order: 3
              bandwidth_limit: 10000000
          nics:
            - name: vNIC 0
              type: VLAN
              network: VLAN-300
              boot_order: 4
              firewall_override: Allow-All
            - name: vNIC 1
              type: VNET
              network: PXE-VNET
              boot_order: 1
              mac_address: b4:d1:35:00:00:01

        - name: Restart all of my Basic_VMs on ThinkAgile CP
          tacp_instance:
            api_key: "{{ api_key }}"
            name: "{{ instance }}"
            state: restarted
          loop:
            - Basic_VM1
            - Basic_VM2
            - Basic_VM3
          loop_control:
            loop_var: instance

        - name: Delete Basic_VM1 from ThinkAgile CP
          tacp_instance:
            api_key: "{{ api_key }}"
            name: Basic_VM1
            state: absent

        - name: Create a variety of VMs on TACP in a loop
          tacp_instance:
            api_key: "{{ api_key }}"
            name: "{{ instance.name }}"
            state: "{{ instance.state }}"
            datacenter: Datacenter2
            migration_zone: Zone2
            template: "{{ instance.template }}"
            storage_pool: Pool2
            vcpu_cores: "{{ instance.vcpu_cores }}"
            memory: "{{ instance.memory }}"
            disks:
              - name: Disk 0
                size_gb: 100
                boot_order: 1
            nics:
              - name: vNIC 0
                type: "{{ instance.network_type }}"
                network: "{{ instance.network_name }}"
                mac_address: "{{ instance.mac_address }}"
                boot_order: 2
          loop:
            - { name: CentOS VM 1,
                state: started,
                template: "CentOS 7.5 (64-bit) - Lenovo Template",
                vcpu_cores: 2,
                memory: 4096MB,
                network_type: VLAN,
                network_name: VLAN-15,
                mac_address: b4:d1:35:00:0f:f0 }
            - { name: RHEL VM 11,
                state: stopped,
                template: "RHEL 7.4 (Minimal) - Lenovo Template",
                vcpu_cores: 6,
                memory: 6g,
                network_type: VNET,
                network_name: Production-VNET,
                mac_address: b4:d1:35:00:0f:f1 }
            - { name: Windows Server 2019 VM 1,
                state: started,
                template: "Windows Server 2019 Standard - Lenovo Template",
                vcpu_cores: 8,
                memory: 16GB,
                network_type: VNET,
                network_name: Internal-VNET,
                mac_address: b4:d1:35:00:0f:f2 }
          loop_control:
            loop_var: instance

**tacp_network**

.. code-block:: yaml

   ---
   - name: Test tacp_network Ansible module for ThinkAgile CP
     hosts: localhost
     gather_facts: false
     tasks:
      - name: Create a VLAN network on ThinkAgile CP
        tacp_network:
          api_key: "{{ api_key }}"
          name: VLAN-15
          state: present
          network_type: VLAN
          vlan_tag: 15

      - name: Delete a VLAN network on ThinkAgile CP
        tacp_network:
          api_key: "{{ api_key }}"
          name: VLAN-15
          state: absent
          network_type: VLAN

      - name: Create a VNET network with an NFV on TACP
        tacp_network:
          api_key: "{{ api_key }}"
          name:  Private VNET
          state: present
          network_type: VNET
          autodeploy_nfv: True
          network_address: 192.168.1.0
          subnet_mask: 255.255.255.0
          gateway: 192.168.1.1
          dhcp:
            dhcp_start: 192.168.1.100
            dhcp_end: 192.168.1.200
            domain_name: test.local
            lease_time: 86400 # seconds, 24 hours
            dns1: 1.1.1.1
            dns2: 8.8.8.8
            static_bindings:
              - hostname: Host1
                ip_address: 192.168.1.101
                mac_address: b4:d1:35:00:0f:f1
              - hostname: Host2
                ip_address: 192.168.1.102
                mac_address: b4:d1:35:00:0f:f2
          routing:
            type: VLAN
            network: Lab-VLAN
            address_mode: static
            ip_address: 192.168.100.201
            subnet_mask: 255.255.255.0
            gateway: 192.168.100.1
          nfv:
            datacenter: Datacenter1
            storage_pool: Pool1
            migration_zone: Zone1
            cpu_cores: 1
            memory: 1G
            auto_recovery: True

Authors
=======
Lenovo (`@lenovo <http://github.com/lenovo/>`_)

Xander Madsen (`@xmadsen <http://github.com/xmadsen/>`_)

Marius Vigariu (`@mariusvigariu <http://github.com/mariusvigariu/>`_)

License
=======

GNU General Public License v3.0 or later

See `COPYING <COPYING>`_ to see the full text.

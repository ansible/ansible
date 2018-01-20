Alibaba Cloud Compute Services Guide
====================================

.. _alicloud_intro:

Introduction
````````````

Ansible contains several modules for controlling and managing Alibaba Cloud Compute Services (Alicloud).  The purpose of this
section is to explain how to put Ansible modules together to use Ansible in Alicloud context.

All of the modules require footmark and it can be installed by python's "sudo pip install footmark" in your control machine.

Classically, ansible will execute tasks in remote machines which defined in its hosts, most cloud-control steps occur on your local machine with reference to the regions to control.

Normally, we'll use the following pattern for provisioning steps::

    - hosts: localhost
      connection: local
      vars:
        - ...
      tasks:
        - ...

.. _alicloud_authentication:

Authentication
``````````````
   
Authentication with the Alicloud-related modules is handled by either
specifying your access and secret key as ENV variables or module arguments.

For environment variables::

    export ALICLOUD_ACCESS_KEY='Alicloud123'
    export ALICLOUD_SECRET_KEY='AlicloudSecret123'

For storing these in a vars_file, ideally encrypted with `ansible-vault <https://docs.ansible.com/ansible/2.4/vault.html>`_ considering its security::

    ---
    alicloud_access_key: "--REMOVED--"
    alicloud_secret_key: "--REMOVED--"

Note that if you store your credentials in vars_file, you need to refer to them in each Alicloud-module. For example::

    - alicloud_instance:
      alicloud_access_key: "{{alicloud_access_key}}"
      alicloud_secret_key: "{{alicloud_secret_key}}"
      image_id: "..."

.. _alicloud_provisioning:

Provisioning
````````````

There are a number of modules to create ECS instance, disk, VPC, VSwitch, Security Group and other resources.

An example of making sure there are only 5 instances tagged 'NewECS' and other resources as Alicloud Module follows.

In the example below, the ``count`` of instances is set to 5. This means if there are 0 instances already existing, then
5 new instances would be created. If there were 2 instances, only 3 would be created, and if there were 8 instances,
3 instances would be terminated.

If ``count_tag`` is not specified, ``coun`` would use ``instance_name`` to create specified number of instances.

::

    # alicloud_setup.yml

    - hosts: localhost
      connection: local

      tasks:

        - name: Create VPC
          alicloud_vpc:
            cidr_block: '{{ cidr_block }}'
            vpc_name: new_vpc
          register: created_vpc

        - name: Create VSwitch
          alicloud_vswitch:
            alicloud_zone: '{{ alicloud_zone }}'
            cidr_block: '{{ vsw_cidr }}'
            vswitch_name: new_vswitch
            vpc_id: '{{ created_vpc.vpc_id }}'
          register: created_vsw

        - name: Create security group
          alicloud_security_group:
            name: new_group
            vpc_id: '{{ created_vpc.vpc_id }}'
            rules:
              - proto: tcp
                port_range: 22/22
                cidr_ip: 0.0.0.0/0
                priority: 1
            rules_egress:
              - proto: tcp
                port_range: 80/80
                cidr_ip: 192.168.0.54/32
                priority: 1
          register: created_group

        - name: Create a set of instances
          alicloud_instance:
             group_id: '{{ created_group.group_id }}'
             instance_type: ecs.n4.small
             image_id: "{{ ami_id }}"
             instance_name: "My-new-instance"
             instance_tags:
                 Name: NewECS
                 Version: 0.0.1
             count: 5
             count_tag:
                 Name: NewECS
             allocate_public_ip: true
             max_bandwidth_out: 50
             vswitch_id: '{{ created_vsw.vswitch_id}}'
          register: create_instance

The data about what vpc, vswitch, instances and other resource are created are being saved by the "register" keyword in the corresponding variable.

Each of the Alicloud modules offers a variety of parameter options. Not all options are demonstrated in the above example.
See each individual module for further details and examples.


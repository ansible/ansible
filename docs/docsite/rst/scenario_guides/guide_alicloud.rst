Alibaba Cloud Compute Services Guide
====================================

.. _alicloud_intro:

Introduction
````````````

Ansible contains several modules for controlling and managing Alibaba Cloud Compute Services (Alicloud).  This guide
explains how to use the Alicloud Ansible modules together.

All Alicloud modules require ``footmark`` - install it on your control machine with ``pip install footmark``.

Cloud modules, including Alicloud modules, execute on your local machine (the control machine) with ``connection: local``, rather than on remote machines defined in your hosts.

Normally, you'll use the following pattern for plays that provision Alicloud resources::

    - hosts: localhost
      connection: local
      vars:
        - ...
      tasks:
        - ...

.. _alicloud_authentication:

Authentication
``````````````

You can specify your Alicloud authentication credentials (access key and secret key) by passing them as
environment variables or by storing them in a vars file.

To pass authentication credentials as environment variables::

    export ALICLOUD_ACCESS_KEY='Alicloud123'
    export ALICLOUD_SECRET_KEY='AlicloudSecret123'

To store authentication credentials in a vars_file, encrypt them with :ref:`Ansible Vault<vault>` to keep them secure, then list them::

    ---
    alicloud_access_key: "--REMOVED--"
    alicloud_secret_key: "--REMOVED--"

Note that if you store your credentials in a vars_file, you need to refer to them in each Alicloud module. For example::

    - ali_instance:
        alicloud_access_key: "{{alicloud_access_key}}"
        alicloud_secret_key: "{{alicloud_secret_key}}"
        image_id: "..."

.. _alicloud_provisioning:

Provisioning
````````````

Alicloud modules create Alicloud ECS instances, disks, virtual private clouds, virtual switches, security groups and other resources.

You can use the ``count`` parameter to control the number of resources you create or terminate. For example, if you want exactly 5 instances tagged ``NewECS``,
set the ``count`` of instances to 5 and the ``count_tag`` to ``NewECS``, as shown in the last task of the example playbook below.
If there are no instances with the tag ``NewECS``, the task creates 5 new instances. If there are 2 instances with that tag, the task
creates 3 more. If there are 8 instances with that tag, the task terminates 3 of those instances.

If you do not specify a ``count_tag``, the task creates the number of instances you specify in ``count`` with the ``instance_name`` you provide.

::

    # alicloud_setup.yml

    - hosts: localhost
      connection: local

      tasks:

        - name: Create VPC
          ali_vpc:
            cidr_block: '{{ cidr_block }}'
            vpc_name: new_vpc
          register: created_vpc

        - name: Create VSwitch
          ali_vswitch:
            alicloud_zone: '{{ alicloud_zone }}'
            cidr_block: '{{ vsw_cidr }}'
            vswitch_name: new_vswitch
            vpc_id: '{{ created_vpc.vpc.id }}'
          register: created_vsw

        - name: Create security group
          ali_security_group:
            name: new_group
            vpc_id: '{{ created_vpc.vpc.id }}'
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
          ali_instance:
             security_groups: '{{ created_group.group_id }}'
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
             vswitch_id: '{{ created_vsw.vswitch.id}}'
          register: create_instance

In the example playbook above, data about the vpc, vswitch, group, and instances created by this playbook
are saved in the variables defined by the "register" keyword in each task.

Each Alicloud module offers a variety of parameter options. Not all options are demonstrated in the above example.
See each individual module for further details and examples.

.. _porting_2.3_guide:

*************************
Ansible 2.3 Porting Guide
*************************

This section discusses the behavioral changes between Ansible 2.2 and Ansible 2.3.

It is intended to assist in updating your playbooks, plugins and other parts of your Ansible infrastructure so they will work with this version of Ansible.


We suggest you read this page along with `Ansible Changelog for 2.3 <https://github.com/ansible/ansible/blob/stable-2.3/CHANGELOG.md>`_ to understand what updates you may need to make.

This document is part of a collection on porting. The complete list of porting guides can be found at :ref:`porting guides <porting_guides>`.

.. contents:: Topics

Playbook
========

Restructued async to work with action plugins
---------------------------------------------

In Ansible 2.2 (and possibly earlier) the `async:` keyword could not be used in conjunction with the action plugins such as `service`. This limitation has been removed in Ansible 2.3

**NEW** In Ansible 2.3:


.. code-block:: guess

    - name: Install nginx asynchronously
      service:
        name: nginx
        state: restarted
      async: 45


OpenBSD version facts
---------------------

The `ansible_distribution_release` and `ansible_distribution_version` facts on OpenBSD hosts were reversed in Ansible 2.2 and earlier. This has been changed so that version has the numeric portion and release has the name of the release.

**OLD** In Ansible 2.2 (and earlier)


.. code-block:: guess

    "ansible_distribution": "OpenBSD"
    "ansible_distribution_release": "6.0",
    "ansible_distribution_version": "release",

**NEW** In Ansible 2.3:


.. code-block:: guess

    "ansible_distribution": "OpenBSD",
    "ansible_distribution_release": "release",
    "ansible_distribution_version": "6.0",


Names Blocks
------------

Blocks can now have names, this allows you to avoid the ugly `# this block is for...` comments.


**NEW** In Ansible 2.3:


.. code-block:: guess

    - name: Block test case
      hosts: localhost
      tasks:
       - name: Attempt to setup foo
         block:
           - debug: msg='I execute normally'
           - command: /bin/false
           - debug: msg='I never execute, cause ERROR!'
         rescue:
           - debug: msg='I caught an error'
           - command: /bin/false
           - debug: msg='I also never execute :-('
         always:
           - debug: msg="this always executes"


Use of multiple tags
--------------------

Specifying ``--tags`` (or ``--skip-tags``) multiple times on the command line currently leads to the last specified tag overriding all the other specified tags. This behaviour is deprecated. In the future, if you specify --tags multiple times the tags will be merged together. From now on, using ``--tags`` multiple times on one command line will emit a deprecation warning. Setting the ``merge_multiple_cli_tags`` option to True in the ``ansible.cfg`` file will enable the new behaviour.

In 2.4, the default will be to merge the tags. You can enable the old overwriting behavior via the config option.
In 2.5, multiple ``--tags`` options will be merged with no way to go back to the old behaviour.


Other caveats
-------------

Here are some rare cases that might be encountered when updating. These are mostly caused by the more stringent parser validation and the capture of errors that were previously ignored.


* Made ``any_errors_fatal`` inheritable from play to task and all other objects in between.

Modules
=======

No major changes in this version.

Modules removed
---------------

No major changes in this version.

Deprecation notices
-------------------

The following modules will be removed in Ansible 2.5. Please update your playbooks accordingly.

* :ref:`ec2_vpc <ec2_vpc_module>`
* :ref:`cl_bond <cl_bond_module>`
* :ref:`cl_bridge <cl_bridge_module>`
* :ref:`cl_img_install <cl_img_install_module>`
* :ref:`cl_interface <cl_interface_module>`
* :ref:`cl_interface_policy <cl_interface_policy_module>`
* :ref:`cl_license <cl_license_module>`
* :ref:`cl_ports <cl_ports_module>`
* :ref:`nxos_mtu <nxos_mtu_module>` use :ref:`nxos_system <nxos_system_module>` instead

Noteworthy module changes
-------------------------

AWS lambda
^^^^^^^^^^
Previously ignored changes that only affected one parameter. Existing deployments may have outstanding changes that this bug fix will apply.


Mount
^^^^^

Mount: Some fixes so bind mounts are not mounted each time the playbook runs.


Plugins
=======

No major changes in this version.

Porting custom scripts
======================

No major changes in this version.

Networking
==========

There have been a number of changes to number of changes to how Networking Modules operate.

Playbooks should still use ``connection: local``.

The following changes apply to:

* dellos6
* dellos9
* dellos10
* eos
* ios
* iosxr
* junos
* sros
* vyos

Deprecation of top-level connection arguments
---------------------------------------------

**OLD** In Ansible 2.2:

.. code-block:: guess

    - name: example of using top-level options for connection properties
      ios_command:
        commands: show version
        host: "{{ inventory_hostname }}"
        username: cisco
        password: cisco
        authorize: yes
        auth_pass: cisco

Will result in:

.. code-block:: guess

   [WARNING]: argument username has been deprecated and will be removed in a future version
   [WARNING]: argument host has been deprecated and will be removed in a future version
   [WARNING]: argument password has been deprecated and will be removed in a future version


**NEW** In Ansible 2.3:


.. code-block:: guess

   - name: Gather facts
     eos_facts:
       gather_subset: all
       provider:
         username: myuser
         password: "{{ networkpassword }}"
         transport: cli
         host: "{{ ansible_host }}"

delegate_to vs ProxyCommand
---------------------------

The new connection framework for Network Modules in Ansible 2.3 that uses ``cli`` transport
no longer supports the use of the ``delegate_to`` directive.
In order to use a bastion or intermediate jump host to connect to network devices over ``cli``
transport, network modules now support the use of ``ProxyCommand``.

To use ``ProxyCommand`` configure the proxy settings in the Ansible inventory
file to specify the proxy host via ``ansible_ssh_common_args``.

For details on how to do this see the :ref:`network proxy guide <network_delegate_to_vs_ProxyCommand>`.

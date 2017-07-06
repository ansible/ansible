.. _porting_2.3_guide:

*************************
Ansible 2.3 Porting Guide
*************************

This section discusses the behavioral changes between Ansible 2.2 and Ansible 2.3.

It is intended to assist in updating your playbooks, plugins and other parts of your Ansible infrastructure so they will work with this version of Ansible.


We suggest you read this page along with `Ansible Changelog <https://github.com/ansible/ansible/blob/devel/CHANGELOG.md#2.3>`_ to understand what updates you may need to make.

This document is part of a collection on porting. The complete list of porting guides can be found at :ref:`porting guides <porting_guides>`.

.. contents:: Topics

Playbook
========


Deprecated
==========



Use of multiple tags
--------------------

Specifying ``--tags`` (or ``--skip-tags``) multiple times on the command line currently leads to the last one overriding all the previous ones. This behaviour is deprecated. In the future, if you specify --tags multiple times the tags will be merged together. From now on, using ``--tags`` multiple times on one command line will emit a deprecation warning. Setting the ``merge_multiple_cli_tags`` option to True in the ``ansible.cfg`` file will enable the new behaviour.

In 2.4, the default will be to merge the tags. You can enable the old overwriting behavior via the config option.
In 2.5, multiple ``--tags`` options will be merged with no way to go back to the old behaviour.


Other caveats
-------------

Here are some rare cases that might be encountered when updating. These are mostly caused by the more stringent parser validation and the capture of errors that were previously ignored.

* The version and release facts for OpenBSD hosts were reversed. This has been changed so that version has the numeric portion and release has the name of the release.

* made ``any_errors_fatal`` inheritable from play to task and all other objects in between.

Modules
=======

Major changes in popular modules are detailed here.

Modules removed
---------------

The following modules no longer exist:

* None

Deprecation notices
-------------------

The following modules will be removed in Ansible 2.5. Please update your playbooks accordingly.

* :ref:`ec2_vpc <ec2_vpc>`
* :ref:`cl_bond <cl_bond>`
* :ref:`cl_bridge <cl_bridge>`
* :ref:`cl_img_install <cl_img_install>`
* :ref:`cl_interface <cl_interface>`
* :ref:`cl_interface_policy <cl_interface_policy>`
* :ref:`cl_license <cl_license>`
* :ref:`cl_ports <cl_ports>`
* :ref:`nxos_mtu <nxos_mtu>` use :ref:`nxos_system <nxos_system>` instead

Noteworthy module changes
-------------------------

AWS lambda
^^^^^^^^^^
Previously ignored changes that only affected one parameter. Existing deployments may have outstanding changes that this bug fix will apply.


oVirt/RHV
^^^^^^^^^

* Added support for 4.1 features and the following:
* data centers, clusters, hosts, storage domains and networks management.
* hosts and virtual machines affinity groups and labels.
* users, groups and permissions management.
* Improved virtual machines and disks management.

Mount
^^^^^

Mount: Some fixes so bind mounts are not mounted each time the playbook runs.

.. Nothing currently in this section so commented out 
   Placeholder left to keep consistent formatting with porting_guide_2.3.rst 

   Plugins
   =======

   Porting custom scripts
   ======================

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

.. code-block:: yaml

    - name: example of using top-level options for connection properties
      ios_command:
        commands: show version
        host: "{{ inventory_hostname }}"
        username: cisco
        password: cisco
        authorize: yes
        auth_pass: cisco

Will result in:

.. code-block:: yaml

   [WARNING]: argument username has been deprecated and will be removed in a future version
   [WARNING]: argument host has been deprecated and will be removed in a future version
   [WARNING]: argument password has been deprecated and will be removed in a future version


**NEW** In Ansible 2.3:


.. code-block:: yaml

   - name: Gather facts
     - eos_facts:
         gather_subset: all
         provider:
           username: myuser
           password: "{{ networkpassword }}"
           transport: cli
           host: "{{ ansible_host }}"

delegate_to vs ProxyCommand
---------------------------

The new connection framework for Network Modules in Ansible 2.3 no longer supports the use of the
``delegate_to`` directive.  In order to use a bastion or intermediate jump host
to connect to network devices, network modules now support the use of
``ProxyCommand``.

To use ``ProxyCommand`` configure the proxy settings in the Ansible inventory
file to specify the proxy host.

.. code-block:: ini

    [nxos]
    nxos01
    nxos02

    [nxos:vars]
    ansible_ssh_common_args='-o ProxyCommand="ssh -W %h:%p -q bastion01"'


With the configuration above, simply build and run the playbook as normal with
no additional changes necessary.  The network module will now connect to the
network device by first connecting to the host specified in
``ansible_ssh_common_args`` which is ``bastion01`` in the above example.


.. notes: Using ``ProxyCommand`` with passwords via variables

   It is a feature that SSH doesn't support providing passwords via environment variables.
   This is done to prevent secrets from leaking out, for example in ``ps`` output.

   We recommend using SSH Keys, and if needed and ssh-agent, rather than passwords, where ever possible.


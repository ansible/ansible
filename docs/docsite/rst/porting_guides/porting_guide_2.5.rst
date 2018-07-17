.. _porting_2.5_guide:

*************************
Ansible 2.5 Porting Guide
*************************

This section discusses the behavioral changes between Ansible 2.4 and Ansible 2.5.

It is intended to assist in updating your playbooks, plugins and other parts of your Ansible infrastructure so they will work with this version of Ansible.

We suggest you read this page along with `Ansible Changelog for 2.5 <https://github.com/ansible/ansible/blob/stable-2.5/changelogs/CHANGELOG-v2.5.rst>`_ to understand what updates you may need to make.

This document is part of a collection on porting. The complete list of porting guides can be found at :ref:`porting guides <porting_guides>`.

.. contents:: Topics

Playbook
========

Dynamic includes and attribute inheritance
------------------------------------------

In Ansible version 2.4, the concept of dynamic includes (``include_tasks``) versus static imports (``import_tasks``) was introduced to clearly define the differences in how ``include`` works between dynamic and static includes.

All attributes applied to a dynamic ``include_*`` would only apply to the include itself, while attributes applied to a
static ``import_*`` would be inherited by the tasks within.

This separation was only partially implemented in Ansible version 2.4. As of Ansible version 2.5, this work is complete and the separation now behaves as designed; attributes applied to an ``include_*`` task will not be inherited by the tasks within.

To achieve an outcome similar to how Ansible worked prior to version 2.5, playbooks should use an explicit application of the attribute on the needed tasks, or use blocks to apply the attribute to many tasks. Another option is to use a static ``import_*`` when possible instead of a dynamic task.

**OLD** In Ansible 2.4:

.. code-block:: yaml

    - include_tasks: "{{ ansible_distribution }}.yml"
      tags:
        - distro_include

Included file:

.. code-block:: yaml

    - block:
        - debug:
            msg: "In included file"

        - apt:
            name: nginx
            state: latest

**NEW** In Ansible 2.5:

Including task:

.. code-block:: yaml

    - include_tasks: "{{ ansible_distribution }}.yml"
      tags:
        - distro_include

Included file:

.. code-block:: yaml

    - block:
        - debug:
            msg: "In included file"

        - apt:
            name: nginx
            state: latest
      tags:
        - distro_include

The relevant change in those examples is, that in Ansible 2.5, the included file defines the tag ``distro_include`` again. The tag is not inherited automatically.

Fixed handling of keywords and inline variables
-----------------------------------------------

We made several fixes to how we handle keywords and 'inline variables', to avoid conflating the two. Unfortunately these changes mean you must specify whether `name` is a keyword or a variable when calling roles. If you have playbooks that look like this::

    roles:
        - { role: myrole, name: Justin, othervar: othervalue, become: True}

You will run into errors because Ansible reads name in this context as a keyword. Beginning in 2.5, if you want to use a variable name that is also a keyword, you must explicitly declare it as a variable for the role::

    roles:
        - { role: myrole, vars: {name: Justin, othervar: othervalue}, become: True}


For a full list of keywords see ::ref::`Playbook Keywords`.

Migrating from with_X to loop
-----------------------------

.. include:: ../user_guide/shared_snippets/with2loop.txt


Deprecated
==========

Jinja tests used as filters
---------------------------

Using Ansible-provided jinja tests as filters will be removed in Ansible 2.9.

Prior to Ansible 2.5, jinja tests included within Ansible were most often used as filters. The large difference in use is that filters are referenced as ``variable | filter_name`` while jinja tests are referenced as ``variable is test_name``.

Jinja tests are used for comparisons, while filters are used for data manipulation and have different applications in jinja. This change is to help differentiate the concepts for a better understanding of jinja, and where each can be appropriately used.

As of Ansible 2.5, using an Ansible provided jinja test with filter syntax, will display a deprecation error.

**OLD** In Ansible 2.4 (and earlier) the use of an Ansible included jinja test would likely look like this:

.. code-block:: yaml

    when:
        - result | failed
        - not result | success

**NEW** In Ansible 2.5 it should be changed to look like this:

.. code-block:: yaml

    when:
        - result is failed
        - results is not successful

In addition to the deprecation warnings, many new tests have been introduced that are aliases of the old tests. These new tests make more sense grammatically with the jinja test syntax, such as the new ``successful`` test which aliases ``success``.

.. code-block:: yaml

    when: result is successful

See :ref:`playbooks_tests` for more information.

Additionally, a script was created to assist in the conversion for tests using filter syntax to proper jinja test syntax. This script has been used to convert all of the Ansible integration tests to the correct format. There are a few limitations documented, and all changes made by this script should be evaluated for correctness before executing the modified playbooks. The script can be found at `https://github.com/ansible/ansible/blob/devel/hacking/fix_test_syntax.py <https://github.com/ansible/ansible/blob/devel/hacking/fix_test_syntax.py>`_.

Modules
=======

Major changes in popular modules are detailed here.

github_release
--------------

In Ansible versions 2.4 and older, after creating a GitHub release using the ``create_release`` state, the ``github_release`` module reported state as ``skipped``.
In Ansible version 2.5 and later, after creating a GitHub release using the ``create_release`` state, the ``github_release`` module now reports state as ``changed``.


Modules removed
---------------

The following modules no longer exist:

* :ref:`nxos_mtu <nxos_mtu_module>` use :ref:`nxos_system <nxos_system_module>`'s ``system_mtu`` option or :ref:`nxos_interface <nxos_interface_module>` instead
* :ref:`cl_interface_policy <cl_interface_policy_module>` use :ref:`nclu <nclu_module>` instead
* :ref:`cl_bridge <cl_bridge_module>` use :ref:`nclu <nclu_module>` instead
* :ref:`cl_img_install <cl_img_install_module>` use :ref:`nclu <nclu_module>` instead
* :ref:`cl_ports <cl_ports_module>` use :ref:`nclu <nclu_module>` instead
* :ref:`cl_license <cl_license_module>` use :ref:`nclu <nclu_module>` instead
* :ref:`cl_interface <cl_interface_module>` use :ref:`nclu <nclu_module>` instead
* :ref:`cl_bond <cl_bond_module>` use :ref:`nclu <nclu_module>` instead
* :ref:`ec2_vpc <ec2_vpc_module>` use :ref:`ec2_vpc_net <ec2_vpc_net_module>` along with supporting modules :ref:`ec2_vpc_igw <ec2_vpc_igw_module>`, :ref:`ec2_vpc_route_table <ec2_vpc_route_table_module>`, :ref:`ec2_vpc_subnet <ec2_vpc_subnet_module>`, :ref:`ec2_vpc_dhcp_option <ec2_vpc_dhcp_option_module>`, :ref:`ec2_vpc_nat_gateway <ec2_vpc_nat_gateway_module>`, :ref:`ec2_vpc_nacl <ec2_vpc_nacl_module>` instead.
* :ref:`ec2_ami_search <ec2_ami_search_module>` use :ref:`ec2_ami_facts <ec2_ami_facts_module>` instead
* :ref:`docker <docker_module>` use :ref:`docker_container <docker_container_module>` and :ref:`docker_image <docker_image_module>` instead

Deprecation notices
-------------------

The following modules will be removed in Ansible 2.9. Please update your playbooks accordingly.

* Apstra's ``aos_*`` modules are deprecated as they do not work with AOS 2.1 or higher. See new modules at `https://github.com/apstra <https://github.com/apstra>`_.
* :ref:`nxos_ip_interface <nxos_ip_interface_module>` use :ref:`nxos_l3_interface <nxos_l3_interface_module>` instead.
* :ref:`nxos_portchannel <nxos_portchannel_module>` use :ref:`nxos_linkagg <nxos_linkagg_module>` instead.
* :ref:`nxos_switchport <nxos_switchport_module>` use :ref:`nxos_l2_interface <nxos_l2_interface_module>` instead.
* :ref:`panos_security_policy <panos_security_policy_module>` use :ref:`panos_security_rule <panos_security_rule_module>` instead.
* :ref:`panos_nat_policy <panos_nat_policy_module>` use :ref:`panos_nat_rule <panos_nat_rule_module>` instead.
* :ref:`vsphere_guest <vsphere_guest_module>` use :ref:`vmware_guest <vmware_guest_module>` instead.

Noteworthy module changes
-------------------------

* The :ref:`stat <stat_module>` and :ref:`win_stat <win_stat_module>` modules have changed the default of the option ``get_md5`` from ``true`` to ``false``.

This option will be removed starting with Ansible version 2.9. The options ``get_checksum: True``
and ``checksum_algorithm: md5`` can still be used if an MD5 checksum is
desired.

* ``osx_say`` module was renamed into :ref:`say <say_module>`.
* Several modules which could deal with symlinks had the default value of their ``follow`` option
  changed as part of a feature to `standardize the behavior of follow
  <https://github.com/ansible/proposals/issues/69>`_:

  * The :ref:`file module <file_module>` changed from ``follow=False`` to ``follow=True`` because
    its purpose is to modify the attributes of a file and most systems do not allow attributes to be
    applied to symlinks, only to real files.
  * The :ref:`replace module <replace_module>` had its ``follow`` parameter removed because it
    inherently modifies the content of an existing file so it makes no sense to operate on the link
    itself.
  * The :ref:`blockinfile module <blockinfile_module>` had its ``follow`` parameter removed because
    it inherently modifies the content of an existing file so it makes no sense to operate on the
    link itself.
  * In Ansible-2.5.3, the :ref:`template module <template_module>` became more strict about its
    ``src`` file being proper utf-8.  Previously, non-utf8 contents in a template module src file
    would result in a mangled output file (the non-utf8 characters would be replaced with a unicode
    replacement character).  Now, on Python2, the module will error out with the message, "Template
    source files must be utf-8 encoded".  On Python3, the module will first attempt to pass the
    non-utf8 characters through verbatim and fail if that does not succeed.

Plugins
=======

As a developer, you can now use 'doc fragments' for common configuration options on plugin types that support the new plugin configuration system.

Inventory
---------

Inventory plugins have been fine tuned, and we have started to add some common features:

* The ability to use a cache plugin to avoid costly API/DB queries is disabled by default.
  If using inventory scripts, some may already support a cache, but it is outside of Ansible's knowledge and control.
  Moving to the internal cache will allow you to use Ansible's existing cache refresh/invalidation mechanisms.

* A new 'auto' plugin, enabled by default, that can automatically detect the correct plugin to use IF that plugin is using our 'common YAML configuration format'.
  The previous host_list, script, yaml and ini plugins still work as they did, the auto plugin is now the last one we attempt to use.
  If you had customized the enabled plugins you should revise the setting to include the new auto plugin.

Shell
-----

Shell plugins have been migrated to the new plugin configuration framework. It is now possible to customize more settings, and settings which were previously 'global' can now also be overriden using host specific variables.

For example, ``system_temps`` is a new setting that allows you to control what Ansible will consider a 'system temporary dir'. This is used when escalating privileges for a non-administrative user. Previously this was hardcoded to '/tmp', which some systems cannot use for privilege escalation. This setting now defaults to ``[ '/var/tmp', '/tmp']``.

Another new setting is ``admin_users`` which allows you to specify a list of users to be considered 'administrators'. Previously this was hardcoded to ``root``. It now it defaults to ``[root, toor, admin]``.  This information is used when choosing between your ``remote_temp`` and ``system_temps`` directory.

For a full list, check the shell plugin you are using, the default shell plugin is ``sh``.

Those that had to work around the global configuration limitations can now migrate to a per host/group settings,
but also note that the new defaults might conflict with existing usage if the assumptions don't correlate to your environment.

Filter
------

The lookup plugin API now throws an error if a non-iterable value is returned from a plugin. Previously, numbers or
other non-iterable types returned by a plugin were accepted without error or warning. This change was made because plugins should always return a list. Please note that plugins that return strings and other non-list iterable values will not throw an error, but may cause unpredictable behavior. If you have a custom lookup plugin that does not return a list, you should modify it to wrap the return values in a list.

Lookup
-------

A new option was added to lookup plugins globally named ``error`` which allows you to control how errors produced by the lookup are handled, before this option they were always fatal. Valid values for this option are ``warn``, ``ignore`` and ``strict``. See the :doc:`lookup <../plugins/lookup>` page for more details.


Porting custom scripts
======================

No notable changes.

Network
=======

Expanding documentation
-----------------------

We're expanding the network documentation. There's new content and a :ref:`new Ansible Network landing page<network_guide>`. We will continue to build the network-related documentation moving forward.

Top-level connection arguments will be removed in 2.9
-----------------------------------------------------

Top-level connection arguments like ``username``, ``host``, and ``password`` are deprecated and will be removed in version 2.9.

**OLD** In Ansible < 2.4

.. code-block:: yaml

    - name: example of using top-level options for connection properties
      ios_command:
        commands: show version
        host: "{{ inventory_hostname }}"
        username: cisco
        password: cisco
        authorize: yes
        auth_pass: cisco

The deprecation warnings reflect this schedule. The task above, run in Ansible 2.5, will result in:

.. code-block:: yaml

   [DEPRECATION WARNING]: Param 'username' is deprecated. See the module docs for more information. This feature will be removed in version
   2.9. Deprecation warnings can be disabled by setting deprecation_warnings=False in ansible.cfg.
   [DEPRECATION WARNING]: Param 'password' is deprecated. See the module docs for more information. This feature will be removed in version
   2.9. Deprecation warnings can be disabled by setting deprecation_warnings=False in ansible.cfg.
   [DEPRECATION WARNING]: Param 'host' is deprecated. See the module docs for more information. This feature will be removed in version 2.9.
   Deprecation warnings can be disabled by setting deprecation_warnings=False in ansible.cfg.

We recommend using the new connection types ``network_cli`` and ``netconf`` (see below), using standard Ansible connection properties, and setting those properties in inventory by group. As you update your playbooks and inventory files, you can easily make the change to ``become`` for privilege escalation (on platforms that support it). For more information, see the :ref:`using become with network modules<become-network>` guide and the :ref:`platform documentation<platform_options>`.

Adding persistent connection types ``network_cli`` and ``netconf``
------------------------------------------------------------------

Ansible 2.5 introduces two top-level persistent connection types, ``network_cli`` and ``netconf``. With ``connection: local``, each task passed the connection parameters, which had to be stored in your playbooks. With ``network_cli`` and ``netconf`` the playbook passes the connection parameters once, so you can pass them at the command line if you prefer. We recommend you use ``network_cli`` and ``netconf`` whenever possible.
Note that eAPI and NX-API still require ``local`` connections with ``provider`` dictionaries. See the :ref:`platform documentation<platform_options>` for more information. Unless you need a ``local`` connection, update your playbooks to use ``network_cli`` or ``netconf`` and to specify your connection variables with standard Ansible connection variables:

**OLD** In Ansible 2.4

.. code-block:: yaml

   ---
   vars:
       cli:
          host: "{{ inventory_hostname }}"
          username: operator
          password: secret
          transport: cli

   tasks:
   - nxos_config:
       src: config.j2
       provider: "{{ cli }}"
       username: admin
       password: admin

**NEW** In Ansible 2.5

.. code-block:: ini

   [nxos:vars]
   ansible_connection=network_cli
   ansible_network_os=nxos
   ansible_user=operator
   ansible_password=secret

.. code-block:: yaml

   tasks:
   - nxos_config:
       src: config.j2

Using a provider dictionary with either ``network_cli`` or ``netconf`` will result in a warning.


Developers: Shared Module Utilities Moved
-----------------------------------------

Beginning with Ansible 2.5, shared module utilities for network modules moved to ``ansible.module_utils.network``.

* Platform-independent utilities are found in ``ansible.module_utils.network.common``

* Platform-specific utilities are found in ``ansible.module_utils.network.{{ platform }}``

If your module uses shared module utilities, you must update all references. For example, change:

**OLD** In Ansible 2.4

.. code-block:: python

   from ansible.module_utils.vyos import get_config, load_config

**NEW** In Ansible 2.5

.. code-block:: python

   from ansible.module_utils.network.vyos.vyos import get_config, load_config


See the module utilities developer guide see :ref:`appendix_module_utilities` for more information.

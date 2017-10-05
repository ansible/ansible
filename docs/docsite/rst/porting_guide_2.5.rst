.. _porting_2.5_guide:

*************************
Ansible 2.5 Porting Guide
*************************

This section discusses the behavioral changes between Ansible 2.4 and Ansible 2.5.

It is intended to assist in updating your playbooks, plugins and other parts of your Ansible infrastructure so they will work with this version of Ansible.

We suggest you read this page along with `Ansible Changelog <https://github.com/ansible/ansible/blob/devel/CHANGELOG.md#2.5>`_ to understand what updates you may need to make.

This document is part of a collection on porting. The complete list of porting guides can be found at :ref:`porting guides <porting_guides>`.

.. contents:: Topics

Playbook
========

No notable changes.

Deprecated
==========

No notable changes.

Modules
=======

Major changes in popular modules are detailed here

No notable changes.

Modules removed
---------------

The following modules no longer exist:

* None

Deprecation notices
-------------------

The following modules will be removed in Ansible 2.8. Please update update your playbooks accordingly.

* :ref:`fixme <fixme>`

Noteworthy module changes
-------------------------

No notable changes.

Plugins
=======

No notable changes.

Porting custom scripts
======================

No notable changes.

Networking
==========


Change in deprecation notice of top-level connection arguments
--------------------------------------------------------------
.. code-block:: yaml

    - name: example of using top-level options for connection properties
      ios_command:
        commands: show version
        host: "{{ inventory_hostname }}"
        username: cisco
        password: cisco
        authorize: yes
        auth_pass: cisco

**OLD** In Ansible 2.4:

Will result in:

.. code-block:: yaml

   [WARNING]: argument username has been deprecated and will be removed in a future version
   [WARNING]: argument host has been deprecated and will be removed in a future version
   [WARNING]: argument password has been deprecated and will be removed in a future version


**NEW** In Ansible 2.5:


.. code-block:: yaml

   [DEPRECATION WARNING]: Param 'username' is deprecated. See the module docs for more information. This feature will be removed in version
   2.9. Deprecation warnings can be disabled by setting deprecation_warnings=False in ansible.cfg.
   [DEPRECATION WARNING]: Param 'password' is deprecated. See the module docs for more information. This feature will be removed in version
   2.9. Deprecation warnings can be disabled by setting deprecation_warnings=False in ansible.cfg.
   [DEPRECATION WARNING]: Param 'host' is deprecated. See the module docs for more information. This feature will be removed in version 2.9.
   Deprecation warnings can be disabled by setting deprecation_warnings=False in ansible.cfg.


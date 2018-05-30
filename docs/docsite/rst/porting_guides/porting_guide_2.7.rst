.. _porting_2.7_guide:

*************************
Ansible 2.7 Porting Guide
*************************

This section discusses the behavioral changes between Ansible 2.6 and Ansible 2.7.

It is intended to assist in updating your playbooks, plugins and other parts of your Ansible infrastructure so they will work with this version of Ansible.

We suggest you read this page along with `Ansible Changelog <https://github.com/ansible/ansible/blob/devel/CHANGELOG.md#2.7>`_ to understand what updates you may need to make.

This document is part of a collection on porting. The complete list of porting guides can be found at :ref:`porting guides <porting_guides>`.

.. contents:: Topics

Playbook
========

No notable changes.

Deprecated
==========

Using a loop on a package module via squash_actions
---------------------------------------------------

The use of ``squash_actions`` to invoke a package module, such as "yum", to only invoke the module once is deprecated, and will be removed in Ansible 2.11.

Instead of relying on implicit squashing, tasks should instead supply the list directly to the ``name``, ``pkg`` or ``package`` parameter of the module. This functionality has been supported in most modules since Ansible 2.3.

**OLD** In Ansible 2.6 (and earlier) the following task would invoke the "yum" module only 1 time to install multiple packages

.. code-block:: yaml

    - name: Install packages
      yum:
        name: "{{ item }}"
        state: present
      with_items: "{{ packages }}"

**NEW** In Ansible 2.7 it should be changed to look like this:

.. code-block:: yaml

    - name: Install packages
      yum:
        name: "{{ packages }}"
        state: present


Modules
=======

Major changes in popular modules are detailed here



Modules removed
---------------

The following modules no longer exist:


Deprecation notices
-------------------

The following modules will be removed in Ansible 2.10. Please update your playbooks accordingly.


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

No notable changes.

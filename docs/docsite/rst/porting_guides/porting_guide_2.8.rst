.. _porting_2.8_guide:

*************************
Ansible 2.8 Porting Guide
*************************

This section discusses the behavioral changes between Ansible 2.7 and Ansible 2.8.

It is intended to assist in updating your playbooks, plugins and other parts of your Ansible infrastructure so they will work with this version of Ansible.

We suggest you read this page along with `Ansible Changelog for 2.8 <https://github.com/ansible/ansible/blob/devel/changelogs/CHANGELOG-v2.8.rst>`_ to understand what updates you may need to make.

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


Modules removed
---------------

The following modules no longer exist:

* ec2_remote_facts
* azure
* cs_nic
* netscaler
* win_msi

Deprecation notices
-------------------

The following modules will be removed in Ansible 2.12. Please update your playbooks accordingly.


Noteworthy module changes
-------------------------

* The ``tower_credential`` module originally required the ``ssh_key_data`` to be the path to a ssh_key_file.
  In order to work like Tower/AWX, ``ssh_key_data`` now contains the content of the file.
  The previous behavior can be achieved with ``lookup('file', '/path/to/file')``.

Plugins
=======

No notable changes.

Porting custom scripts
======================

No notable changes.

Networking
==========

No notable changes.

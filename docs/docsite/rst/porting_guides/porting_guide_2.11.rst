
.. _porting_2.11_guide:

**************************
Ansible 2.11 Porting Guide
**************************

This section discusses the behavioral changes between Ansible 2.10 and Ansible 2.11.

It is intended to assist in updating your playbooks, plugins and other parts of your Ansible infrastructure so they will work with this version of Ansible.

We suggest you read this page along with `Ansible Changelog for 2.11 <https://github.com/ansible/ansible/blob/devel/changelogs/CHANGELOG-v2.11.rst>`_ to understand what updates you may need to make.

This document is part of a collection on porting. The complete list of porting guides can be found at :ref:`porting guides <porting_guides>`.

.. contents:: Topics


Playbook
========

No notable changes


Command Line
============

No notable changes


Deprecated
==========

No notable changes


Modules
=======

Change to Default File Permissions
----------------------------------

To address CVE-2020-1736, the default permissions for certain files created by Ansible using ``atomic_move()`` were changed from ``0o666`` to ``0o600``. The default permissions value was only used for the temporary file before it was moved into its place or newly created files. If the file existed when the new temporary file was moved into place, Ansible would use the permissions of the existing file. If there was no existing file, Ansible would retain the default file permissions, combined with the system ``umask``, of the temporary file.

Most modules that call ``atomic_move()`` also call ``set_fs_attributes_if_different()``, which will set the permissions of the file to what is specified in the task.

A new warning will be displayed when all of the following conditions are true:

    - The file at the final destination, not the temporary file, does not exist
    - A module supports setting ``mode`` but it was not specified for the task
    - The module calls ``atomic_move()`` but does not later call ``set_fs_attributes_if_different()``

The following modules call ``atomic_move()`` but do not call ``set_fs_attributes_if_different()`` and do not support setting ``mode``. This means for files they create, the default permissions have changed and there is no indication:

    - [insert modules here]

* The ``apt_key`` module has explicitly defined ``file`` as mutually exclusive with ``data``, ``keyserver`` and ``url``. They cannot be used together anymore.

Modules removed
---------------

The following modules no longer exist:

* No notable changes


Deprecation notices
-------------------

No notable changes


Noteworthy module changes
-------------------------

* facts - ``ansible_virtualization_type`` now tries to report a more accurate result than ``xen`` when virtualized and not running on Xen.


Plugins
=======

No notable changes


Porting custom scripts
======================

No notable changes


Networking
==========

No notable changes

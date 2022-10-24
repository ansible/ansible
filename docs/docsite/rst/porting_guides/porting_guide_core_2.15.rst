
.. _porting_2.15_guide_core:

*******************************
Ansible-core 2.15 Porting Guide
*******************************

This section discusses the behavioral changes between ``ansible-core`` 2.14 and ``ansible-core`` 2.15.

It is intended to assist in updating your playbooks, plugins and other parts of your Ansible infrastructure so they will work with this version of Ansible.

We suggest you read this page along with `ansible-core Changelog for 2.15 <https://github.com/ansible/ansible/blob/stable-2.15/changelogs/CHANGELOG-v2.15.rst>`_ to understand what updates you may need to make.

This document is part of a collection on porting. The complete list of porting guides can be found at :ref:`porting guides <porting_guides>`.

.. contents:: Topics


Playbook
========

No notable changes


Command Line
============

* The return code of ``ansible-galaxy search`` is now 0 instead of 1 when results are empty to align with other ``ansible-galaxy`` commands.


Deprecated
==========

* Providing a list of dictionaries to ``vars:`` is deprecated in favor of supplying a dictionary.

  Instead of:

  .. code-block:: yaml

     vars:
       - var1: foo
       - var2: bar

  Use:

  .. code-block:: yaml

     vars:
       var1: foo
       var2: bar

Modules
=======

No notable changes


Modules removed
---------------

The following modules no longer exist:

* No notable changes


Deprecation notices
-------------------

No notable changes


Noteworthy module changes
-------------------------

No notable changes


Plugins
=======

No notable changes


Porting custom scripts
======================

No notable changes


Networking
==========

No notable changes

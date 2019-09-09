
.. _porting_2.10_guide:

**************************
Ansible 2.10 Porting Guide
**************************

This section discusses the behavioral changes between Ansible 2.9 and Ansible 2.10.

It is intended to assist in updating your playbooks, plugins and other parts of your Ansible infrastructure so they will work with this version of Ansible.

We suggest you read this page along with `Ansible Changelog for 2.10 <https://github.com/ansible/ansible/blob/devel/changelogs/CHANGELOG-v2.10.rst>`_ to understand what updates you may need to make.

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

httpapi Plugins Migrated to Collections
---------------------------------------
* ``splunk`` is now part of the upstream Collection `splunk.enterprise_security
  <https://github.com/ansible-security/splunk_enterprise_security>`_, please use
  as provided by the Collection.
* ``qradar`` is now part of the upstream Collection `ibm.qradar
  <https://github.com/ansible-security/ibm_qradar>`_, please use as provided
  by the Collection.



Porting custom scripts
======================

No notable changes


Networking
==========

No notable changes

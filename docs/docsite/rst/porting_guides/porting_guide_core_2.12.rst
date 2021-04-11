
.. _porting_2.12_guide:

**************************
Ansible 2.12 Porting Guide
**************************

This section discusses the behavioral changes between Ansible 2.11 and Ansible 2.12.

It is intended to assist in updating your playbooks, plugins and other parts of your Ansible infrastructure so they will work with this version of Ansible.

We suggest you read this page along with `Ansible Changelog for 2.12 <https://github.com/ansible/ansible/blob/devel/changelogs/CHANGELOG-v2.12.rst>`_ to understand what updates you may need to make.

This document is part of a collection on porting. The complete list of porting guides can be found at :ref:`porting guides <porting_guides>`.

.. contents:: Topics


Playbook
========

* When calling tasks and setting ``async``, setting ``ANSIBLE_ASYNC_DIR`` under ``environment:`` is no longer valid. Instead, use the shell configuration variable ``async_dir``, for example by setting ``ansible_async_dir``:

.. code-block:: yaml

   tasks:
     - dnf:
         name: '*'
         state: latest
       async: 300
       poll: 5
       vars:
         ansible_async_dir: /path/to/my/custom/dir

Command Line
============

No notable changes


Deprecated
==========

No notable changes


Modules
=======

* ``cron`` now requires ``name`` to be specified in all cases.
* ``cron`` no longer allows a ``reboot`` parameter. Use ``special_time: reboot`` instead.


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

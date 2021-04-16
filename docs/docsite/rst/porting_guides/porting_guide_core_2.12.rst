
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

No notable changes


Command Line
============

No notable changes


Deprecated
==========

* Python 2.6 on the target node is deprecated in this release. ``ansible-core`` 2.13 will remove support for Python 2.6.
* Bare variables in conditionals: ``when`` conditionals no longer automatically parse string booleans such as ``"true"`` and ``"false"`` into actual booleans. Any variable containing a non-empty string is considered true. This was previously configurable with the ``CONDITIONAL_BARE_VARS`` configuration option (and the ``ANSIBLE_CONDITIONAL_BARE_VARS`` environment variable). This setting no longer has any effect. Users can work around the issue by using the ``|bool`` filter:

.. code-block:: yaml

    vars:
      teardown: 'false'

    tasks:
      - include_tasks: teardown.yml
        when: teardown | bool

      - include_tasks: provision.yml
        when: not teardown | bool


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

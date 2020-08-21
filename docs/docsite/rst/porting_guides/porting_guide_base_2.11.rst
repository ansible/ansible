
.. _porting_2.11_guide_base:

*******************************
Ansible-base 2.11 Porting Guide
*******************************

This section discusses the behavioral changes between Ansible-base 2.10 and Ansible-base 2.11.

It is intended to assist in updating your playbooks, plugins and other parts of your Ansible infrastructure so they will work with this version of Ansible-base.

We suggest you read this page along with the `Ansible-base Changelog for 2.11 <https://github.com/ansible/ansible/blob/stable-2.11/changelogs/CHANGELOG-v2.11.rst>`_ to understand what updates you may need to make.

Ansible-base is mainly of interest for developers and users who only want to use a small, controlled subset of the available collections. Regular users should install ansible.

The complete list of porting guides can be found at :ref:`porting guides <porting_guides>`.

.. contents::

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

* The ``apt_key`` module has explicitly defined ``file`` as mutually exclusive with ``data``, ``keyserver`` and ``url``. They cannot be used together anymore.
* The ``meta`` module now supports tags for user-defined tasks. Set the task's tags to 'always' to maintain the previous behavior. Internal ``meta`` tasks continue to always run.


Modules removed
---------------

The following modules no longer exist:

* No notable changes


Deprecation notices
-------------------

No notable changes


Noteworthy module changes
-------------------------

* facts - On NetBSD, ``ansible_virtualization_type`` now tries to report a more accurate result than ``xen`` when virtualized and not running on Xen.
* facts - Virtualization facts now include ``virtualization_tech_guest`` and ``virtualization_tech_host`` keys. These are lists of virtualization technologies that a guest is a part of, or that a host provides, respectively. As an example, a host may be set up to provide both KVM and VirtualBox, and these will be included in ``virtualization_tech_host``, and a podman container running on a VM powered by KVM will have a ``virtualization_tech_guest`` of ``["kvm", "podman", "container"]``.


Plugins
=======

* inventory plugins - ``CachePluginAdjudicator.flush()`` now calls the underlying cache plugin's ``flush()`` instead of only deleting keys that it knows about. Inventory plugins should use ``delete()`` to remove any specific keys. As a user, this means that when an inventory plugin calls its ``clear_cache()`` method, facts could also be flushed from the cache. To work around this, users can configure inventory plugins to use a cache backend that is independent of the facts cache.
* callback plugins - ``meta`` task execution is now sent to ``v2_playbook_on_task_start`` like any other task. By default, only explicit meta tasks are sent there. Callback plugins can opt-in to receiving internal, implicitly created tasks to act on those as well, as noted in the plugin development documentation.

Porting custom scripts
======================

No notable changes

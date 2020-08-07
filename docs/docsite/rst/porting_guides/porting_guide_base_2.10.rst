
.. _porting_2.10_guide_base:

*******************************
Ansible-base 2.10 Porting Guide
*******************************

.. warning::

	In preparation for the release of 2.10, many plugins and modules have migrated to Collections on  `Ansible Galaxy <https://galaxy.ansible.com>`_. For the current development status of Collections and FAQ see `Ansible Collections Community Guide <https://github.com/ansible-collections/overview/blob/master/README.rst>`_. We expect the 2.10 Porting Guide to change frequently up to the 2.10 release. Follow the conversations about collections on our various :ref:`communication` channels for the latest information on the status of the ``devel`` branch.

This section discusses the behavioral changes between Ansible 2.9 and Ansible-base 2.10.

It is intended to assist in updating your playbooks, plugins and other parts of your Ansible infrastructure so they will work with this version of Ansible-base.

We suggest you read this page along with the `Ansible-base Changelog for 2.10 <https://github.com/ansible/ansible/blob/stable-2.10/changelogs/CHANGELOG-v2.10.rst>`_ to understand what updates you may need to make.

Ansible-base is mainly of interest for developers and users who only want to use a small, controlled subset of the available collections. Regular users should install ansible.

The complete list of porting guides can be found at :ref:`porting guides <porting_guides>`.

.. contents::


Playbook
========

* Fixed a bug on boolean keywords that made random strings return 'False', now they should return an error if they are not a proper boolean
  Example: `diff: yes-` was returning `False`.
* A new fact, ``ansible_processor_nproc`` reflects the number of vcpus
  available to processes (falls back to the number of vcpus available to
  the scheduler).


Command Line
============

No notable changes


Deprecated
==========

* Windows Server 2008 and 2008 R2 will no longer be supported or tested in the next Ansible release, see :ref:`windows_faq_server2008`.


Modules
=======

.. warning::

	Links on this page may not point to the most recent versions of modules. We will update them when we can.


Noteworthy module changes
-------------------------

* Ansible modules created with ``add_file_common_args=True`` added a number of undocumented arguments which were mostly there to ease implementing certain action plugins. The undocumented arguments ``src``, ``follow``, ``force``, ``content``, ``backup``, ``remote_src``, ``regexp``, ``delimiter``, and ``directory_mode`` are now no longer added. Modules relying on these options to be added need to specify them by themselves.
* Ansible no longer looks for Python modules in the current working directory (typically the ``remote_user``'s home directory) when an Ansible module is run. This is to fix becoming an unprivileged user on OpenBSD and to mitigate any attack vector if the current working directory is writable by a malicious user. Install any Python modules needed to run the Ansible modules on the managed node in a system-wide location or in another directory which is in the ``remote_user``'s ``$PYTHONPATH`` and readable by the ``become_user``.


Plugins
=======

Lookup plugin names case-sensitivity
------------------------------------

* Prior to Ansible ``2.10`` lookup plugin names passed in as an argument to the ``lookup()`` function were treated as case-insensitive as opposed to lookups invoked via ``with_<lookup_name>``. ``2.10`` brings consistency to ``lookup()`` and ``with_`` to be both case-sensitive.

Noteworthy plugin changes
-------------------------

* Cache plugins in collections can be used to cache data from inventory plugins. Previously, cache plugins in collections could only be used for fact caching.
* Some undocumented arguments from ``FILE_COMMON_ARGUMENTS`` have been removed; plugins using these, in particular action plugins, need to be adjusted. The undocumented arguments which were removed are ``src``, ``follow``, ``force``, ``content``, ``backup``, ``remote_src``, ``regexp``, ``delimiter``, and ``directory_mode``.

Action plugins which execute modules should use fully-qualified module names
----------------------------------------------------------------------------

* Action plugins that call modules should pass explicit, fully-qualified module names to ``_execute_module()`` whenever possible (eg, ``ansible.builtin.file`` rather than ``file``). This ensures that the task's collection search order is not consulted to resolve the module. Otherwise, a module from a collection earlier in the search path could be used when not intended.

Porting custom scripts
======================

No notable changes

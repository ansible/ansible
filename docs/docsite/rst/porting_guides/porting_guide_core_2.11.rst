
.. _porting_2.11_guide_core:

*******************************
Ansible-core 2.11 Porting Guide
*******************************

This section discusses the behavioral changes between ``ansible-base`` 2.10 and ``ansible-core`` 2.11.

It is intended to assist in updating your playbooks, plugins and other parts of your Ansible infrastructure so they will work with this version of ``ansible-core``.

We suggest you read this page along with the `ansible-core Changelog for 2.11 <https://github.com/ansible/ansible/blob/devel/changelogs/CHANGELOG-v2.11.rst>`_ to understand what updates you may need to make.

``ansible-core`` is mainly of interest for developers and users who only want to use a small, controlled subset of the available collections. Regular users should install Ansible.

The complete list of porting guides can be found at :ref:`porting guides <porting_guides>`.

.. contents::

Playbook
========

* The ``jinja2_native`` setting now does not affect the template module which implicitly returns strings. For the template lookup there is a new argument ``jinja2_native`` (off by default) to control that functionality. The rest of the Jinja2 expressions still operate based on the ``jinja2_native`` setting.


Command Line
============

* The ``ansible-galaxy login`` command has been removed, as the underlying API it used for GitHub auth is being shut down. Publishing roles or
  collections to Galaxy via ``ansible-galaxy`` now requires that a Galaxy API token be passed to the CLI via a token file (default location
  ``~/.ansible/galaxy_token``) or (insecurely) via the ``--token`` argument to ``ansible-galaxy``.


Other:
======

* **Upgrading**: If upgrading from ``ansible < 2.10`` or from ``ansible-base`` and using pip, you will need to ``pip uninstall ansible`` or ``pip uninstall ansible-base`` before installing ``ansible-core`` to avoid conflicts.
* Python 3.8 on the controller node is a soft requirement for this release. ``ansible-core`` 2.11 will continue to work with the same versions of Python that ``ansible-base`` 2.10 worked with, however it will emit a warning when running on a controller node with a Python version less than 3.8. This warning can be disabled by setting ``ANSIBLE_CONTROLLER_PYTHON_WARNING=False`` in your environment. ``ansible-core`` 2.12 will require Python 3.8 or greater.
* The configuration system now validates the ``choices`` field, so any settings that currently violate it and are currently ignored will now cause an error.
  For example, `ANSIBLE_COLLECTIONS_ON_ANSIBLE_VERSION_MISMATCH=0` will now cause an error (valid choices are 'ignore', 'warn' or 'error').
* The ``ansible-galaxy`` command now uses ``resolvelib`` for resolving dependencies. In most cases this should not make a user-facing difference beyond being more performant, but we note it here for posterity and completeness.
* Python ``module_utils`` imports may now be marked as optional during the module payload build by wrapping the ``import`` statement in a ``try`` or ``if`` block. This allows modules to use ``module_utils`` that may not be present in all versions of Ansible or a collection, and to perform arbitrary recovery or fallback actions during module runtime.


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
* The parameter ``filter`` type is changed from ``string`` to ``list`` in the :ref:`setup <setup_module>` module in order to use more than one filter. Previous behaviour (using a ``string``) still remains and works as a single filter.


Plugins
=======

* inventory plugins - ``CachePluginAdjudicator.flush()`` now calls the underlying cache plugin's ``flush()`` instead of only deleting keys that it knows about. Inventory plugins should use ``delete()`` to remove any specific keys. As a user, this means that when an inventory plugin calls its ``clear_cache()`` method, facts could also be flushed from the cache. To work around this, users can configure inventory plugins to use a cache backend that is independent of the facts cache.
* callback plugins - ``meta`` task execution is now sent to ``v2_playbook_on_task_start`` like any other task. By default, only explicit meta tasks are sent there. Callback plugins can opt-in to receiving internal, implicitly created tasks to act on those as well, as noted in the plugin development documentation.
* The ``choices`` are now validated, so plugins that were using incorrect or incomplete choices will now issue an error if the value provided does not match. This has a simple fix: update the entries in ``choices`` to match reality.

Porting custom scripts
======================

No notable changes

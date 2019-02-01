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

Distribution Facts
------------------

The information returned for the ``ansible_distribution_*`` group of facts may have changed
slightly.  Ansible 2.8 uses a new backend library for information about distributions: `nir0s/distro <https://github.com/nir0s/distro>`_. This library runs on Python-3.8 and fixes many bugs, including correcting release and version names.

The two facts used in playbooks most often, ``ansible_distribution`` and ``ansible_distribution_major_version``, should not change. If you discover a change in these facts, please file a bug so we can address the
difference.  However, other facts like ``ansible_distribution_release`` and
``ansible_distribution_version`` may change as erroneous information gets corrected.

Imports as handlers
-------------------

Beginning in version 2.8, a task cannot notify ``import_tasks`` or a static ``include`` that is specified in ``handlers``.

The goal of a static import is to act as a pre-processor, where the import is replaced by the tasks defined within the imported file. When
using an import, a task can notify any of the named tasks within the imported file, but not the name of the import itself.

To achieve the results of notifying a single name but running mulitple handlers, utilize ``include_tasks``, or ``listen`` :ref:`handlers`.

Command Line
============

Become Prompting
----------------

Beginning in version 2.8, by default Ansible will use the word ``BECOME`` to prompt you for a password for elevated privileges (``sudo`` privileges on unix systems or ``enable`` mode on network devices):

By default in Ansible 2.8::

    ansible-playbook --become --ask-become-pass site.yml
    BECOME password:

If you want the prompt to display the specific ``become_method`` you're using, instead of the agnostic value ``BECOME``, set :ref:`AGNOSTIC_BECOME_PROMPT` to ``False`` in your Ansible configuration.

By default in Ansible 2.7, or with ``AGNOSTIC_BECOME_PROMPT=False`` in Ansible 2.8::

    ansible-playbook --become --ask-become-pass site.yml
    SUDO password:

Deprecated
==========

* Setting the async directory using ``ANSIBLE_ASYNC_DIR`` as an task/play environment key is deprecated and will be
  removed in Ansible 2.12. You can achieve the same result by setting ``ansible_async_dir`` as a variable like::

      - name: run task with custom async directory
        command: sleep 5
        async: 10
        vars:
          ansible_aync_dir: /tmp/.ansible_async

* Plugin writers who need a ``FactCache`` object should be aware of two deprecations:

  1. The ``FactCache`` class has moved from ``ansible.plugins.cache.FactCache`` to
     ``ansible.vars.fact_cache.FactCache``.  This is because the ``FactCache`` is not part of the
     cache plugin API and cache plugin authors should not be subclassing it.  ``FactCache`` is still
     available from its old location but will issue a deprecation warning when used from there.  The
     old location will be removed in Ansible 2.12.

  2. The ``FactCache.update()`` method has been converted to follow the dict API.  It now takes a
     dictionary as its sole argument and updates itself with the dictionary's items.  The previous
     API where ``update()`` took a key and a value will now issue a deprecation warning and will be
     removed in 2.12.  If you need the old behaviour switch to ``FactCache.first_order_merge()``
     instead.

Modules
=======

Major changes in popular modules are detailed here

The exec wrapper that runs PowerShell modules has been changed to set ``$ErrorActionPreference = "Stop"`` globally.
This may mean that custom modules can fail if they implicitly relied on this behaviour. To get the old behaviour back,
add ``$ErrorActionPreference = "Continue"`` to the top of the module. This change was made to restore the old behaviour
of the EAP that was accidentally removed in a previous release and ensure that modules are more resiliant to errors
that may occur in execution.


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

* ``foreman`` use <https://github.com/theforeman/foreman-ansible-modules> instead.
* ``katello`` use <https://github.com/theforeman/foreman-ansible-modules> instead.
* ``github_hooks`` use :ref:`github_webhook <github_webhook_module>` and :ref:`github_webhook_facts <github_webhook_facts_module>` instead.
* ``digital_ocean`` use :ref `digital_ocean_droplet <digital_ocean_droplet_module>` instead.


Noteworthy module changes
-------------------------

* The ``foreman`` and ``katello`` modules have been deprecated in favor of a set of modules that are broken out per entity with better idempotency in mind.
* The ``foreman`` and ``katello`` modules replacement is officially part of the Foreman Community and supported there.
* The ``tower_credential`` module originally required the ``ssh_key_data`` to be the path to a ssh_key_file.
  In order to work like Tower/AWX, ``ssh_key_data`` now contains the content of the file.
  The previous behavior can be achieved with ``lookup('file', '/path/to/file')``.
* The ``win_scheduled_task`` module deprecated support for specifying a trigger repetition as a list and this format
  will be removed in Ansible 2.12. Instead specify the repetition as a dictionary value.

* The ``win_feature`` module has removed the deprecated ``restart_needed`` return value, use the standardised
  ``reboot_required`` value instead.

* The ``win_package`` module has removed the deprecated ``restart_required`` and ``exit_code`` return value, use the
  standardised ``reboot_required`` and ``rc`` value instead.

* The ``win_get_url`` module has removed the deprecated ``win_get_url`` return dictionary, contained values are
  returned directly.

* The ``win_get_url`` module has removed the deprecated ``skip_certificate_validation`` option, use the standardised
  ``validate_certs`` option instead.

* The ``vmware_local_role_facts`` module now returns a list of dicts instead of a dict of dicts for role information.

* If ``docker_network`` or ``docker_volume`` were called with ``diff: yes``, ``check_mode: yes`` or ``debug: yes``,
  a return value called ``diff`` was returned of type ``list``. To enable proper diff output, this was changed to
  type ``dict``; the original ``list`` is returned as ``diff.differences``.

* The ``na_ontap_cluster_peer`` module has replaced ``source_intercluster_lif`` and ``dest_intercluster_lif`` string options with
  ``source_intercluster_lifs`` and ``dest_intercluster_lifs`` list options

* The ``modprobe`` module now detects kernel builtins. Previously, attempting to remove (with ``state: absent``)
  a builtin kernel module succeeded without any error message because ``modprobe`` did not detect the module as
  ``present``. Now, ``modprobe`` will fail if a kernel module is builtin and ``state: absent`` (with an error message
  from the modprobe binary like ``modprobe: ERROR: Module nfs is builtin.``), and it will succeed without reporting
  changed if ``state: present``. Any playbooks that are using ``changed_when: no`` to mask this quirk can safely
  remove that workaround. To get the previous behavior when applying ``state: absent`` to a builtin kernel module,
  use ``failed_when: false`` or ``ignore_errors: true`` in your playbook.

* The ``digital_ocean`` module has been deprecated in favor of modules that do not require external dependencies.
  This allows for more flexibility and better module support.

* The ``docker_service`` module was renamed to :ref:`docker_compose <docker_compose_module>`.

* The ``docker_swarm_service`` module no longer sets a default for the ``user`` option. Before, the default was ``root``.

Plugins
=======

* The ``powershell`` shell plugin now uses ``async_dir`` to define the async path for the results file and the default
  has changed to ``%USERPROFILE%\.ansible_async``. To control this path now, either set the ``ansible_async_dir``
  variable or the ``async_dir`` value in the ``powershell`` section of the config ini.

* Order of enabled inventory plugins (:ref:`INVENTORY_ENABLED`) has been updated, :ref:`auto <auto_inventory>` is now before :ref:`yaml <yaml_inventory>` and :ref:`ini <ini_inventory>`.

* The private ``_options`` attribute has been removed from the ``CallbackBase`` class of callback
  plugins.  If you have a third-party callback plugin which needs to access the command line arguments,
  use code like the following instead of trying to use ``self._options``:

  .. code-block:: python

     from ansible import context
     [...]
     tags = context.CLIARGS['tags']

  ``context.CLIARGS`` is a read-only dictionary so normal dictionary retrieval methods like
  ``CLIARGS.get('tags')`` and ``CLIARGS['tags']`` work as expected but you won't be able to modify
  the cli arguments at all.


Porting custom scripts
======================

Display class
-------------

As of Ansible 2.8, the ``Display`` class is now a "singleton". Instead of using ``__main__.display`` each file should
import and instantiate ``ansible.utils.display.Display`` on its own.

**OLD** In Ansible 2.7 (and earlier) the following was used to access the ``display`` object:

.. code-block:: python

   try:
       from __main__ import display
   except ImportError:
       from ansible.utils.display import Display
       display = Display()

**NEW** In Ansible 2.8 the following should be used:

.. code-block:: python

   from ansible.utils.display import Display
   display = Display()

Networking
==========

* The ``eos_config``, ``ios_config``, and ``nxos_config`` modules have removed the deprecated
  ``save`` and ``force`` parameters, use the ``save_when`` parameter to replicate their
  functionality.

* The ``nxos_vrf_af`` module has removed the ``safi`` paramter. This parameter was deprecated
  in Ansible 2.4 and has had no impact on the module since then.

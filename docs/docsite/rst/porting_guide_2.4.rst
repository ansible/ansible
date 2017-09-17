.. _porting_2.4_guide:

*************************
Ansible 2.4 Porting Guide
*************************

This section discusses the behavioral changes between Ansible 2.3 and Ansible 2.4.

It is intended to assist in updating your playbooks, plugins and other parts of your Ansible infrastructure so they will work with this version of Ansible.


We suggest you read this page along with `Ansible Changelog <https://github.com/ansible/ansible/blob/stable-2.4/CHANGELOG.md#2.4>`_ to understand what updates you may need to make.

This document is part of a collection on porting. The complete list of porting guides can be found at :ref:`porting guides <porting_guides>`.

.. contents:: Topics

Python version
==============

Ansible will not support Python 2.4 nor 2.5 on the target hosts anymore. Going forward, Python 2.6+ will be required on targets, as already is the case on the controller.

Deprecated
==========

Specifying Inventory sources
-----------------------------

Use of ``--inventory-file`` on the command line is now deprecated. Use ``--inventory`` or ``-i``.
The associated ini configuration key, ``hostfile``, and environment variable, :envvar:`ANSIBLE_HOSTS`,
are also deprecated.  Replace them with the configuration key ``inventory`` and environment variable :envvar:        `ANSIBLE_INVENTORY`.

Use of multiple tags
--------------------

Specifying ``--tags`` (or ``--skip-tags``) multiple times on the command line currently leads to the last one overriding all the previous ones. This behavior is deprecated. In the future, if you specify --tags multiple times the tags will be merged together. From now on, using ``--tags`` multiple times on one command line will emit a deprecation warning. Setting the ``merge_multiple_cli_tags`` option to True in the ``ansible.cfg`` file will enable the new behavior.

In 2.4, the default has change to merge the tags. You can enable the old overwriting behavior via the config option.

In 2.5, multiple ``--tags`` options will be merged with no way to go back to the old behavior.


Other caveats
-------------

No major changes in this version.

Modules
=======

Major changes in popular modules are detailed here

* The :ref:`win_shell <win_shell>` and :ref:`win_command <win_command>` modules now properly preserve quoted arguments in the command-line. Tasks that attempted to work around the issue by adding extra quotes/escaping may need to be reworked to remove the superfluous escaping. See `Issue 23019 <https://github.com/ansible/ansible/issues/23019>`_ for additional detail.

Modules removed
---------------

The following modules no longer exist:

* None

Deprecation notices
-------------------

The following modules will be removed in Ansible 2.8. Please update update your playbooks accordingly.

* :ref:`azure <azure>`, use :ref:`azure_rm_virtualmachine <azure_rm_virtualmachine>`, which uses the new Resource Manager SDK.
* :ref:`win_msi <win_msi>`, use :ref:`win_package <win_package>` instead

Noteworthy module changes
-------------------------

* The :ref:`win_get_url <win_get_url>`  module has the dictionary ``win_get_url`` in its results deprecated, its content is now also available directly in the resulting output, like other modules. This dictionary will be removed in Ansible 2.8.
* The :ref:`win_unzip <win_unzip>` module no longer includes the dictionary ``win_unzip`` in its results; the contents are now included directly in the resulting output, like other modules.
* The :ref:`win_package <win_package>` module return values ``exit_code`` and ``restart_required`` have been deprecated in favour of ``rc`` and ``reboot_required`` respectively. The deprecated return values will be removed in Ansible 2.6.


Plugins
=======

A new way to configure and document plugins has been introduced.  This does not require changes to existing setups   but developers might want to start adapting to the new infrastructure now. More details should be available in the   developer documentation for each plugin type.

Vars plugin changes
-------------------

There have been many changes to the implementation of vars plugins, but both users and developers should not need to change anything to keep current setups working. Developers might WANT to change their plugins take advantage of new  features.

The most notable difference to users is that vars plugins now get invoked on demand instead of at inventory build    time.  This should make them more efficient for large inventories, especially when using a subset of the hosts.

Inventory plugins
-----------------

Developers might want to start migrating from hardcoded inventory with dynamic inventory scripts to the new          Inventory Plugins. The scripts will still work via the ``script`` inventory plugin but efforts will now concentrate  on writing plugins rather than enhancing existing scripts.

Both users and developers might want to look into the new plugins as we hope they alleviate the need for many of the hacks and workarounds found i nthe dynamic inventory scripts.


Networking
==========

There have been a number of changes to how Networking Modules operate.

Playbooks should still use ``connection: local``.

Persistent Connection
---------------------

The configuration variables ``connection_retries`` and ``connect_interval`` which were added in Ansible 2.3 are now deprecated. For Ansible 2.4 and later use ``connection_retry_timeout``.

To control timeouts use ``command_timeout`` rather than the previous top level ``timeout`` variable under ``[default]``

See :ref:`Ansible Network debug guide <network_debug_troubleshooting>` for more information.


Configuration API
=================

The configuration system has had some major changes, but users should be unaffected.  Developers that were poking    directly into the previous API might need to revisit their usage as some methods (for example, ``get_config``) were  kept for backwards compatibility but will warn users that the function has been deprecated.

The new configuration has been designed to minimize the need for code changes in core for new plugins.  The plugins  should just need to document their settings and the configuration system will use the documentation to provide what  they need. This is still a work in progress, currently only 'callback' and 'connection' plugins support this.  More  details will be added to the specific plugin developer guides.

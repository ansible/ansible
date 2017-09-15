.. _porting_2.4_guide:

*************************
Ansible 2.4 Porting Guide
*************************

This section discusses the behavioral changes between Ansible 2.3 and Ansible 2.4.

It is intended to assist in updating your playbooks, plugins and other parts of your Ansible infrastructure so they will work with this version of Ansible.


We suggest you read this page along with `Ansible Changelog <https://github.com/ansible/ansible/blob/devel/CHANGELOG.md#2.4>`_ to understand what updates you may need to make.

This document is part of a collection on porting. The complete list of porting guides can be found at :ref:`porting guides <porting_guides>`.

.. contents:: Topics

Playbook
========

`import_` and `include_` split
------------------------------


**OLD** In Ansible 2.3:

.. code-block:: yaml

    - name: old foo

Will result in:

.. code-block:: yaml

   [WARNING]: deprecation message 1
   [WARNING]: deprecation message 2
   [WARNING]: deprecation message 3


**NEW** In Ansible 2.4:


.. code-block:: yaml

   - name: foo

ansible_facts namespacing
-------------------------

FIXME:

Inventory plugins
-----------------

FIXME: starting migration from hardcoded inventory + inventory scripts. scripts will still work via script plugin but efforts will now concentrate on plugins

Multiple inventory
------------------

**NEW** In Ansible 2.4:


.. code-block:: shell

   ansible-playbook -i /path/to/inventory1, /some/other/path/inventory2


Deprecated
==========

Inventory argument
-------------------------

Use of ``--inventory-file`` is now deprecated. Use ``--inventory`` or ``-i``.


Use of multiple tags
--------------------

Specifying ``--tags`` (or ``--skip-tags``) multiple times on the command line currently leads to the last one overriding all the previous ones. This behavior is deprecated. In the future, if you specify --tags multiple times the tags will be merged together. From now on, using ``--tags`` multiple times on one command line will emit a deprecation warning. Setting the ``merge_multiple_cli_tags`` option to True in the ``ansible.cfg`` file will enable the new behavior.

In 2.4, the default has change to merge the tags. You can enable the old overwriting behavior via the config option.

In 2.5, multiple ``--tags`` options will be merged with no way to go back to the old behavior.


Other caveats
-------------

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


Plugins
=======

var plugin changes
------------------

FIXME: bcoca to add details


Porting custom scripts
======================

Inventory script now obsolete
-----------------------------

FIXME: inventory scripts are becoming obsolete, in favor of inventory plugins

Networking
==========

There have been a number of changes to how Networking Modules operate.

Playbooks should still use ``connection: local``.

Persistent Connection
---------------------

The configuration variables ``connection_retries`` and ``connect_interval`` which were added in Ansible 2.3 are now deprecated. For Ansible 2.4 and later use ``connection_retry_timeout``.

To control timeouts use ``command_timeout`` rather than the previous top level ``timeout`` variable under ``[default]``

See :ref:`Ansible Network debug guide <network_debug_troubleshooting>` for more information.

The following changes apply to:

* FIXME List modules that have been ported to new framework in 2.4 - Link back to 2.3 porting guide

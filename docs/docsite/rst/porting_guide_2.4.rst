.. _porting_2.4_guide:

*************************
Ansible 2.3 Porting Guide
*************************

This section discusses the changes to how you use Ansible between Ansible 2.2 and Ansible 2.3.

It is intended to assist in updating your playbooks, plugins, etc so they will work with this version of Ansible.


We suggest you read this page along with https://github.com/ansible/ansible/blob/devel/CHANGELOG.md#24-dancing-days---active-development before upgrading Ansible to understand what, if any updates you will need to make.

This document is part of a collection on porting, the rest can be found at :ref:`porting_guides <Porting Guides>`.

.. contents:: Topics

Playbook
========


Deprecated
==========



Use of multiple tags
--------------------

Specifying ``--tags`` (or ``--skip-tags``) multiple times on the command line currently leads to the last one overriding all the previous ones. This behavior is deprecated. In the future, if you specify --tags multiple times the tags will be merged together. From now on, using ``--tags`` multiple times on one command line will emit a deprecation warning. Setting the ``merge_multiple_cli_tags`` option to True in the ``ansible.cfg`` file will enable the new behavior.

In 2.4, the default will be to merge and you can enable the old overwriting behavior via the config option.
In 2.5, multiple ``--tags`` options will be merged with no way to go back to the old behavior.

Other caveats

Modules
=======

Major changes in popular modules are detailed here

Modules removed
---------------

The following modules no longer exist:

* None

Deprecation notices
-------------------

Notice had been given that the following modules will be removed in Ansible 2.5, we suggest updating your Playbooks at your earliest convenience.

* :ref:`fixme <fixme>`
oteworthy module changes
-------------------------
Plugins
=======



Porting custom scripts
======================

Networking
==========

There have been a number of changes to number of changes to how Networking Modules operate.

Playbooks should still use ``connection: local``

The following changes apply to:

* TBD List modules that have been ported to new framework in 2.4
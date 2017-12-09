.. _porting_2.5_guide:

*************************
Ansible 2.5 Porting Guide
*************************

This section discusses the behavioral changes between Ansible 2.4 and Ansible 2.5.

It is intended to assist in updating your playbooks, plugins and other parts of your Ansible infrastructure so they will work with this version of Ansible.

We suggest you read this page along with `Ansible Changelog <https://github.com/ansible/ansible/blob/devel/CHANGELOG.md#2.5>`_ to understand what updates you may need to make.

This document is part of a collection on porting. The complete list of porting guides can be found at :ref:`porting guides <porting_guides>`.

.. contents:: Topics

Playbook
========

No notable changes.

Deprecated
==========

Jinja tests used as filters
---------------------------

Using Ansible provided jinja tests as filters will be removed in Ansible 2.9.

Prior to Ansible 2.5, jinja tests included within Ansible were most often used as filters. The large difference in use is that filters are referenced as ``variable | filter_name`` where as jinja tests are refereced as ``variable is test_name``.

Jinja tests are used for comparisons, whereas filters are used for data manipulation, and have different applications in jinja. This change is to help differentiate the concepts for a better understanding of jinja, and where each can be appropriately used.

As of Ansible 2.5 using an Ansible provided jinja test with filter syntax, will display a deprecation error.

**OLD** In Ansible 2.4 (and earlier) the use of an Ansible included jinja test would likely look like this:

.. code-block:: yaml

    when:
        - result | failed
        - not result | success

**NEW** In Ansible 2.5 it should be changed to look like this:

.. code-block:: yaml

    when:
        - result is failed
        - results is not successful

In addition to the deprecation warnings, many new tests have been introduced that are aliases of the old tests, that make more sense grammatically with the jinja test syntax such as the new ``successful`` test which aliases ``success``

.. code-block:: yaml

    when: result is successful

See :ref:`The Ansible Tests Documentation <playbooks_tests>` for more information.

Additionally, a script was created to assist in the conversion for tests using filter syntax to proper jinja test syntax. This script has been used to convert all of the Ansible integration tests to the correct format. There are a few limitations documented, and all changes made by this script should be evaluated for correctness before executing the modified playbooks. The script can be found at `https://github.com/ansible/ansible/blob/devel/hacking/fix_test_syntax.py <https://github.com/ansible/ansible/blob/devel/hacking/fix_test_syntax.py>`_.

Modules
=======

Major changes in popular modules are detailed here

No notable changes.

Modules removed
---------------

The following modules no longer exist:

* None

Deprecation notices
-------------------

The following modules will be removed in Ansible 2.9. Please update update your playbooks accordingly.

* :ref:`fixme <fixme>`

Noteworthy module changes
-------------------------

* The :ref:`stat <stat>` and :ref:`win_stat <win_stat>` modules have changed the default of the option ``get_md5`` from ``true`` to ``false``.

This option will be removed starting with Ansible version 2.9. The options ``get_checksum: True``
and ``checksum_algorithm: md5`` can still be used if an MD5 checksum is
desired.

* ``osx_say`` module was renamed into :ref:`say <say>`.

Plugins
=======

No notable changes.

Porting custom scripts
======================

No notable changes.

Networking
==========


Change in deprecation notice of top-level connection arguments
--------------------------------------------------------------
.. code-block:: yaml

    - name: example of using top-level options for connection properties
      ios_command:
        commands: show version
        host: "{{ inventory_hostname }}"
        username: cisco
        password: cisco
        authorize: yes
        auth_pass: cisco

**OLD** In Ansible 2.4:

Will result in:

.. code-block:: yaml

   [WARNING]: argument username has been deprecated and will be removed in a future version
   [WARNING]: argument host has been deprecated and will be removed in a future version
   [WARNING]: argument password has been deprecated and will be removed in a future version


**NEW** In Ansible 2.5:


.. code-block:: yaml

   [DEPRECATION WARNING]: Param 'username' is deprecated. See the module docs for more information. This feature will be removed in version
   2.9. Deprecation warnings can be disabled by setting deprecation_warnings=False in ansible.cfg.
   [DEPRECATION WARNING]: Param 'password' is deprecated. See the module docs for more information. This feature will be removed in version
   2.9. Deprecation warnings can be disabled by setting deprecation_warnings=False in ansible.cfg.
   [DEPRECATION WARNING]: Param 'host' is deprecated. See the module docs for more information. This feature will be removed in version 2.9.
   Deprecation warnings can be disabled by setting deprecation_warnings=False in ansible.cfg.

Notice when using provider dictionary with new persistent connection types
--------------------------------------------------------------------------

Using a provider dictionary with one of the new persistent connection types for networking
(network_cli, netconf, etc.) will result in a warning. When using these connections
the standard Ansible infrastructure for controlling connections should be used.
(Link to basic inventory documentation?)

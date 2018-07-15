.. _porting_2.7_guide:

*************************
Ansible 2.7 Porting Guide
*************************

This section discusses the behavioral changes between Ansible 2.6 and Ansible 2.7.

It is intended to assist in updating your playbooks, plugins and other parts of your Ansible infrastructure so they will work with this version of Ansible.

We suggest you read this page along with `Ansible Changelog for 2.7 <https://github.com/ansible/ansible/blob/devel/changelogs/CHANGELOG-v2.7.rst>`_ to understand what updates you may need to make.

This document is part of a collection on porting. The complete list of porting guides can be found at :ref:`porting guides <porting_guides>`.

.. contents:: Topics

Playbook
========

Role Precedence Fix during Role Loading
---------------------------------------

Ansible 2.7 makes a small change to variable precedence when loading roles, resolving a bug, ensuring that role loading matches :ref:`variable precedence expectations <ansible_variable_precedence>`.

Before Ansible 2.7, when loading a role, the variables defined in the role's ``vars/main.yml`` and ``defaults/main.yml`` were not available when parsing the role's ``tasks/main.yml`` file. This prevented the role from utilizing these variables when being parsed. The problem manifested when ``import_tasks`` or ``import_role`` was used with a variable defined in the role's vars or defaults.

In Ansible 2.7, role ``vars`` and ``defaults`` are now parsed before ``tasks/main.yml``. This can cause a change in behavior if the same variable is defined at the play level and the role level with different values, and leveraged in ``import_tasks`` or ``import_role`` to define the role or file to import.

include_role and import_role variable exposure
----------------------------------------------

In Ansible 2.7 a new module argument named ``public`` was added to the ``include_role`` module that dictates whether or not the role's ``defaults`` and ``vars`` will be exposed outside of the role, allowing those variables to be used by later tasks.  This value defaults to ``public: False``, matching current behavior.

``import_role`` does not support the ``public`` argument, and will unconditionally expose the role's ``defaults`` and ``vars`` to the rest of the playbook. This functinality brings ``import_role`` into closer alignment with roles listed within the ``roles`` header in a play.

There is an important difference in the way that ``include_role`` (dynamic) will expose the role's variables, as opposed to ``import_role`` (static). ``import_role`` is a pre-processor, and the ``defaults`` and ``vars`` are evaluated at playbook parsing, making the variables available to tasks and roles listed at any point in the play. ``include_role`` is a conditional task, and the ``defaults`` and ``vars`` are evaluated at execution time, making the variables available to tasks and roles listed *after* the ``include_role`` task.

Deprecated
==========

Using a loop on a package module via squash_actions
---------------------------------------------------

The use of ``squash_actions`` to invoke a package module, such as "yum", to only invoke the module once is deprecated, and will be removed in Ansible 2.11.

Instead of relying on implicit squashing, tasks should instead supply the list directly to the ``name``, ``pkg`` or ``package`` parameter of the module. This functionality has been supported in most modules since Ansible 2.3.

**OLD** In Ansible 2.6 (and earlier) the following task would invoke the "yum" module only 1 time to install multiple packages

.. code-block:: yaml

    - name: Install packages
      yum:
        name: "{{ item }}"
        state: present
      with_items: "{{ packages }}"

**NEW** In Ansible 2.7 it should be changed to look like this:

.. code-block:: yaml

    - name: Install packages
      yum:
        name: "{{ packages }}"
        state: present


Modules
=======

Major changes in popular modules are detailed here

* The :ref:`DEFAULT_SYSLOG_FACILITY` configuration option tells Ansible modules to use a specific
  `syslog facility <https://en.wikipedia.org/wiki/Syslog#Facility>`_ when logging information on all
  managed machines. Due to a bug with older Ansible versions, this setting did not affect machines
  using journald with the systemd Python bindings installed. On those machines, Ansible log
  messages were sent to ``/var/log/messages``, even if you set :ref:`DEFAULT_SYSLOG_FACILITY`.
  Ansible 2.7 fixes this bug, routing all Ansible log messages according to the value set for
  :ref:`DEFAULT_SYSLOG_FACILITY`. If you have :ref:`DEFAULT_SYSLOG_FACILITY` configured, the
  location of remote logs on systems which use journald may change.

* The ``lineinfile`` module was changed to show a warning when using an empty string as a regexp.
  Since an empty regexp matches every line in a file, it will replace the last line in a file rather
  than inserting. If this is the desired behavior, use ``'^'`` which will match every line and
  will not trigger the warning.


Modules removed
---------------

The following modules no longer exist:


Deprecation notices
-------------------

The following modules will be removed in Ansible 2.10. Please update your playbooks accordingly.


Noteworthy module changes
-------------------------

No notable changes.

Plugins
=======

No notable changes.

Porting custom scripts
======================

No notable changes.

Networking
==========

No notable changes.

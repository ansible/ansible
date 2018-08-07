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

Expedited Deprecation: Use of ``__file__`` in ``AnsibleModule``
---------------------------------------------------------------

.. note:: The use of the ``__file__`` variable is deprecated in Ansible 2.7 and **will be eliminated in Ansible 2.8**. This is much quicker than our usual 4-release deprecation cycle.

We are deprecating the use of the ``__file__`` variable to refer to the file containing the currently-running code. This common Python technique for finding a filesystem path does not always work (even in vanilla Python). Sometimes a Python module can be imported from a virtual location (like inside of a zip file). When this happens, the ``__file__`` variable will reference a virtual location pointing to inside of the zip file. This can cause problems if, for instance, the code was trying to use ``__file__`` to find the directory containing the python module to write some temporary information.

Before the introduction of AnsiBallZ in Ansible 2.1, using ``__file__`` worked in ``AnsibleModule`` sometimes, but any module that used it would fail when pipelining was turned on (because the module would be piped into the python interpreter's standard input, so ``__file__`` wouldn't contain a file path). AnsiBallZ unintentionally made using ``__file__`` always work, by always creating a temporary file for ``AnsibleModule`` to reside in.

Ansible 2.8 will no longer create a temporary file for ``AnsibleModule``; instead it will read the file out of a zip file. This change should speed up module execution, but it does mean that starting with Ansible 2.8, referencing ``__file__`` will always fail in ``AnsibleModule``.

If you are the author of a third-party module which uses ``__file__`` with ``AnsibleModule``, please update your module(s) now, while the use of ``__file__`` is deprecated but still available. The most common use of ``__file__`` is to find a directory to write a temporary file. In Ansible 2.5 and above, you can use the ``tmpdir`` attribute on an ``AnsibleModule`` instance instead, as shown in this code from the :ref:`apt module <apt_module>`:

.. code-block:: diff

    -    tempdir = os.path.dirname(__file__)
    -    package = os.path.join(tempdir, to_native(deb.rsplit('/', 1)[1]))
    +    package = os.path.join(module.tmpdir, to_native(deb.rsplit('/', 1)[1]))


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

* Check mode is now supported in the ``command`` and ``shell`` modules. However, only when ``creates`` or ``removes`` is
  specified. If either of these are specified, the module will check for existence of the file and report the correct
  changed status, if they are not included the module will skip like it had done previously.

* The ``win_chocolatey`` module originally required the ``proxy_username`` and ``proxy_password`` to
  escape any double quotes in the value. This is no longer required and the escaping may cause further
  issues.

* The ``win_uri`` module has removed the deprecated option ``use_basic_parsing``, since Ansible 2.5 this option did
  nothing

* The ``win_scheduled_task`` module has removed the following deprecated options:

  * ``executable``, use ``path`` in an actions entry instead
  * ``argument``, use ``arguments`` in an actions entry instead
  * ``store_password``, set ``logon_type: password`` instead
  * ``days_of_week``, use ``monthlydow`` in a triggers entry instead
  * ``frequency``, use ``type``, in a triggers entry instead
  * ``time``, use ``start_boundary`` in a triggers entry instead


Plugins
=======

No notable changes.

Porting custom scripts
======================

No notable changes.

Networking
==========

No notable changes.

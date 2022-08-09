
.. _porting_2.12_guide_core:

*******************************
Ansible-core 2.12 Porting Guide
*******************************

This section discusses the behavioral changes between ``ansible-core`` 2.11 and ``ansible-core`` 2.12.

It is intended to assist in updating your playbooks, plugins and other parts of your Ansible infrastructure so they will work with this version of Ansible.

We suggest you read this page along with `ansible-core Changelog for 2.12 <https://github.com/ansible/ansible/blob/stable-2.12/changelogs/CHANGELOG-v2.12.rst>`_ to understand what updates you may need to make.

This document is part of a collection on porting. The complete list of porting guides can be found at :ref:`porting guides <porting_guides>`.

.. contents:: Topics


Playbook
========

* When calling tasks and setting ``async``, setting ``ANSIBLE_ASYNC_DIR`` under ``environment:`` is no longer valid. Instead, use the shell configuration variable ``async_dir``, for example by setting ``ansible_async_dir``:

.. code-block:: yaml

   tasks:
     - dnf:
         name: '*'
         state: latest
       async: 300
       poll: 5
       vars:
         ansible_async_dir: /path/to/my/custom/dir

* The ``undef()`` function is added to the templating environment for creating undefined variables directly in a template. Optionally, a hint may be provided for variables which are intended to be overridden.

.. code-block:: yaml

   vars:
     old: "{{ undef }}"
     new: "{{ undef() }}"
     new_with_hint: "{{ undef(hint='You must override this variable') }}"

Python Interpreter Discovery
============================

The default value of ``INTERPRETER_PYTHON`` changed to ``auto``. The list of Python interpreters in ``INTERPRETER_PYTHON_FALLBACK`` changed to prefer Python 3 over Python 2. The combination of these two changes means the new default behavior is to quietly prefer Python 3 over Python 2 on remote hosts. Previously a deprecation warning was issued in situations where interpreter discovery would have used Python 3 but the interpreter was set to ``/usr/bin/python``.

``INTERPRETER_PYTHON_FALLBACK`` can be changed from the default list of interpreters by setting the ``ansible_interpreter_python_fallback`` variable.

See :ref:`interpreter discovery documentation <interpreter_discovery>` for more details.


Command Line
============

* Python 3.8 on the controller node is a hard requirement for this release. The command line scripts will not function with a lower Python version.
* ``ansible-vault`` no longer supports ``PyCrypto`` and requires ``cryptography``.

Deprecated
==========

* Python 2.6 on the target node is deprecated in this release. ``ansible-core`` 2.13 will remove support for Python 2.6.
* Bare variables in conditionals: ``when`` conditionals no longer automatically parse string booleans such as ``"true"`` and ``"false"`` into actual booleans. Any variable containing a non-empty string is considered true. This was previously configurable with the ``CONDITIONAL_BARE_VARS`` configuration option (and the ``ANSIBLE_CONDITIONAL_BARE_VARS`` environment variable). This setting no longer has any effect. Users can work around the issue by using the ``|bool`` filter:

.. code-block:: yaml

    vars:
      teardown: 'false'

    tasks:
      - include_tasks: teardown.yml
        when: teardown | bool

      - include_tasks: provision.yml
        when: not teardown | bool

* The ``_remote_checksum()`` method in ``ActionBase`` is deprecated. Any action plugin using this method should use ``_execute_remote_stat()`` instead.

Modules
=======

* ``cron`` now requires ``name`` to be specified in all cases.
* ``cron`` no longer allows a ``reboot`` parameter. Use ``special_time: reboot`` instead.
* ``hostname`` - On FreeBSD, the ``before`` result will no longer be ``"temporarystub"`` if permanent hostname file does not exist. It will instead be ``""`` (empty string) for consistency with other systems.
* ``hostname`` - On OpenRC and Solaris based systems, the ``before`` result will no longer be ``"UNKNOWN"`` if the permanent hostname file does not exist. It will instead be ``""`` (empty string) for consistency with other systems.
* ``pip`` now uses the ``pip`` Python module installed for the Ansible module's Python interpreter, if available, unless ``executable`` or ``virtualenv`` were specified.


Modules removed
---------------

The following modules no longer exist:

* No notable changes


Deprecation notices
-------------------

No notable changes


Noteworthy module changes
-------------------------

No notable changes


Plugins
=======

* ``unique`` filter with Jinja2 < 2.10 is case-sensitive and now raise coherently an error if ``case_sensitive=False`` instead of when ``case_sensitive=True``.
* Set theory filters (``intersect``, ``difference``, ``symmetric_difference`` and ``union``) are now case-sensitive. Explicitly use ``case_sensitive=False`` to keep previous behavior. Note: with Jinja2 < 2.10, the filters were already case-sensitive by default.
* ``password_hash``` now uses ``passlib`` defaults when an option is unspecified, e.g. ``bcrypt_sha256`` now default to the "2b" format and if the "2a" format is required it must be specified.

Porting custom scripts
======================

No notable changes


Networking
==========

No notable changes

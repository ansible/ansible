
.. _porting_2.12_guide:

**************************
Ansible 2.12 Porting Guide
**************************

This section discusses the behavioral changes between Ansible 2.11 and Ansible 2.12.

It is intended to assist in updating your playbooks, plugins and other parts of your Ansible infrastructure so they will work with this version of Ansible.

We suggest you read this page along with `Ansible Changelog for 2.12 <https://github.com/ansible/ansible/blob/devel/changelogs/CHANGELOG-v2.12.rst>`_ to understand what updates you may need to make.

This document is part of a collection on porting. The complete list of porting guides can be found at :ref:`porting guides <porting_guides>`.

.. contents:: Topics


Playbook
========

No notable changes

Python Interpreter Discovery
============================

The default value of ``INTERPRETER_PYTHON_FALLBACK`` changed to ``auto``. The list of Python interpreters in ``INTERPRETER_PYTHON_FALLBACK`` changed to prefer Python 3 over Python 2. The combination of these two changes means the new default behavior is to quietly prefer Python 3 over Python 2 on remote hosts. Previously a deprecation warning was issued in situations where interpreter discovery would have used Python 3 but the interpreter was set to ``/usr/bin/python``.

``INTERPRETER_PYTHON_FALLBACK`` can be changed from the default list of interpreters by setting the ``ansible_interpreter_python_fallback`` variable.

See :ref:`interpreter discovery documentation <interpreter_discovery>` for more details.


Command Line
============

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


Porting custom scripts
======================

No notable changes


Networking
==========

No notable changes


.. _porting_2.13_guide_core:

*******************************
Ansible-core 2.13 Porting Guide
*******************************

This section discusses the behavioral changes between ``ansible-core`` 2.12 and ``ansible-core`` 2.13.

It is intended to assist in updating your playbooks, plugins and other parts of your Ansible infrastructure so they will work with this version of Ansible.

We suggest you read this page along with `ansible-core Changelog for 2.13 <https://github.com/ansible/ansible/blob/stable-2.13/changelogs/CHANGELOG-v2.13.rst>`_ to understand what updates you may need to make.

This document is part of a collection on porting. The complete list of porting guides can be found at :ref:`porting guides <porting_guides>`.

.. contents:: Topics


Playbook
========

* Templating - You can no longer perform arithmetic and concatenation operations outside of the jinja template. The following statement will need to be rewritten to produce ``[1, 2]``:

 .. code-block:: yaml

     - name: Prior to 2.13
       debug:
         msg: '[1] + {{ [2] }}'

     - name: 2.13 and forward
       debug:
         msg: '{{ [1] + [2] }}'

* The return value of the ``__repr__`` method of an undefined variable represented by the ``AnsibleUndefined`` object changed. ``{{ '%r'|format(undefined_variable) }}`` returns ``AnsibleUndefined(hint=None, obj=missing, name='undefined_variable')`` in 2.13 as opposed to just ``AnsibleUndefined`` in versions 2.12 and prior.

* The ``finalize`` method is no longer exposed in the globals for use in templating. To convert ``None`` to an empty string the following expression can be used: ``{{ value if value is not none }}``.


Command Line
============

No notable changes


Deprecated
==========

No notable changes


Modules
=======

* To use ansible-core 2.13 for module execution, you must use Python 2 version 2.7 or Python 3 version 3.5 or newer. Any code utilizing ``ansible.module_utils.basic`` will not function with lower Python versions.


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


Breaking Changes
----------------

* ``ansible.module_utils.urls.fetch_url`` will now return the captured ``HTTPError`` exception as ``r``. ``HTTPError`` is a response like object that can offer more information to module authors. Modules should rely on ``info['status'] >= 400`` to determine if there was a failure, instead of using ``r is None`` or catching ``AttributeError`` when attempting ``r.read()``.


Plugins
=======

No notable changes


Porting custom scripts
======================

No notable changes


Networking
==========

No notable changes

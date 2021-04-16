.. _ansible.module_utils:
.. _module_utils:

***************************************************************
Ansible Reference: Module Utilities
***************************************************************

This page documents utilities intended to be helpful when writing
Ansible modules in Python.


AnsibleModule
--------------

To use this functionality, include ``from ansible.module_utils.basic import AnsibleModule`` in your module.

.. autoclass:: ansible.module_utils.basic.AnsibleModule
   :members:
   :noindex:

Basic
------

To use this functionality, include ``import ansible.module_utils.basic`` in your module.

.. automodule:: ansible.module_utils.basic
   :members:


Argument Spec
---------------------

Classes and functions for validating parameters against an argument spec.

ArgumentSpecValidator
=====================

.. autoclass:: ansible.module_utils.common.arg_spec.ArgumentSpecValidator
   :members:

ValidationResult
================

.. autoclass:: ansible.module_utils.common.arg_spec.ValidationResult
   :members:
   :member-order: bysource
   :private-members: _no_log_values  # This only works in sphinx >= 3.2. Otherwise it shows all private members with doc strings.

Parameters
==========

.. automodule:: ansible.module_utils.common.parameters
   :members:

   .. py:data:: DEFAULT_TYPE_VALIDATORS

     :class:`dict` of type names, such as ``'str'``, and the default function
     used to check that type, :func:`~ansible.module_utils.common.validation.check_type_str` in this case.

Validation
==========

Standalone functions for validating various parameter types.

.. automodule:: ansible.module_utils.common.validation
   :members:


Errors
------

.. automodule:: ansible.module_utils.errors
   :members:
   :member-order: bysource

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


Basic
------

To use this functionality, include ``import ansible.module_utils.basic`` in your module.

.. automodule:: ansible.module_utils.basic
   :members:

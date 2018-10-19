.. _ansible.module_utils:
.. _module_utils:

***************************************************************
Ansible Reference: Module Utilities
***************************************************************

This page documents the available utilities called with ``ansible.module_utils.util_name``.

Generic
--------
.. glossary::

    .. _ansible.module_utils.debug
    debug
    .. _ansible.module_utils.url
    url
    .. _ansible.module_utils.log
    log
    .. _ansible.module_utils.no_log
    no_log
    .. _Ansible.get_bin_path
    Ansible.get_bin_path


.. _AnsibleModule:
.. _ansible.module_utils.basic.AnsibleModule:

AnsibleModule
--------------
.. glossary::

    ansible.module_utils.basic.AnsibleModule
      Utilities in module_utils.basic.AnsibleModule apply to all module types

    .. _AnsibleModule.debug:
    AnsibleModule.debug
    .. _AnsibleModule._debug:
    AnsibleModule._debug
    .. _AnsibleModule._diff:
    AnsibleModule._diff
    .. _AnsibleModule.log:
    AnsibleModule.log
    .. _AnsibleModule.no_log:
    AnsibleModule.no_log
    .. _AnsibleModule.params:
    AnsibleModule.params
    .. _AnsibleModule.run_command:
    AnsibleModule.run_command
    .. _ansible.module_utils.basic.AnsibleModule._selinux_special_fs:
    ansible.module_utils.basic.AnsibleModule._selinux_special_fs
      (formerly ansible.module_utils.basic.SELINUX_SPECIAL_FS)


.. _ansible.module_utils.basic:

Basic
------
.. glossary::

    ansible.module_utils.basic
      Utilities in module_utils.basic apply to all module types.

    .. _ansible.module_utils.basic.SELINUX_SPECIAL_FS:
    ansible.module_utils.basic.SELINUX_SPECIAL_FS
      *deprecated* replaced by :term:`ansible.module_utils.basic.AnsibleModule._selinux_special_fs`

    .. _ansible.module_utils.basic._load_params:
    load_params

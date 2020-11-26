:orphan:

*************************
Ansible API Documentation
*************************

The Ansible API is under construction. These stub references for attributes, classes, functions, methods, and modules will be documented in future.
The :ref:`module utilities <ansible.module_utils>` included in ``ansible.module_utils.basic`` and ``AnsibleModule`` are documented under Reference & Appendices.

.. contents::
   :local:

Attributes
==========

.. py:attribute:: AnsibleModule.params

The parameters accepted by the module.

.. py:attribute:: ansible.module_utils.basic.ANSIBLE_VERSION

.. py:attribute:: ansible.module_utils.basic.SELINUX_SPECIAL_FS

Deprecated in favor of ansibleModule._selinux_special_fs.

.. py:attribute:: AnsibleModule.ansible_version

.. py:attribute:: AnsibleModule._debug

.. py:attribute:: AnsibleModule._diff

.. py:attribute:: AnsibleModule.no_log

.. py:attribute:: AnsibleModule._selinux_special_fs

(formerly ansible.module_utils.basic.SELINUX_SPECIAL_FS)

.. py:attribute:: AnsibleModule._syslog_facility

.. py:attribute:: self.playbook

.. py:attribute:: self.play

.. py:attribute:: self.task

.. py:attribute:: sys.path


Classes
=======

.. py:class:: ``ansible.module_utils.basic.AnsibleModule``
   :noindex:

The basic utilities for AnsibleModule.

.. py:class:: AnsibleModule

The main class for an Ansible module.


Functions
=========

.. py:function:: ansible.module_utils.basic._load_params()

Load parameters.


Methods
=======

.. py:method:: AnsibleModule.log()

Logs the output of Ansible.

.. py:method:: AnsibleModule.debug()

Debugs Ansible.

.. py:method:: Ansible.get_bin_path()

Retrieves the path for executables.

.. py:method:: AnsibleModule.run_command()

Runs a command within an Ansible module.

.. py:method:: module.fail_json()

Exits and returns a failure.

.. py:method:: module.exit_json()

Exits and returns output.


Modules
=======

.. py:module:: ansible.module_utils

.. py:module:: ansible.module_utils.basic
  :noindex:


.. py:module:: ansible.module_utils.url

.. _module_contribution:

===================================
Contributing Your Module to Ansible
===================================

If you want to contribute a module to Ansible, you must meet our objective and subjective requirements. Modules accepted into the `main project repo <https://github.com/ansible/ansible>`_ ship with every Ansible installation. However, contributing to the main project isn't the only way to distribute a module - you can embed modules in roles on Galaxy or simply share copies of your module code for :ref:`local use <developing_locally>`.

Objective requirements
----------------------

* write your module in either Python or Powershell for Windows
* use the ``AnsibleModule`` common code
* support Python 2.6 and Python 3.5 - if your module cannot support Python 2.6, explain the required minimum Python version and rationale in the requirements section in ``DOCUMENTATION`` ## TODO confirm required python versions
* use proper :ref:`Python-3 syntax <developing_python_3>`
* follow `PEP 8 <https://www.python.org/dev/peps/pep-0008/>`_ Python style conventions - see :ref:`testing_pep8` for more information
* license your module with GPL 3
* conform to Ansible's :ref:`formatting and documentation <developing_modules_documenting>` standards
* include comprehensive :ref:`tests <developing_modules_testing>` for your module
* minimize module dependencies
* support :ref:`check_mode <check_mode_dry>` if possible

Please make sure your module meets these requirements before you submit your PR/proposal. If you have questions, reach out on IRC or the mailing list.

Subjective requirements
-----------------------

If your module meets our objective requirements, we'll review your code to see if we think it's clear, concise, secure, and maintainable. We'll consider whether your module provides a good user experience, helpful error messages, reasonable defaults, and more. This process is subjective, and we can't list exact standards for acceptance. For the best chance of getting your module accepted into the Ansible repo, follow our :ref:`best practices for module development <developing_modules_best_practices>`.

Windows modules checklist
=========================

For a checklist and details on how to write Windows modules please see :ref:`developing_modules_general_windows`

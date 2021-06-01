.. _developing_modules_checklist:
.. _module_contribution:

**********************************************************
Contributing your module to an existing Ansible collection
**********************************************************

If you want to contribute a module to an existing collection, you must meet the community's objective and subjective requirements. Please read the details below, and also review our :ref:`tips for module development <developing_modules_best_practices>`.

Modules accepted into certain collections are included in every Ansible release on PyPI. However, contributing to one of these collections is not the only way to distribute a module - you can :ref:`create your own collection <developing_collections>`, embed modules in roles on Galaxy or simply share copies of your module code for :ref:`local use <developing_locally>`.

Contributing modules: objective requirements
===============================================

To contribute a module to most Ansible collections, you must:

* write your module in either Python or Powershell for Windows
* use the ``AnsibleModule`` common code
* support Python 2.6 and Python 3.5 - if your module cannot support Python 2.6, explain the required minimum Python version and rationale in the requirements section in ``DOCUMENTATION``
* use proper :ref:`Python 3 syntax <developing_python_3>`
* follow `PEP 8 <https://www.python.org/dev/peps/pep-0008/>`_ Python style conventions - see :ref:`testing_pep8` for more information
* license your module under the GPL license (GPLv3 or later)
* understand the :ref:`license agreement <contributor_license_agreement>`, which applies to all contributions
* conform to Ansible's :ref:`formatting and documentation <developing_modules_documenting>` standards
* include comprehensive :ref:`tests <developing_testing>` for your module
* minimize module dependencies
* support :ref:`check_mode <check_mode_dry>` if possible
* ensure your code is readable
* if a module is named ``<something>_facts``, it should be because its main purpose is returning ``ansible_facts``. Do not name modules that do not do this with ``_facts``. Only use ``ansible_facts`` for information that is specific to the host machine, for example network interfaces and their configuration, which operating system and which programs are installed.
* Modules that query/return general information (and not ``ansible_facts``) should be named ``_info``. General information is non-host specific information, for example information on online/cloud services (you can access different accounts for the same online service from the same host), or information on VMs and containers accessible from the machine.

Additional requirements may apply for certain collections. Review the individual collection repositories for more information.

Please make sure your module meets these requirements before you submit your PR/proposal. If you have questions, reach out via ``#ansible-devel``, Ansible's IRC chat channel on `irc.libera.chat <http://libera.chat>`_ or the `Ansible development mailing list <https://groups.google.com/group/ansible-devel>`_.

Contributing to Ansible: subjective requirements
================================================

If your module meets these objective requirements, collection maintainers will review your code to see if they think it's clear, concise, secure, and maintainable. They will consider whether your module provides a good user experience, helpful error messages, reasonable defaults, and more. This process is subjective, with no exact standards for acceptance. For the best chance of getting your module accepted, follow our :ref:`tips for module development <developing_modules_best_practices>`.

Other checklists
================

* :ref:`Tips for module development <developing_modules_best_practices>`.
* :ref:`Amazon development checklist <AWS_module_development>`.
* :ref:`Windows development checklist <developing_modules_general_windows>`.
